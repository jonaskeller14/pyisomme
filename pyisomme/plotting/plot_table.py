# matplotlib 3.7.5 ships no stubs, so Pylance falls back on its own bundled ones, which type the
# Axes.table arguments as Sequence[str] although the runtime accepts the ndarray/list-of-list cell
# blocks this module passes. None of that is a real defect, so the two rule families it produces are
# switched off rather than papered over at every argument.
# pyright: reportArgumentType=false, reportAttributeAccessIssue=false
from __future__ import annotations

from pyisomme.plotting.plot import Plot

from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import numpy as np
import logging
from typing import cast


logger = logging.getLogger(__name__)


class Plot_Table(Plot):
    cell_texts: list[np.ndarray | list[list]]
    cell_colors: list[np.ndarray | list[list]] | None = None
    row_labels: list[np.ndarray | list]
    col_labels: list[np.ndarray | list]
    col_labels_colors: list[np.ndarray | list] | None = None
    col_labels_fontweight: str = "bold"

    def __init__(self,
                 cell_texts: list[np.ndarray | list[list]],
                 row_labels: list[np.ndarray | list],
                 col_labels: list[np.ndarray | list],
                 cell_colors: list[np.ndarray | list[list]] | None = None,
                 col_labels_colors: list[np.ndarray | list] | None = None,
                 col_labels_fontweight: str | None = None,
                 nrows: int | None = None,
                 ncols: int | None = None,
                 figsize: tuple[float, float] = (10, 10)):
        super().__init__(figsize=figsize, nrows=nrows, ncols=ncols)

        self.cell_texts = cell_texts
        self.row_labels = row_labels
        self.col_labels = col_labels

        if cell_colors is not None:
            self.cell_colors = cell_colors
        if col_labels_colors is not None:
            self.col_labels_colors = col_labels_colors
        if col_labels_fontweight is not None:
            self.col_labels_fontweight = col_labels_fontweight

        if self.cell_colors is None:
            self.cell_colors = [[[None for _ in row] for row in cell_text] for cell_text in self.cell_texts]

        self.fig = self.plot()

    def plot(self) -> Figure:
        fig, subplot_axs = plt.subplots(self.nrows, self.ncols, figsize=self.figsize, layout="constrained")
        fig = cast(Figure, fig)  # matplotlib is unstubbed: inferred as FigureBase | Unknown
        if (self.nrows * self.ncols) == 1:
            axs = [subplot_axs, ]
        else:
            axs = list(subplot_axs.flat)
        axs = cast("list[Axes]", axs)

        # Some type checkers may not recognize Figure.patch; access safely
        _patch = getattr(fig, "patch", None)
        if _patch is not None:
            _patch.set_visible(False)

        self.plot_tables(axs)

        return fig

    def plot_tables(self, axs: list[Axes]) -> None:
        cell_colors = self.cell_colors
        assert cell_colors is not None  # resolved to a concrete list in __init__

        for idx, ax in enumerate(axs):
            ax.axis('off')
            ax.axis('tight')

            table = ax.table(cellText=self.cell_texts[idx],
                             cellColours=cell_colors[idx],
                             cellLoc="center",
                             rowLabels=self.row_labels[idx],
                             colLabels=self.col_labels[idx],
                             loc="center",)
            table.scale(1, 3)
            table.set_fontsize(20)

            for idx in range(len(self.cell_texts[0][0])):
                if self.col_labels_colors is not None:
                    table[0, idx].get_text().set_color(self.col_labels_colors[0][idx])
                if self.col_labels_fontweight is not None:
                    table[0, idx].get_text().set_fontweight(self.col_labels_fontweight)
