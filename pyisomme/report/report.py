from __future__ import annotations

import logging
from typing import Any, Generic, TypeVar, cast

from tqdm.auto import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from pyisomme.isomme import Isomme
from pyisomme.limits import Limits
from pyisomme.report.base_report import BaseReport
from pyisomme.report.criterion import Criterion
from pyisomme.report.describe import describe_report
from pyisomme.report.manual import suggest
from pyisomme.report.page import Page_Cover
from pyisomme.report.report_protocol import ReportProtocol
from pyisomme.report.validate import Issue, validate_report
from pyisomme.utils import json_encode

logger = logging.getLogger(__name__)

#: The overall criterion a concrete report is built around. Parameterising ``Report``
#: with it is what makes ``report.overall(isomme).criterion_driver...`` type-check.
#: Every report module defines its tree as a module-level class named ``Overall`` and
#: declares ``class X(Report[Overall])`` with ``Criterion_Overall = Overall``.
C = TypeVar("C", bound=Criterion)


class Report(BaseReport, Generic[C]):
    _name: str
    title: str

    isomme_list: list[Isomme]

    _limits: dict[Isomme, Limits]
    criterion_overall: dict[Isomme, C]

    _protocol: ReportProtocol
    _protocols: tuple[ReportProtocol, ...]

    #: Concrete reports must rebind this to their module-level ``Overall`` tree.
    Criterion_Overall: type[Criterion]

    def __init__(
        self,
        isomme_list: list[Isomme],
        title: str = "Unnamed Report",
        protocol_version: str | None = None,
    ) -> None:
        super().__init__(title=title)
        self.isomme_list = isomme_list

        if protocol_version is not None:
            self.protocol_version = protocol_version

        self._limits = {
            isomme: Limits(name=self._name or "Unnamed Limits", limit_list=[])
            for isomme in isomme_list
        }

        overall_type = getattr(type(self), "Criterion_Overall", None)
        if overall_type is None:
            raise TypeError(
                f"{type(self).__name__} must declare Criterion_Overall; "
                "a bare Report has no criterion tree."
            )

        self.criterion_overall = {}
        for isomme in self.isomme_list:
            # A concrete report's inner ``Criterion_Overall`` *is* the ``C`` it parameterises
            # ``Report`` with, but the language cannot express "this inner class is type[C]".
            self.criterion_overall[isomme] = cast(C, overall_type(self, isomme))
            self.criterion_overall[isomme].build_limits()

        self._available_pages = (Page_Cover(self),)
        self._selected_pages = list(self._available_pages)

    @property
    def coverage_labels(self) -> tuple[str, ...]:
        return tuple(str(isomme.test_number) for isomme in self.isomme_list)

    def overall(self, isomme: Isomme) -> C:
        """The overall criterion for ``isomme``, typed as the concrete report's own tree."""
        return self.criterion_overall[isomme]

    def calculate(self) -> Report[C]:
        with logging_redirect_tqdm():
            for isomme in tqdm(self.isomme_list, desc="Calculate Report"):
                logger.info(f"Calculate Criteria for {isomme}")
                self.criterion_overall[isomme].calculate()
        return self

    def _input_key(self, isomme: Isomme) -> str:
        return str(isomme.test_number)

    def get_inputs(self) -> dict[str, dict[str, Any]]:
        """
        Every manual input of every test, ``{test: {path: value}}``.

        JSON-serialisable by construction (inputs are scalars), so the manual
        assumptions behind a run can be stored beside the ISO-MME container and
        replayed with :meth:`set_inputs` — see :meth:`print_inputs` for a
        human-readable listing.
        """
        return {
            self._input_key(isomme): {
                path: getattr(criterion, spec.name)
                for path, criterion, spec in self.criterion_overall[
                    isomme
                ].iter_inputs()
            }
            for isomme in self.isomme_list
        }

    def set_inputs(self, inputs: dict[str, dict[str, Any]]) -> None:
        """
        Apply a mapping produced by :meth:`get_inputs`.

        Unknown tests and unknown input paths raise — a saved file that no
        longer matches the report is a mistake worth hearing about, not
        something to apply halfway.
        """
        by_key = {self._input_key(isomme): isomme for isomme in self.isomme_list}
        for key, values in inputs.items():
            if key not in by_key:
                raise KeyError(f"{self}: no test {key!r}. Available: {sorted(by_key)}")
            criteria = {
                path: (criterion, spec)
                for path, criterion, spec in self.criterion_overall[
                    by_key[key]
                ].iter_inputs()
            }
            for path, value in values.items():
                if path not in criteria:
                    raise KeyError(
                        f"{self}: test {key!r} has no manual input {path!r}."
                        f"{suggest(path, frozenset(criteria))}"
                    )
                criterion, spec = criteria[path]
                setattr(criterion, spec.name, value)

    def print_inputs(self) -> None:
        """
        List every manual input with its path, current value, default, unit and doc.

        The marker in front of the path says where the value comes from:
        ``*`` set by the user, ``~`` derived by the report (a position implied by
        ``p_driver``, a value read out of the test info), blank the declared default.
        """
        for isomme in self.isomme_list:
            print(isomme)
            for path, criterion, spec in self.criterion_overall[isomme].iter_inputs():
                value = getattr(criterion, spec.name)
                marker = (
                    "*"
                    if criterion.input_is_set(spec.name)
                    else (" " if value == spec.default else "~")
                )
                unit = f" [{spec.unit}]" if spec.unit else ""
                doc = f" — {spec.doc}" if spec.doc else ""
                source = f" (source: {spec.source})" if spec.source else ""
                print(
                    f"\t{marker} {path}: {value!r}{unit} "
                    f"(default {spec.default!r}, {spec.type_name()}){doc}{source}"
                )

    def print_results(self) -> None:
        for isomme in self.isomme_list:
            print(isomme)
            for path, criterion in self.criterion_overall[isomme].walk():
                intend = "\t" * (path.count("/") + 2 if path else 1)
                result = criterion.result
                value = result.value if result is not None else float("nan")
                rating = result.rating if result is not None else float("nan")
                unit = (
                    result.channel.unit
                    if result is not None and result.channel is not None
                    else ""
                )
                print(
                    f"{intend}{criterion.name if criterion.name is not None else criterion.__class__.__name__}: "
                    f"Value={value:.5g} [{unit}] Rating={rating:.5g}"
                )

    def json_results(self) -> dict[str, Any]:
        results: dict[str, Any] = {}
        for isomme_idx, isomme in enumerate(self.isomme_list, 1):
            test_results: dict[str, Any] = {}
            for path, criterion in self.criterion_overall[isomme].walk():
                node = test_results
                path_parts = path.split("/") if path else ("Overall",)
                for part in path_parts:
                    node = node.setdefault(part, {})
                node["result"] = {
                    "name": criterion.name
                    if criterion.name is not None
                    else criterion.__class__.__name__,
                    "value": json_encode(
                        criterion.result.value if criterion.result is not None else None
                    ),
                    "rating": json_encode(
                        criterion.result.rating
                        if criterion.result is not None
                        else None
                    ),
                    "color": json_encode(
                        criterion.result.color if criterion.result is not None else None
                    ),
                    "status": criterion.status.name,
                }
            results[f"{isomme_idx}: {isomme.test_number}"] = test_results
        return results

    def validate(self, errors_only: bool = False) -> list[Issue]:
        issues = validate_report(self)
        return [issue for issue in issues if issue.is_error] if errors_only else issues

    def describe(self) -> str:
        return describe_report(self)

    @property
    def limits(self) -> dict[Isomme, Limits]:
        return self._limits

    @property
    def protocol_version(self) -> str:
        return self._protocol.version

    @protocol_version.setter
    def protocol_version(self, protocol_version: str) -> None:
        for protocol in self._protocols:
            if protocol.version == protocol_version:
                self._protocol = protocol
                return
        raise ValueError(
            f"Protocol {protocol_version} not available. Available protocols: {[p.version for p in self._protocols]}"
        )

    @property
    def protocol(self) -> ReportProtocol:
        return self._protocol

    @protocol.setter
    def protocol(self, protocol: ReportProtocol) -> None:
        if protocol in self._protocols:
            self._protocol = protocol
        else:
            raise ValueError(
                f"Protocol {protocol.version} not available. Available protocols: {[p.version for p in self._protocols]}"
            )

    @property
    def protocols(self) -> tuple[ReportProtocol, ...]:
        return self._protocols
