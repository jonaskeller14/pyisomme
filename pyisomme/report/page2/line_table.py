from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, cast

import plotly.graph_objects as go

from pyisomme.limit_set import LimitSet
from pyisomme.plotting2 import plot_line_table
from pyisomme.plotting2.plot_line import ChannelPanels
from pyisomme.report.base_report import BaseReport
from pyisomme.report.page2.figure import FigurePage

R = TypeVar("R", bound=BaseReport)


@dataclass(frozen=True)
class TableData:
    cell_texts: Sequence[Sequence[Sequence[Any]]]
    row_labels: Sequence[Sequence[Any]]
    col_labels: Sequence[Sequence[Any]]
    cell_colors: Sequence[Sequence[Sequence[Any]] | None] | None = None
    col_labels_colors: Sequence[Sequence[Any] | None] | None = None


class LineTablePage(FigurePage[R], Generic[R]):
    """Interactive channel panels and tables in a single Plotly grid."""

    def __init__(
        self,
        report: R,
        *,
        name: str,
        title: str,
        channels: Callable[[R], ChannelPanels],
        table: Callable[[R], TableData],
        nrows: int | None = None,
        ncols: int | None = None,
        sharex: bool = False,
        sharey: bool = False,
        xlim: tuple[float | int, float | int] | None = None,
        ylim: tuple[float | int, float | int] | None = None,
        limits: LimitSet | dict | None = None,
        footer: str | None = None,
    ) -> None:
        resolved_limits = cast(Any, report).limits if limits is None else limits

        def build(
            current_report: R, figsize: tuple[float | int, float | int]
        ) -> go.Figure:
            data = table(current_report)
            return plot_line_table(
                channels=channels(current_report),
                cell_texts=data.cell_texts,
                row_labels=data.row_labels,
                col_labels=data.col_labels,
                cell_colors=data.cell_colors,
                col_labels_colors=data.col_labels_colors,
                nrows=nrows,
                ncols=ncols,
                sharex=sharex,
                sharey=sharey,
                xlim=xlim,
                ylim=ylim,
                limits=cast(Any, resolved_limits),
                figsize=figsize,
            )

        super().__init__(
            report,
            name=name,
            title=title,
            figure_builder=build,
            footer=footer,
        )


__all__ = ["LineTablePage", "TableData"]
