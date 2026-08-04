from __future__ import annotations

from pyisomme import Channel
from pyisomme.isomme import Isomme
from pyisomme.report.page import Page_Cover, Page_Criterion_Table
from pyisomme.report.report import Report
from pyisomme.report.criterion import Criterion, Role
from pyisomme.correlation import Correlation_ISO18571

import logging
import numpy as np
from typing import Any, cast


logger = logging.getLogger(__name__)


def _curve_sort_key(criterion: Overall.Criterion_Curve_Correlation) -> str:
    return str(criterion.channel_r.code) if criterion.channel_r is not None else ""


class Overall(Criterion):
    name = "Overall"
    role = Role.AGGREGATE
    is_reference: bool | None = None
    is_comparison: bool | None = None

    def __init__(self, report: Report, isomme: Isomme) -> None:
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
            self.add_child(name, self.Criterion_Curve_Correlation(
                report=report,
                isomme=isomme,
                channel_r=isomme_r.get_channel(code),
                channel_c=isomme_c.get_channel(code, calculate=False, integrate=False, differentiate=False)))

    @property
    def criteria(self) -> list[Overall.Criterion_Curve_Correlation]:
        """The per-channel criteria, in the order the reference test lists its channels."""
        return [child for _, child in self.get_children()
                if isinstance(child, Overall.Criterion_Curve_Correlation)]

    def calculation(self) -> None:
        if not self.is_comparison:
            return

        self.value = np.nanmin([criterion.value for criterion in self.criteria])

    class Criterion_Curve_Correlation(Criterion):
        name = "Correlation"
        channel_r: Channel | None = None
        channel_c: Channel | None = None

        def __init__(self, report: Report, isomme: Isomme, channel_r: Channel | None, channel_c: Channel | None) -> None:
            self.name = f"{channel_c.code if channel_c is not None else np.nan}"

            super().__init__(report, isomme)

            self.channel_r = channel_r
            self.channel_c = channel_c

        def calculation(self) -> None:
            if self.isomme == self.report.isomme_list[0]:
                # The reference test is not correlated against itself. The guard used to
                # sit in `Overall.calculation()`, which skipped the whole loop; now that
                # the framework owns the children it has to live where the work is.
                return
            if self.channel_r is not None and self.channel_c is not None and self.channel_r is not self.channel_c:
                self.value = Correlation_ISO18571(reference_channel=self.channel_r,
                                                  comparison_channel=self.channel_c).overall_rating()
                self.color = "green" if self.value > 0.75 else "orange" if self.value > 0.5 else "red"


class Correlation(Report[Overall]):
    name = "Correlation"
    protocol = "ISO-18571:2024"
    protocols = {
        "ISO-18571:2024": "Objective Rating Metric for non ambigious signals according to ISO/TS 18571:2024 "
                          "[https://www.iso.org/standard/85791.html][https://openvt.eu/validation-metrics/ISO18571]",
    }

    #: The report's criterion tree, defined at module level (see `Overall`).
    Criterion_Overall = Overall

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.pages = [
            Page_Cover(self),
            self.Page_Correlation_Overall_Rating_Table(self),
        ]

    class Page_Correlation_Overall_Rating_Table(Page_Criterion_Table):
        report: Correlation
        name = "Correlation Overall Rating Table"
        title = "Correlation Overall Rating"
        row_label = staticmethod(lambda criterion: f"{criterion.name}")
        cell_text = staticmethod(lambda criterion: f"{criterion.value:.1%}")

        def __init__(self, report: Correlation) -> None:
            super().__init__(report)

            self.criteria = {isomme: cast("list[Criterion]",
                                          sorted(self.report.criterion_overall[isomme].criteria, key=_curve_sort_key))
                             for isomme in self.report.isomme_list}
