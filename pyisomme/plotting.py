from __future__ import annotations

from pyisomme.limits import Limits, limit_list_unique, limit_list_sort
from pyisomme.channel import Channel
from pyisomme.code import combine_codes
from pyisomme.isomme import Isomme

import copy
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import logging


logger = logging.getLogger(__name__)


class Plot:
    colors: list = list(mcolors.TABLEAU_COLORS.values())
    linestyles: list = ["-", "--", "-.", ":", (0, (10, 3)), (0, (5, 1)), ]
    isomme_list: list
    figsize: tuple
    fig: plt.Figure
    nrows: int = 1
    ncols: int = 1

    def __init__(self, figsize: tuple, nrows: int, ncols: int):
        self.figsize = figsize
        if nrows is not None:
            self.nrows = nrows
        if ncols is not None:
            self.ncols = ncols

    def show(self, *args, **kwargs):
        plt.show(*args, **kwargs)
        return self


class Plot_Line(Plot):
    isomme_list: list[Isomme]
    channels: dict[Isomme, list[list[Channel]]]
    sharex: bool
    sharey: bool | str
    limits: dict[Isomme, Limits] | None = None
    legend: bool = True

    def __init__(self,
                 channels: dict[Isomme, list[list[Channel | str]]],
                 nrows: int = None,
                 ncols: int = None,
                 xlim: tuple[float | int, float | int] = None,
                 ylim: tuple[float | int, float | int] = None,
                 sharex: bool = True,
                 sharey: bool = False,
                 figsize: tuple = (10, 10),
                 legend: bool = None,
                 limits: Limits | dict[Isomme, Limits] = None):
        super().__init__(figsize=figsize, nrows=nrows, ncols=ncols)

        self.isomme_list = list(channels.keys())

        # Replace Channel-Code with Channel
        for isomme, channel_list in channels.items():
            for idx_ax, channel_ax_list in enumerate(channel_list):
                for idx, channel_ax in enumerate(channel_ax_list):
                    if isinstance(channel_ax, str):
                        channels[isomme][idx_ax][idx] = isomme.get_channel(channel_ax)

        self.channels = channels

        self.xlim = xlim
        self.ylim = ylim

        self.sharex = sharex
        self.sharey = sharey

        if isinstance(limits, dict):
            self.limits = limits
        elif isinstance(limits, Limits):
            self.limits = {isomme: limits for isomme in self.isomme_list}

        if legend is not None:
            self.legend = legend

        self.fig = self.plot()

    def plot(self) -> plt.Figure:
        fig, axs = plt.subplots(self.nrows, self.ncols, figsize=self.figsize, layout="constrained")
        if (self.nrows * self.ncols) == 1:
            axs = [axs, ]
        else:
            axs = list(axs.flat)

        # Remove empty axes
        for idx, ax in enumerate(axs):
            if idx >= max([len(self.channels[isomme]) for isomme in self.isomme_list]):
                ax.remove()
                break

        self.plot_lines(axs)

        return fig

    def plot_lines(self, axs) -> None:
        # Plot Channels
        codes_plotted, y_units = self.plot_channel(axs)

        # X-Range
        xlims = self.determine_xlims(axs)

        # Find Limits
        limit_list_dict = {ax: [] for ax in axs}
        if self.limits is not None:
            for ax in axs:
                for isomme in self.isomme_list:
                    limit_list_dict[ax] += self.limits[isomme].find_limits(*(codes_plotted[ax][isomme]))

        # Limit (Line)
        for idx, ax in enumerate(axs):
            if self.limits is not None:
                self.plot_line_limits(ax, limit_list_dict[ax], xlim=xlims[idx], x_unit="ms", y_unit=y_units[ax], label=False)

        # Y-Range
        ylims = self.determine_ylims(axs)

        # Limit (Fill+Text)
        for idx, ax in enumerate(axs):
            if self.limits is not None:
                self.plot_fill_limits(ax, limit_list_dict[ax], xlim=xlims[idx], ylim=ylims[idx], x_unit="ms", y_unit=y_units[ax])
                self.plot_text_limits(ax, limit_list_dict[ax], xlim=xlims[idx], ylim=ylims[idx], x_unit="ms", y_unit=y_units[ax])

            if self.legend:
                ax.legend(loc='upper right')
            ax.yaxis.set_tick_params(labelleft=True)
            ax.grid(True)
            ax.set_xlim(xlims[idx])
            ax.set_ylim(ylims[idx])

    def plot_channel(self, axs) -> tuple[dict, dict]:
        codes_plotted = {ax: {isomme: [] for isomme in self.isomme_list} for ax in axs}
        y_units = {ax: None for ax in axs}

        for idx, ax in enumerate(axs):
            ax.margins(x=0, y=0)
            for idx_isomme, isomme in enumerate(self.isomme_list):
                if idx >= len(self.channels[isomme]):
                    continue
                channels = self.channels[isomme][idx]
                for idx2, channel in enumerate(channels):
                    if channel is None:
                        continue
                    if y_units[ax] is None:
                        y_units[ax] = channel.unit

                    logger.debug(f"Plotting {isomme} {channel}")

                    data = copy.deepcopy(channel.convert_unit(y_units[ax]).data)
                    data.index *= 1000  # convert to ms
                    data = data.truncate(before=self.xlim[0] if self.xlim is not None else None,
                                         after=self.xlim[1] if self.xlim is not None else None)
                    ax.plot(data,
                            c=self.colors[idx_isomme % len(self.colors)],
                            label=isomme.test_number if len(channels) <= 1 else f"{isomme.test_number} {channel.code}",
                            ls=self.linestyles[idx2 % len(self.linestyles)])
                    if not ax.get_title():
                        ax.set_title(f"{channel.code}")
                    else:
                        ax.set_title(combine_codes(ax.get_title(), channel.code))
                    if not ax.get_xlabel():
                        ax.set_xlabel('Time [ms]')
                    if not ax.get_ylabel():
                        ax.set_ylabel(f"{channel.get_info('Dimension')} [{y_units[ax]}]")
                    codes_plotted[ax][isomme].append(channel.code)
        return codes_plotted, y_units

    def determine_xlims(self, axs) -> np.ndarray:
        if self.xlim is not None:
            xlims = np.array([self.xlim for ax in axs])
        else:
            xlims = np.array([(ax.get_xlim()[0] - 0.05 * (ax.get_xlim()[1] - ax.get_xlim()[0]),
                               ax.get_xlim()[1] + 0.05 * (ax.get_xlim()[1] - ax.get_xlim()[0])) for ax in axs])
            if self.sharey:
                xlims[:, 0] = np.min(xlims[:, 0])
                xlims[:, 1] = np.max(xlims[:, 1])
        return xlims

    def determine_ylims(self, axs) -> np.ndarray:
        if self.ylim is not None:
            ylims = np.array([self.ylim for ax in axs])
        else:
            ylims = np.array([(ax.get_ylim()[0] - 0.05 * (ax.get_ylim()[1] - ax.get_ylim()[0]),
                               ax.get_ylim()[1] + 0.05 * (ax.get_ylim()[1] - ax.get_ylim()[0])) for ax in axs])
            if self.sharey:
                ylims[:, 0] = np.min(ylims[:, 0])
                ylims[:, 1] = np.max(ylims[:, 1])
        return ylims

    def plot_line_limits(self, ax, limit_list, xlim, x_unit, y_unit, label=False) -> None:
        x = np.linspace(*xlim, 1000)
        # TODO: replace infinity values with ylim values to get vertical lines
        limit_list = limit_list_sort(limit_list)
        limit_list = limit_list_unique(limit_list, x=x, x_unit=x_unit, y_unit=y_unit)

        for limit in limit_list:
            ax.plot(x, limit.get_data(x, x_unit=x_unit, y_unit=y_unit), color=limit.color, linestyle=limit.linestyle, label=limit.name if label else None)

    def plot_fill_limits(self, ax, limit_list, xlim, ylim, x_unit, y_unit) -> None:
        x = np.linspace(*xlim, 1000)
        y_min, y_max = ylim

        limit_list = limit_list_sort(limit_list)
        limit_list = limit_list_unique(limit_list, x=x, x_unit=x_unit, y_unit=y_unit)

        for idx, limit in enumerate(limit_list):
            if limit.upper:
                # Fill to minus infinity
                if idx == 0:
                    y = limit.get_data(x, x_unit=x_unit, y_unit=y_unit)
                    if np.any(y_min <= y):
                        ax.fill(np.concatenate([[x[0]], x, [x[-1]]]),
                                np.concatenate([[y_min], y, [y_min]]),
                                color=limit.color, alpha=0.2)

                # Prevent double fill (because transparency)
                elif idx >= 1 and limit_list[idx - 1].lower:
                    logger.debug(f"Preventing double fill: {limit} and {limit_list[idx - 1]}")

                # Default upper case
                else:
                    previous_limit = limit_list[idx - 1]
                    y_1 = limit.get_data(x, x_unit=x_unit, y_unit=y_unit)
                    x_2 = x[::-1]
                    y_2 = previous_limit.get_data(x_2, x_unit=x_unit, y_unit=y_unit)
                    ax.fill(np.concatenate([x, x_2]),
                            np.concatenate([y_1, y_2]),
                            color=limit.color, alpha=0.2)

            if limit.lower:
                # Fill to plus infinity
                if idx == len(limit_list) - 1:
                    y = limit.get_data(x, x_unit=x_unit, y_unit=y_unit)
                    if np.any(y_max >= y):
                        ax.fill(np.concatenate([[x[0]], x, [x[-1]]]),
                                np.concatenate([[y_max], y, [y_max]]),
                                color=limit.color, alpha=0.2)

                # Default lower case
                else:
                    next_limit = limit_list[idx + 1]
                    y_1 = limit.get_data(x, x_unit=x_unit, y_unit=y_unit)
                    x_2 = x[::-1]
                    y_2 = next_limit.get_data(x_2, x_unit=x_unit, y_unit=y_unit)
                    ax.fill(np.concatenate([x, x_2]),
                            np.concatenate([y_1, y_2]),
                            color=limit.color, alpha=0.2)

    def plot_text_limits(self, ax, limit_list, xlim, ylim, x_unit, y_unit) -> None:
        x = np.linspace(*xlim, 1000)
        x0 = x[0]

        limit_list = limit_list_sort(limit_list)
        limit_list = limit_list_unique(limit_list, x=x, x_unit=x_unit, y_unit=y_unit)

        for limit in limit_list:
            if limit.name is None:
                continue
            if not ylim[0] <= limit.get_data(x0, x_unit=x_unit, y_unit=y_unit) <= ylim[1]:
                logger.warning(f"Label of {limit} not visible.")
                continue
            ax.text(x0, limit.get_data(x0, x_unit=x_unit, y_unit=y_unit), limit.name, color="black", bbox={"facecolor": limit.color, "edgecolor": "black", "linewidth": 1}, verticalalignment="top" if limit.upper else "bottom" if limit.lower else "center")


class Plot_Table(Plot):
    cell_texts: list[np.ndarray | list[list, ...]]
    cell_colors: list[np.ndarray | list[list, ...]] = None
    row_labels: list[np.ndarray | list]
    col_labels: list[np.ndarray | list]
    col_labels_colors: list[np.ndarray | list] = None
    col_labels_fontweight: str = "bold"

    def __init__(self,
                 cell_texts: list[np.ndarray | list[list, ...]],
                 row_labels: list[np.ndarray | list],
                 col_labels: list[np.ndarray | list],
                 cell_colors: list[np.ndarray | list[list, ...]] = None,
                 col_labels_colors: list[np.ndarray | list] = None,
                 col_labels_fontweight: str = None,
                 nrows: int = None,
                 ncols: int = None,
                 figsize: tuple = (10, 10)):
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

    def plot(self):
        fig, axs = plt.subplots(self.nrows, self.ncols, figsize=self.figsize, layout="constrained")
        if (self.nrows * self.ncols) == 1:
            axs = [axs, ]
        else:
            axs = list(axs.flat)

        fig.patch.set_visible(False)

        self.plot_tables(axs)

        return fig

    def plot_tables(self, axs: list) -> None:
        for idx, ax in enumerate(axs):
            ax.axis('off')
            ax.axis('tight')

            table = ax.table(cellText=self.cell_texts[idx],
                             cellColours=self.cell_colors[idx],
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


class Plot_Line_Table(Plot_Line, Plot_Table):
    def __init__(self,
                 channels: dict[Isomme, list[list[Channel | str]]],
                 cell_texts: list[np.ndarray | list[list, ...]],
                 row_labels: list[np.ndarray | list],
                 col_labels: list[np.ndarray | list],
                 xlim: tuple[float | int, float | int] = None,
                 ylim: tuple[float | int, float | int] = None,
                 sharex: bool = True,
                 sharey: bool = False,
                 limits: Limits | dict[Isomme, Limits] = None,
                 cell_colors: list[np.ndarray | list[list, ...]] = None,
                 col_labels_colors: list[np.ndarray | list] = None,
                 col_labels_fontweight: str = None,
                 nrows: int = None,
                 ncols: int = None,
                 figsize: tuple = (10, 10)):
        Plot.__init__(self, figsize=figsize, nrows=nrows, ncols=ncols)

        # Line
        self.isomme_list = list(channels.keys())

        # Replace Channel-Code with Channel
        for isomme, channel_list in channels.items():
            for idx_ax, channel_ax_list in enumerate(channel_list):
                for idx, channel_ax in enumerate(channel_ax_list):
                    if isinstance(channel_ax, str):
                        channels[isomme][idx_ax][idx] = isomme.get_channel(channel_ax)

        self.channels = channels

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

    def plot(self) -> plt.Figure:
        fig, axs = plt.subplots(self.nrows, self.ncols, figsize=self.figsize, layout="constrained")
        if (self.nrows * self.ncols) == 1:
            axs = [axs, ]
        else:
            axs = list(axs.flat)

        fig.patch.set_visible(False)

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
