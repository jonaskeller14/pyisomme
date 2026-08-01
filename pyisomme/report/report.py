from __future__ import annotations

from pyisomme.isomme import Isomme
from pyisomme.report.page import Page, Page_Cover
from pyisomme.limits import Limits
from pyisomme.report.criterion import Criterion
from pyisomme.report.manual import suggest

from pptx import Presentation
from pptx.presentation import Presentation as PptxPresentation
from tqdm.auto import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm
import numpy as np
import time
import logging
from pathlib import Path
from typing import Any, Generic, TypeVar, cast


logger = logging.getLogger(__name__)

#: The overall criterion a concrete report is built around. Parameterising ``Report``
#: with it is what makes ``report.overall(isomme).criterion_driver...`` type-check.
#: Every report module defines its tree as a module-level class named ``Overall`` and
#: declares ``class X(Report[Overall])`` with ``Criterion_Overall = Overall``.
C = TypeVar("C", bound=Criterion)


class Overall(Criterion):
    """Empty default tree, so a bare ``Report`` is still constructible."""

    def calculation(self) -> None:
        pass


class Report(Generic[C]):
    name: str | None = None
    title: str
    isomme_list: list[Isomme]
    limits: dict[Isomme, Limits]
    criterion_overall: dict[Isomme, C]
    pages: list[Page]
    protocol: str | None = None
    protocols: dict[str, str] = {}
    #: The report's criterion tree. Subclasses rebind it to their own ``Overall``.
    Criterion_Overall: type[Criterion] = Overall

    def __init__(self, isomme_list: list[Isomme], title: str = "Unnamed Report", protocol: str | None = None) -> None:
        self.isomme_list = isomme_list
        self.title = title

        if protocol is not None:
            assert protocol in self.protocols.keys(), \
                f"Protocol {protocol} not available. Available protocols: {list(self.protocols.keys())}"
            self.protocol = protocol

        self.limits = {isomme: Limits(name=self.name or "Unnamed Limits", limit_list=[]) for isomme in isomme_list}

        self.criterion_overall = {}
        for isomme in self.isomme_list:
            # A concrete report's inner ``Criterion_Overall`` *is* the ``C`` it parameterises
            # ``Report`` with, but the language cannot express "this inner class is type[C]".
            self.criterion_overall[isomme] = cast(C, self.Criterion_Overall(self, isomme))

        self.pages = [
            Page_Cover(self),
        ]

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
                for path, criterion, spec in self.criterion_overall[isomme].iter_inputs()
            }
            for isomme in self.isomme_list
        }

    def set_inputs(self, inputs: dict[str, dict[str, Any]]) -> Report[C]:
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
            criteria = {path: (criterion, spec)
                        for path, criterion, spec in self.criterion_overall[by_key[key]].iter_inputs()}
            for path, value in values.items():
                if path not in criteria:
                    raise KeyError(
                        f"{self}: test {key!r} has no manual input {path!r}."
                        f"{suggest(path, frozenset(criteria))}"
                    )
                criterion, spec = criteria[path]
                setattr(criterion, spec.name, value)
        return self

    def print_inputs(self) -> Report[C]:
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
                marker = "*" if criterion.input_is_set(spec.name) else (" " if value == spec.default else "~")
                unit = f" [{spec.unit}]" if spec.unit else ""
                doc = f" — {spec.doc}" if spec.doc else ""
                source = f" (source: {spec.source})" if spec.source else ""
                print(f"\t{marker} {path}: {value!r}{unit} "
                      f"(default {spec.default!r}, {spec.type_name()}){doc}{source}")
        return self

    def print_results(self) -> Report[C]:
        def print_subcriteria_results(criterion: Criterion, intend: str = "\t") -> None:
            print(f"{intend}{criterion.name if criterion.name is not None else criterion.__class__.__name__}: "
                  f"Value={criterion.value:.5g} [{criterion.channel.unit if criterion.channel is not None else ''}] "
                  f"Rating={criterion.rating:.5g}")

            subcriteria = [getattr(criterion, a) for a in dir(criterion) if isinstance(getattr(criterion, a), Criterion)]
            for subcriterion in subcriteria:
                print_subcriteria_results(subcriterion, intend=f"{intend}\t")

        for isomme in self.isomme_list:
            print(isomme)
            print_subcriteria_results(self.criterion_overall[isomme])
        return self

    def validate(self) -> bool:
        def print_subcriteria_results(criterion: Criterion) -> bool:
            subcriteria = [getattr(criterion, a) for a in dir(criterion) if isinstance(getattr(criterion, a), Criterion)]
            for subcriterion in subcriteria:
                if subcriterion.name == None:
                    return False
                result = print_subcriteria_results(subcriterion)
                if result == False:
                    return False
            return True
        
        for isomme in self.isomme_list:
            result = print_subcriteria_results(self.criterion_overall[isomme])
            if result == False:
                return False
        return True

    def __repr__(self) -> str:
        return f"Report(title='{self.title}', name='{self.name}')"

    def export_pptx(self, path: str | Path, template: str | Path | None = None) -> Report[C]:
        presentation: PptxPresentation = Presentation(template)

        with logging_redirect_tqdm():
            for page_number, page in enumerate(tqdm(self.pages, desc="Construct Pages")):
                logger.info(f"{page_number}:{page.name}")
                page.__init__(page.report)  # update. report could be changed since init  # TODO: TEST!
                page.construct(presentation)

        while True:
            try:
                presentation.save(path)
                break
            except PermissionError as e:
                logger.critical(e)
                time.sleep(3)
        logger.info(f"pptx successfully exported: {path}")
        return self
