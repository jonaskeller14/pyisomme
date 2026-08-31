from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any, Generic, TypeVar, cast

import plotly.graph_objects as go

from pyisomme.limit_set import LimitSet
from pyisomme.plotting2 import plot_line
from pyisomme.plotting2.plot_line import ChannelPanels
from pyisomme.report.base_report import BaseReport
from pyisomme.report.page2.figure import FigurePage

R = TypeVar("R", bound=BaseReport)
S_contra = TypeVar("S_contra", contravariant=True)
ChannelSelector = Callable[[S_contra], ChannelPanels]


def _channels_required(_: S_contra) -> ChannelPanels: # pyright: ignore[reportInvalidTypeVarUse]
    raise RuntimeError("ChannelPlotSpec requires channels via with_channels().")


@dataclass(frozen=True)
class ChannelPlotSpec(Generic[S_contra]):
    """Reusable rules for selecting and laying out a channel plot."""

    name: str
    title: str
    channels: ChannelSelector[S_contra]
    nrows: int | None = None
    ncols: int | None = None
    sharex: bool = False
    sharey: bool = False
    xlim: tuple[float | int, float | int] | None = None
    ylim: tuple[float | int, float | int] | None = None
    limits: LimitSet | dict | None = None
    footer: str | None = None

    def with_channels(
        self, channels: ChannelSelector[S_contra]
    ) -> ChannelPlotSpec[S_contra]:
        """Return a copy with a report-specific channel selector."""
        return replace(self, channels=channels)


def channel_plot_spec_for(
    _report: R,
    *,
    name: str,
    title: str,
    nrows: int | None = None,
    ncols: int | None = None,
    sharex: bool = False,
    sharey: bool = False,
    xlim: tuple[float | int, float | int] | None = None,
    ylim: tuple[float | int, float | int] | None = None,
    limits: LimitSet | dict | None = None,
    footer: str | None = None,
) -> ChannelPlotSpec[R]:
    """Create a plot spec bound to the concrete report type."""
    return ChannelPlotSpec(
        name=name,
        title=title,
        channels=_channels_required,
        nrows=nrows,
        ncols=ncols,
        sharex=sharex,
        sharey=sharey,
        xlim=xlim,
        ylim=ylim,
        limits=limits,
        footer=footer,
    )


class ChannelPlotPage(FigurePage[R], Generic[R]):
    """A composable grid of interactive ISO-MME channel plots."""

    spec: ChannelPlotSpec[R]

    def __init__(
        self,
        report: R,
        *,
        spec: ChannelPlotSpec[R],
    ) -> None:
        self.spec = spec
        limits = spec.limits if spec.limits is not None else cast(Any, report).limits

        def build(
            current_report: R, figsize: tuple[float | int, float | int]
        ) -> go.Figure:
            return plot_line(
                spec.channels(current_report),
                nrows=spec.nrows,
                ncols=spec.ncols,
                sharex=spec.sharex,
                sharey=spec.sharey,
                xlim=spec.xlim,
                ylim=spec.ylim,
                limits=cast(Any, limits),
                figsize=figsize,
            )

        super().__init__(
            report,
            name=spec.name,
            title=spec.title,
            figure_builder=build,
            footer=spec.footer,
        )


__all__ = [
    "ChannelPlotPage",
    "ChannelPlotSpec",
    "ChannelSelector",
    "channel_plot_spec_for",
]
