# matplotlib 3.7.5 ships no stubs and pandas' typed signatures are narrower than its runtime
# behaviour, so Pylance flags calls that are correct here — DataFrame.truncate rejects the float
# index labels this module truncates on, and Axes.plot rejects the tuple linestyles matplotlib
# documents. None of that is a real defect, so the two rule families are switched off for this file.
# pyright: reportArgumentType=false, reportAttributeAccessIssue=false
from __future__ import annotations

import copy
import logging
from typing import TYPE_CHECKING, cast

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pyisomme.code import Code, combine_codes
from pyisomme.limit import Limit
from pyisomme.limits import Limits, limit_list_sort, limit_list_unique
from pyisomme.plotting.plot import Plot
from pyisomme.unit import Unit

if TYPE_CHECKING:
    from pyisomme.channel import Channel
    from pyisomme.isomme import Isomme


logger = logging.getLogger(__name__)


class Plot_Line(Plot):
    isomme_list: list[Isomme]
    channels: dict[Isomme, list[list[Channel | None]]]
    xlim: tuple[float, float] | None
    ylim: tuple[float, float] | None
    sharex: bool
    sharey: bool
    limits: dict[Isomme, Limits] | None = None
    legend: bool = True

    def __init__(
        self,
        channels: dict[Isomme, list[list[Channel | str | None]]],
        nrows: int | None = None,
        ncols: int | None = None,
        xlim: tuple[float, float] | None = None,
        ylim: tuple[float, float] | None = None,
        sharex: bool = True,
        sharey: bool = False,
        figsize: tuple[float, float] = (10, 10),
        legend: bool | None = None,
        limits: Limits | dict[Isomme, Limits] | None = None,
    ):
        super().__init__(figsize=figsize, nrows=nrows, ncols=ncols)

        self.isomme_list = list(channels.keys())

        # Replace Channel-Code with Channel
        self.channels = {
            isomme: [
                [
                    isomme.get_channel(channel_ax)
                    if isinstance(channel_ax, str)
                    else channel_ax
                    for channel_ax in channel_ax_list
                ]
                for channel_ax_list in channel_list
            ]
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

        if legend is not None:
            self.legend = legend

        self.fig = self.plot()

    def plot(self) -> Figure:
        fig, subplot_axs = plt.subplots(
            self.nrows, self.ncols, figsize=self.figsize, layout="constrained"
        )
        fig = cast(
            Figure, fig
        )  # matplotlib is unstubbed: inferred as FigureBase | Unknown
        if (self.nrows * self.ncols) == 1:
            axs = [
                subplot_axs,
            ]
        else:
            axs = list(subplot_axs.flat)

        # Remove empty axes
        for idx, ax in enumerate(axs):
            if idx >= max([len(self.channels[isomme]) for isomme in self.isomme_list]):
                ax.remove()
                break

        self.plot_lines(axs)

        return fig

    def plot_lines(self, axs: list[Axes]) -> None:
        # Plot Channels
        codes_plotted, y_units = self.plot_channel(axs)

        # X-Range
        xlims = self.determine_xlims(axs)

        # Find Limits
        limit_list_dict: dict[Axes, list[Limit]] = {ax: [] for ax in axs}
        if self.limits is not None:
            for ax in axs:
                for isomme in self.isomme_list:
                    limit_list_dict[ax] += self.limits[isomme].find_limits(
                        *(codes_plotted[ax][isomme])
                    )

        # Limit (Line)
        for idx, ax in enumerate(axs):
            if self.limits is not None:
                self.plot_line_limits(
                    ax,
                    limit_list_dict[ax],
                    xlim=xlims[idx],
                    x_unit="ms",
                    y_unit=y_units[ax],
                    label=False,
                )

        # Y-Range
        ylims = self.determine_ylims(axs)

        # Limit (Fill+Text)
        for idx, ax in enumerate(axs):
            if self.limits is not None:
                self.plot_fill_limits(
                    ax,
                    limit_list_dict[ax],
                    xlim=xlims[idx],
                    ylim=ylims[idx],
                    x_unit="ms",
                    y_unit=y_units[ax],
                )
                self.plot_text_limits(
                    ax,
                    limit_list_dict[ax],
                    xlim=xlims[idx],
                    ylim=ylims[idx],
                    x_unit="ms",
                    y_unit=y_units[ax],
                )

            if self.legend:
                ax.legend(loc="upper right")
            ax.yaxis.set_tick_params(labelleft=True)
            ax.grid(True)
            ax.set_xlim(xlims[idx])
            ax.set_ylim(ylims[idx])

    def plot_channel(
        self, axs: list[Axes]
    ) -> tuple[dict[Axes, dict[Isomme, list[Code]]], dict[Axes, Unit | None]]:
        codes_plotted: dict[Axes, dict[Isomme, list[Code]]] = {
            ax: {isomme: [] for isomme in self.isomme_list} for ax in axs
        }
        y_units: dict[Axes, Unit | None] = {ax: None for ax in axs}

        for idx, ax in enumerate(axs):
            ax.margins(x=0, y=0)
            for idx_isomme, isomme in enumerate(self.isomme_list):
                if idx >= len(self.channels[isomme]):
                    continue
                channels = self.channels[isomme][idx]
                for idx2, channel in enumerate(channels):
                    if channel is None:
                        continue
                    unit = y_units[ax]
                    if unit is None:
                        unit = channel.unit
                        y_units[ax] = unit

                    logger.debug(f"Plotting {isomme} {channel}")

                    data = copy.deepcopy(channel.convert_unit(unit).data)
                    data.index *= 1000  # convert to ms
                    data = data.truncate(
                        before=self.xlim[0] if self.xlim is not None else None,
                        after=self.xlim[1] if self.xlim is not None else None,
                    )
                    ax.plot(
                        data,
                        c=self.colors[idx_isomme % len(self.colors)],
                        label=isomme.test_number
                        if len(channels) <= 1
                        else f"{isomme.test_number} {channel.code}",
                        ls=self.linestyles[idx2 % len(self.linestyles)],
                    )
                    if not ax.get_title():
                        ax.set_title(f"{channel.code}")
                    else:
                        ax.set_title(combine_codes(ax.get_title(), channel.code))
                    if not ax.get_xlabel():
                        ax.set_xlabel("Time [ms]")
                    if not ax.get_ylabel():
                        ax.set_ylabel(f"{channel.get_info('Dimension')} [{unit}]")
                    codes_plotted[ax][isomme].append(channel.code)
        return codes_plotted, y_units

    def determine_xlims(self, axs: list[Axes]) -> np.ndarray:
        if self.xlim is not None:
            xlims = np.array([self.xlim for ax in axs])
        else:
            xlims = np.array(
                [
                    (
                        ax.get_xlim()[0] - 0.05 * (ax.get_xlim()[1] - ax.get_xlim()[0]),
                        ax.get_xlim()[1] + 0.05 * (ax.get_xlim()[1] - ax.get_xlim()[0]),
                    )
                    for ax in axs
                ]
            )
            if self.sharey:
                xlims[:, 0] = np.min(xlims[:, 0])
                xlims[:, 1] = np.max(xlims[:, 1])
        return xlims

    def determine_ylims(self, axs: list[Axes]) -> np.ndarray:
        if self.ylim is not None:
            ylims = np.array([self.ylim for ax in axs])
        else:
            ylims = np.array(
                [
                    (
                        ax.get_ylim()[0] - 0.05 * (ax.get_ylim()[1] - ax.get_ylim()[0]),
                        ax.get_ylim()[1] + 0.05 * (ax.get_ylim()[1] - ax.get_ylim()[0]),
                    )
                    for ax in axs
                ]
            )
            if self.sharey:
                ylims[:, 0] = np.min(ylims[:, 0])
                ylims[:, 1] = np.max(ylims[:, 1])
        return ylims

    def plot_line_limits(
        self,
        ax: Axes,
        limit_list: list[Limit],
        xlim: tuple[float, float],
        x_unit: str | Unit | None,
        y_unit: str | Unit | None,
        label: bool = False,
    ) -> None:
        x = np.linspace(*xlim, 1000)
        # TODO: replace infinity values with ylim values to get vertical lines
        limit_list = limit_list_sort(limit_list)
        limit_list = limit_list_unique(limit_list, x=x, x_unit=x_unit, y_unit=y_unit)

        for limit in limit_list:
            ax.plot(
                x,
                limit.get_data(x, x_unit=x_unit, y_unit=y_unit),
                color=limit.color,
                linestyle=limit.linestyle,
                label=limit.name if label else None,
            )

    def plot_fill_limits(
        self,
        ax: Axes,
        limit_list: list[Limit],
        xlim: tuple[float, float],
        ylim: tuple[float, float],
        x_unit: str | Unit | None,
        y_unit: str | Unit | None,
    ) -> None:
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
                        ax.fill(
                            np.concatenate([[x[0]], x, [x[-1]]]),
                            np.concatenate([[y_min], y, [y_min]]),
                            color=limit.color,
                            alpha=0.2,
                        )

                # Prevent double fill (because transparency)
                elif idx >= 1 and limit_list[idx - 1].lower:
                    logger.debug(
                        f"Preventing double fill: {limit} and {limit_list[idx - 1]}"
                    )

                # Default upper case
                else:
                    previous_limit = limit_list[idx - 1]
                    y_1 = limit.get_data(x, x_unit=x_unit, y_unit=y_unit)
                    x_2 = x[::-1]
                    y_2 = previous_limit.get_data(x_2, x_unit=x_unit, y_unit=y_unit)
                    ax.fill(
                        np.concatenate([x, x_2]),
                        np.concatenate([y_1, y_2]),
                        color=limit.color,
                        alpha=0.2,
                    )

            if limit.lower:
                # Fill to plus infinity
                if idx == len(limit_list) - 1:
                    y = limit.get_data(x, x_unit=x_unit, y_unit=y_unit)
                    if np.any(y_max >= y):
                        ax.fill(
                            np.concatenate([[x[0]], x, [x[-1]]]),
                            np.concatenate([[y_max], y, [y_max]]),
                            color=limit.color,
                            alpha=0.2,
                        )

                # Default lower case
                else:
                    next_limit = limit_list[idx + 1]
                    y_1 = limit.get_data(x, x_unit=x_unit, y_unit=y_unit)
                    x_2 = x[::-1]
                    y_2 = next_limit.get_data(x_2, x_unit=x_unit, y_unit=y_unit)
                    ax.fill(
                        np.concatenate([x, x_2]),
                        np.concatenate([y_1, y_2]),
                        color=limit.color,
                        alpha=0.2,
                    )

    def plot_text_limits(
        self,
        ax: Axes,
        limit_list: list[Limit],
        xlim: tuple[float, float],
        ylim: tuple[float, float],
        x_unit: str | Unit | None,
        y_unit: str | Unit | None,
    ) -> None:
        x = np.linspace(*xlim, 1000)
        x0 = x[0]

        limit_list = limit_list_sort(limit_list)
        limit_list = limit_list_unique(limit_list, x=x, x_unit=x_unit, y_unit=y_unit)

        for limit in limit_list:
            if limit.name is None:
                continue
            y0 = float(limit.get_data(x0, x_unit=x_unit, y_unit=y_unit))
            if not ylim[0] <= y0 <= ylim[1]:
                logger.warning(f"Label of {limit} not visible.")
                continue
            ax.text(
                x0,
                y0,
                limit.name,
                color="black",
                bbox={"facecolor": limit.color, "edgecolor": "black", "linewidth": 1},
                verticalalignment="top"
                if limit.upper
                else "bottom"
                if limit.lower
                else "center",
            )
