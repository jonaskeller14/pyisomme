from __future__ import annotations

from collections.abc import Callable
from typing import Any, Generic, TypeVar, cast

import plotly.graph_objects as go

from pyisomme.limit_set import LimitSet
from pyisomme.plotting2 import plot_line
from pyisomme.plotting2.plot_line import ChannelPanels
from pyisomme.report.base_report import BaseReport
from pyisomme.report.page2.figure import FigurePage

R = TypeVar("R", bound=BaseReport)
ChannelSelector = Callable[[R], ChannelPanels]


class ChannelPlotPage(FigurePage[R], Generic[R]):
    """A composable grid of interactive ISO-MME channel plots."""

    channels: ChannelPanels
    name: str
    title: str
    nrows: int | None = None
    ncols: int | None = None
    sharex: bool = False
    sharey: bool = False
    xlim: tuple[float | int, float | int] | None = None
    ylim: tuple[float | int, float | int] | None = None
    limits: LimitSet | dict | None = None
    footer: str | None = None

    def __init__(
        self,
        report: R,
        *,
        name: str | None = None,
        title: str | None = None,
        channels: ChannelSelector[R] | None = None,
        nrows: int | None = None,
        ncols: int | None = None,
        sharex: bool = False,
        sharey: bool = False,
        xlim: tuple[float | int, float | int] | None = None,
        ylim: tuple[float | int, float | int] | None = None,
        limits: LimitSet | dict | None = None,
        footer: str | None = None,
    ) -> None:
        selector = channels or (lambda _report: self.channels)
        resolved_limits = (
            cast(Any, report).limits
            if limits is None and self.limits is None
            else self.limits if limits is None else limits
        )
        resolved_nrows = self.nrows if nrows is None else nrows
        resolved_ncols = self.ncols if ncols is None else ncols
        resolved_xlim = self.xlim if xlim is None else xlim
        resolved_ylim = self.ylim if ylim is None else ylim

        def build(
            current_report: R, figsize: tuple[float | int, float | int]
        ) -> go.Figure:
            return plot_line(
                selector(current_report),
                nrows=resolved_nrows,
                ncols=resolved_ncols,
                sharex=self.sharex if not sharex else sharex,
                sharey=self.sharey if not sharey else sharey,
                xlim=resolved_xlim,
                ylim=resolved_ylim,
                limits=cast(Any, resolved_limits),
                figsize=figsize,
            )

        super().__init__(
            report,
            name=name or self.name,
            title=title or self.title,
            figure_builder=build,
            footer=self.footer if footer is None else footer,
        )


__all__ = ["ChannelPlotPage", "ChannelSelector"]
