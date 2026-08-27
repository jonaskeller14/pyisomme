from __future__ import annotations

from typing import TYPE_CHECKING, Any

from matplotlib.figure import Figure
from typing_extensions import override

from pyisomme.channel import Channel
from pyisomme.isomme import Isomme
from pyisomme.limit_set import LimitSet
from pyisomme.plotting import Plot_Line
from pyisomme.report.page.figure import Page_Figure

if TYPE_CHECKING:
    from pyisomme.report.report import Report


class Page_Plot_nxn(Page_Figure):
    channels: dict[Isomme, list[list[Channel | str | None]]]
    nrows: int = 1
    ncols: int = 1
    sharex: bool = False
    sharey: bool = False
    xlim: tuple[float | int, float | int] | None = None
    ylim: tuple[float | int, float | int] | None = None
    limits: LimitSet | dict[Isomme, LimitSet] | None = None

    def __init__(
        self, report: Report[Any], limits: LimitSet | dict[Isomme, LimitSet] | None = None
    ) -> None:
        super().__init__(report)
        if self.title is None:
            self.title = self.name
        self.limits = limits if limits is not None else report.limits

    @override
    def figure(self, figsize: tuple[float, float]) -> Figure:
        return Plot_Line(
            self.channels,
            nrows=self.nrows,
            ncols=self.ncols,
            sharex=self.sharex,
            sharey=self.sharey,
            xlim=self.xlim,
            ylim=self.ylim,
            limits=self.limits,
            figsize=figsize,
        ).fig
