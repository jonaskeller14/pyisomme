from __future__ import annotations

from pyisomme.limits import Limits, limit_list_unique, limit_list_sort
from pyisomme.channel import Channel
from pyisomme.isomme import Isomme

import copy
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import logging


logger = logging.getLogger(__name__)


class Plot:
    colors = mcolors.TABLEAU_COLORS.values()
    linestyles = ("-", "--", "-.", ":")
    isomme_list: list
    figsize: tuple
    fig: plt.Figure

    def __init__(self, isomme_list: list, figsize: tuple):
        self.isomme_list = isomme_list
        self.figsize = figsize


class Plot_Line(Plot):
    channels: dict[Isomme, list[list[Channel]]]
    nrows: int = 1
    ncols: int = 1
    sharex: bool
    sharey: bool
    limits: dict[Isomme, Limits] | None = None

    def __init__(self,
                 channels: dict[Isomme, list[list[Channel | str]]],
                 nrows: int = None,
                 ncols: int = None,
                 xlim: tuple = None,
                 ylim: tuple = None,
                 sharex: bool = True,
                 sharey: bool = False,
                 figsize: tuple = (10, 10),
                 limits: Limits | dict[Isomme, Limits] = None):
        super().__init__(isomme_list=list(channels.keys()), figsize=figsize)

        for isomme, channel_list in channels.items():
            for idx_ax, channel_ax_list in enumerate(channel_list):
                for idx, channel_ax in enumerate(channel_ax_list):
                    if isinstance(channel_ax, str):
                        channels[isomme][idx_ax][idx] = isomme.get_channel(channel_ax)
        self.channels = channels

        if nrows is not None:
            self.nrows = nrows
        if ncols is not None:
            self.ncols = ncols

        self.xlim = xlim
        self.ylim = ylim

        self.sharex = sharex
        self.sharey = sharey

        if isinstance(limits, dict):
            self.limits = limits
        elif isinstance(limits, Limits):
            self.limits = {isomme: limits for isomme in self.isomme_list}

        self.fig = self.plot()

    def plot(self):
        fig, axs = plt.subplots(self.nrows, self.ncols, figsize=self.figsize, sharey=self.sharey, layout="constrained")
        if (self.nrows * self.ncols) == 1:
            axs = [axs, ]
        else:
            axs = list(axs.flat)

        y_units = {ax: None for ax in axs}
        codes_plotted = {ax: {isomme: [] for isomme in self.isomme_list} for ax in axs}

        for idx, ax in enumerate(axs):
            if idx >= max([len(self.channels[isomme]) for isomme in self.isomme_list]):
                ax.remove()
                break

            ax.margins(x=0, y=0)
            for isomme, color in zip(self.isomme_list, self.colors):
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
                    ax.plot(data, c=color, label=isomme.test_number if len(channels) <= 1 else f"{isomme.test_number} {channel.code}", ls=self.linestyles[idx2 % len(self.linestyles)])
                    if not ax.get_title():
                        ax.set_title(f"{channel.code}")
                    if not ax.get_xlabel():
                        ax.set_xlabel('Time [ms]')
                    if not ax.get_ylabel():
                        ax.set_ylabel(f"{channel.get_info('Dimension')} [{y_units[ax]}]")
                    codes_plotted[ax][isomme].append(channel.code)

        xlim_dict = {ax: self.xlim if self.xlim is not None else ax.get_xlim() if not self.sharex else (min([a.get_xlim()[0] for a in axs]), max([a.get_xlim()[1] for a in axs])) for ax in axs}

        # Limits
        limit_list_dict = {ax: [] for ax in axs}
        if self.limits is not None:
            for ax in axs:
                for isomme in self.isomme_list:
                    limit_list_dict[ax] += self.limits[isomme].find_limits(*(codes_plotted[ax][isomme]))

        # Limit (Line)
        for ax in axs:
            if self.limits is not None:
                self.plot_line_limits(ax, limit_list_dict[ax], xlim=xlim_dict[ax], x_unit="ms", y_unit=y_units[ax], label=False)

        ylim_dict = {ax: self.ylim if self.ylim is not None else ax.get_ylim() if not self.sharey else (min([a.get_ylim()[0] for a in axs]), max([a.get_ylim()[1] for a in axs])) for ax in axs}

        # Limit (Fill+Text)
        for ax in axs:
            if self.limits is not None:
                self.plot_fill_limits(ax, limit_list_dict[ax], xlim=xlim_dict[ax], ylim=ylim_dict[ax], x_unit="ms", y_unit=y_units[ax])
                self.plot_text_limits(ax, limit_list_dict[ax], xlim=xlim_dict[ax], ylim=ylim_dict[ax], x_unit="ms", y_unit=y_units[ax])

            ax.legend(loc='upper right')
            ax.yaxis.set_tick_params(labelleft=True)
            ax.grid(True)
            ax.set_xlim(xlim_dict[ax])
            ax.set_ylim(ylim_dict[ax])
        return fig

    def plot_line_limits(self, ax, limit_list, xlim, x_unit, y_unit, label=False):
        x = np.linspace(*xlim, 1000)

        limit_list = limit_list_sort(limit_list)
        limit_list = limit_list_unique(limit_list, x=x, x_unit=x_unit, y_unit=y_unit)

        for limit in limit_list:
            ax.plot(x, limit.get_data(x, x_unit=x_unit, y_unit=y_unit), color=limit.color, linestyle=limit.linestyle, label=limit.name if label else None)

    def plot_fill_limits(self, ax, limit_list, xlim, ylim, x_unit, y_unit):
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

    def plot_text_limits(self, ax, limit_list, xlim, ylim, x_unit, y_unit):
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


class Plot_Values(Plot):
    pass
    # TODO: plot_limits (t=0) und werte als linien