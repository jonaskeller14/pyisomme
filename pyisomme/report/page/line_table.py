from __future__ import annotations

from abc import ABC
from typing_extensions import override
from matplotlib.figure import Figure
import numpy as np

from pyisomme.channel import Channel
from pyisomme.isomme import Isomme
from pyisomme.plotting import Plot_Line_Table
from pyisomme.report.page.figure import Page_Figure


class Page_Line_Table(Page_Figure, ABC):
    channels: dict[Isomme, list[list[Channel | str | None]]]
    cell_texts: list[np.ndarray | list[list]]
    row_labels: list[np.ndarray | list]
    col_labels: list[np.ndarray | list]
    cell_colors: list[np.ndarray | list[list]] | None = None
    col_labels_colors: list[np.ndarray | list] | None = None
    col_labels_fontweight: str | None = None
    nrows: int = 1
    ncols: int = 1
    sharex: bool = False
    sharey: bool = False
    xlim: tuple[float | int, float | int] | None = None
    ylim: tuple[float | int, float | int] | None = None

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
            limits=self.report.limits,
            figsize=figsize,
        ).fig
