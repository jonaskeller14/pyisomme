from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any

import numpy as np
from matplotlib.figure import Figure
from typing_extensions import override

from pyisomme.channel import Channel
from pyisomme.isomme import Isomme
from pyisomme.limit_set import LimitSet
from pyisomme.plotting import Plot_Line_Table
from pyisomme.report.page.figure import Page_Figure

if TYPE_CHECKING:
    from pyisomme.report.report import Report


class Page_Line_Table(Page_Figure, ABC):
    channels: dict[Isomme, list[list[Channel | str | None]]]
    cell_texts: list[np.ndarray[Any, Any] | list[list[Any]]]
    row_labels: list[np.ndarray[Any, Any] | list[Any]]
    col_labels: list[np.ndarray[Any, Any] | list[Any]]
    cell_colors: list[np.ndarray[Any, Any] | list[list[Any]]] | None = None
    col_labels_colors: list[np.ndarray[Any, Any] | list[Any]] | None = None
    col_labels_fontweight: str | None = None
    nrows: int = 1
    ncols: int = 1
    sharex: bool = False
    sharey: bool = False
    xlim: tuple[float | int, float | int] | None = None
    ylim: tuple[float | int, float | int] | None = None
    limits: LimitSet | dict[Isomme, LimitSet] | None = None

    def __init__(
        self,
        report: Report[Any],
        limits: LimitSet | dict[Isomme, LimitSet] | None = None,
    ) -> None:
        super().__init__(report)
        self.limits = limits if limits is not None else report.limits

    @override
    def figure(self, figsize: tuple[float, float]) -> Figure:
        return Plot_Line_Table(
            channels=self.channels,
            cell_texts=self.cell_texts,
            row_labels=self.row_labels,
            col_labels=self.col_labels,
            cell_colors=self.cell_colors,
            col_labels_colors=self.col_labels_colors,
            col_labels_fontweight=self.col_labels_fontweight,
            nrows=self.nrows,
            ncols=self.ncols,
            sharex=self.sharex,
            sharey=self.sharey,
            xlim=self.xlim,
            ylim=self.ylim,
            limits=self.limits,
            figsize=figsize,
        ).fig
