from __future__ import annotations

import logging
from dataclasses import replace
from datetime import date
from typing import Any

import numpy as np

from pyisomme.channel import Channel
from pyisomme.correlation import Correlation_ISO18571
from pyisomme.isomme import Isomme
from pyisomme.report.criterion import Criterion, Role
from pyisomme.report.criterion_result import CriterionResult
from pyisomme.report.page2 import CoverPage, CriterionTablePage, rating_table_spec_for
from pyisomme.report.report import Report
from pyisomme.report.report_protocol import ReportProtocol

logger = logging.getLogger(__name__)


class Overall(Criterion):
    name = "Overall"
    role = Role.AGGREGATE
    is_reference: bool | None = None
    is_comparison: bool | None = None

    def __init__(self, report: Report[Any], isomme: Isomme) -> None:
        super().__init__(report, isomme)

        isomme_r = self.report.isomme_list[0]
        isomme_c = self.isomme

        self.is_reference = True if isomme_r == isomme_c else False
        self.is_comparison = True if isomme_r != isomme_c else False

        # This tree's *shape* is the data's: one criterion per channel of the reference
        # test, so it cannot be declared with `sub()`. `add_child` is the escape hatch
        # for exactly that (F6/A12) -- the children are then walked, printed and
        # calculated like any declared one.
        taken: set[str] = set()
        for channel_r in isomme_r.channels:
            code = channel_r.code.set(filter_class="D")
            # `channels` is a list, not a mapping, and `.set(filter_class=…)` collapses
            # the filter classes onto one code, so two entries can want the same name.
            name = str(channel_r.code)
            while name in taken:
                name += "'"
            taken.add(name)
            self.add_child(
                name,
                self.Criterion_Curve_Correlation(
                    report=report,
                    isomme=isomme,
                    channel_r=isomme_r.get_channel(code),
                    channel_c=isomme_c.get_channel(
                        code, calculate=False, integrate=False, differentiate=False
                    ),
                ),
            )

    @property
    def criteria(self) -> list[Overall.Criterion_Curve_Correlation]:
        """The per-channel criteria, in the order the reference test lists its channels."""
        return [
            child
            for _, child in self.get_children()
            if isinstance(child, Overall.Criterion_Curve_Correlation)
        ]

    def calculation(self) -> CriterionResult:
        if not self.is_comparison:
            return CriterionResult(
                channel=None, value=float(np.nan), rating=float(np.nan), color=None
            )

        value = np.nanmin(
            [Criterion.value_of(criterion) for criterion in self.criteria]
        )
        return CriterionResult(
            channel=None,
            value=value,
            rating=value,
            color=None,
        )

    class Criterion_Curve_Correlation(Criterion):
        name = "Correlation"
        channel_r: Channel | None = None
        channel_c: Channel | None = None

        def __init__(
            self,
            report: Report[Any],
            isomme: Isomme,
            channel_r: Channel | None,
            channel_c: Channel | None,
        ) -> None:
            self.name = f"{channel_c.code if channel_c is not None else np.nan}"

            super().__init__(report, isomme)

            self.channel_r = channel_r
            self.channel_c = channel_c

        def calculation(self) -> CriterionResult:
            value = float(np.nan)
            color = None
            if self.isomme == self.report.isomme_list[0]:
                # The reference test is not correlated against itself. The guard used to
                # sit in `Overall.calculation()`, which skipped the whole loop; now that
                # the framework owns the children it has to live where the work is.
                return CriterionResult(
                    channel=None, value=value, rating=value, color=color
                )
            if (
                self.channel_r is not None
                and self.channel_c is not None
                and self.channel_r is not self.channel_c
            ):
                value = Correlation_ISO18571(
                    reference_channel=self.channel_r, comparison_channel=self.channel_c
                ).overall_rating()
                color = "green" if value > 0.75 else "orange" if value > 0.5 else "red"
            return CriterionResult(
                channel=None,
                value=value,
                rating=value,
                color=color,
            )


PROTOCOL_ISO_18571_2024 = ReportProtocol(
    version="ISO-18571:2024",
    name="ISO/TS 18571:2024: Road vehicles — Objective rating metric for non-ambiguous signals",
    date=date(2024, 5, 1),
    sources=(
        "https://www.iso.org/standard/85791.html",
        "https://openvt.eu/validation-metrics/ISO18571",
    ),
)


class Correlation(Report[Overall]):
    _name = "Correlation"
    _protocol = PROTOCOL_ISO_18571_2024
    _protocols = (PROTOCOL_ISO_18571_2024,)
    Criterion_Overall = Overall

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._available_pages = (
            CoverPage(self),
            CriterionTablePage(
                self,
                name="Correlation Overall Rating Table",
                title="Correlation Overall Rating",
                spec=replace(
                    rating_table_spec_for(self),
                    row_label=lambda criterion: f"{criterion.name}",
                    cell_text=lambda criterion: f"{Criterion.value_of(criterion):.1%}",
                ).with_criteria(
                    lambda report: {
                        isomme: sorted(
                            report.overall(isomme).criteria,
                            key=lambda criterion: (
                                str(criterion.channel_r.code)
                                if isinstance(
                                    criterion, Overall.Criterion_Curve_Correlation
                                )
                                and criterion.channel_r is not None
                                else ""
                            ),
                        )
                        for isomme in report.isomme_list
                    }
                ),
            ),
        )
        self._selected_pages = list(self._available_pages)
