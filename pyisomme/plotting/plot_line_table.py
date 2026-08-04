# Same matplotlib/pandas stub friction as plot_line.py and plot_table.py, whose methods this class
# combines — see the note in either module.
# pyright: reportArgumentType=false, reportAttributeAccessIssue=false
from __future__ import annotations

from pyisomme.limits import Limits
from pyisomme.plotting.plot import Plot
from pyisomme.plotting.plot_line import Plot_Line
from pyisomme.plotting.plot_table import Plot_Table

from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import numpy as np
import logging
from typing import cast, TYPE_CHECKING

if TYPE_CHECKING:
    from pyisomme.isomme import Isomme
    from pyisomme.channel import Channel


logger = logging.getLogger(__name__)


class Plot_Line_Table(Plot_Line, Plot_Table):
    def __init__(self,
                 channels: dict[Isomme, list[list[Channel | str | None]]],
                 cell_texts: list[np.ndarray | list[list]],
                 row_labels: list[np.ndarray | list],
                 col_labels: list[np.ndarray | list],
                 xlim: tuple[float, float] | None = None,
                 ylim: tuple[float, float] | None = None,
                 sharex: bool = True,
                 sharey: bool = False,
                 limits: Limits | dict[Isomme, Limits] | None = None,
                 cell_colors: list[np.ndarray | list[list]] | None = None,
                 col_labels_colors: list[np.ndarray | list] | None = None,
                 col_labels_fontweight: str | None = None,
                 nrows: int | None = None,
                 ncols: int | None = None,
                 figsize: tuple[float, float] = (10, 10)):
        Plot.__init__(self, figsize=figsize, nrows=nrows, ncols=ncols)

        # Line
        self.isomme_list = list(channels.keys())

        # Replace Channel-Code with Channel
        self.channels = {
            isomme: [[isomme.get_channel(channel_ax) if isinstance(channel_ax, str) else channel_ax
                      for channel_ax in channel_ax_list]
                     for channel_ax_list in channel_list]
            for isomme, channel_list in channels.items()
        }

        self.xlim = xlim
        self.ylim = ylim

        self.sharex = sharex
        self.sharey = sharey

        if isinstance(limits, dict):
            self.limits = limits
        elif isinstance(limits, Limits):
            self.limits = {isomme: limits for isomme in self.isomme_list}

        # Table
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
            self.cell_colors = [[[(0,0,0,0) for _ in row] for row in cell_text] for cell_text in self.cell_texts]

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

        n_lines = max([len(self.channels[isomme]) for isomme in self.isomme_list])
        n_tables = len(self.cell_texts)

        axs_lines = axs[:n_lines]
        axs_tables = axs[n_lines:n_lines + n_tables]

        # Remove empty axes
        for idx, ax in enumerate(axs):
            if idx >= (n_lines + n_tables):
                ax.remove()
                break

        self.plot_lines(axs_lines)
        self.plot_tables(axs_tables)

        return fig
