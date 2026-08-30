from __future__ import annotations

import logging
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Union

import numpy as np
import numpy.typing as npt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing_extensions import TypeAlias

from pyisomme.channel import Channel
from pyisomme.code import Code, combine_codes
from pyisomme.isomme import Isomme
from pyisomme.limit import Limit
from pyisomme.limit_set import LimitSet, limit_list_sort, limit_list_unique
from pyisomme.plotting2.config import DEFAULT_CONFIG
from pyisomme.unit import Unit

logger = logging.getLogger(__name__)

ChannelInput: TypeAlias = Union[Channel, str, None]
ChannelPanels: TypeAlias = Mapping[
    Isomme, Sequence[Sequence[ChannelInput]]
]
FigureSize: TypeAlias = tuple[Union[int, float], Union[int, float]]
Range: TypeAlias = tuple[float, float]


@dataclass(frozen=True)
class _ChannelTrace:
    x: npt.NDArray[np.float64]
    y: npt.NDArray[np.float64]
    name: str
    color: str
    dash: str
    legendgroup: str


@dataclass
class _LinePanel:
    title: str = ""
    y_title: str = ""
    unit: Unit | None = None
    traces: list[_ChannelTrace] = field(default_factory=list)
    codes: dict[Isomme, list[Code]] = field(default_factory=dict)
    limits: list[Limit] = field(default_factory=list)


def _resolve_grid(
    item_count: int, nrows: int | None, ncols: int | None
) -> tuple[int, int]:
    if item_count < 1:
        raise ValueError("At least one subplot is required.")
    if nrows is not None and nrows < 1 or ncols is not None and ncols < 1:
        raise ValueError("nrows and ncols must be positive integers.")
    if nrows is None and ncols is None:
        ncols = max(1, math.ceil(math.sqrt(item_count)))
        nrows = math.ceil(item_count / ncols)
    elif nrows is None:
        assert ncols is not None
        nrows = math.ceil(item_count / ncols)
    elif ncols is None:
        ncols = math.ceil(item_count / nrows)
    if nrows * ncols < item_count:
        raise ValueError(
            f"The {nrows}x{ncols} grid has fewer cells than the {item_count} plots."
        )
    return nrows, ncols


def _resolve_limits(
    limits: LimitSet | Mapping[Isomme, LimitSet] | None,
    isommes: Sequence[Isomme],
) -> dict[Isomme, LimitSet]:
    if limits is None:
        return {}
    if isinstance(limits, LimitSet):
        return {isomme: limits for isomme in isommes}
    missing = [isomme for isomme in isommes if isomme not in limits]
    if missing:
        raise ValueError(f"No LimitSet supplied for: {missing!r}")
    return dict(limits)


def _prepare_line_panels(
    channels: ChannelPanels,
    xlim: Range | None,
    colors: Sequence[str],
    line_dashes: Sequence[str],
    limits: LimitSet | Mapping[Isomme, LimitSet] | None,
) -> list[_LinePanel]:
    if not channels:
        raise ValueError("channels must contain at least one Isomme.")
    if not colors:
        raise ValueError("colors must not be empty.")
    if not line_dashes:
        raise ValueError("line_dashes must not be empty.")

    isommes = list(channels)
    panel_count = max(len(channel_groups) for channel_groups in channels.values())
    if panel_count == 0:
        raise ValueError("channels must contain at least one subplot.")
    limit_sets = _resolve_limits(limits, isommes)
    panels = [_LinePanel(codes={isomme: [] for isomme in isommes}) for _ in range(panel_count)]

    for panel_index, panel in enumerate(panels):
        title_codes: list[Code] = []
        for isomme_index, isomme in enumerate(isommes):
            groups = channels[isomme]
            if panel_index >= len(groups):
                continue
            group = groups[panel_index]
            for channel_index, channel_input in enumerate(group):
                channel = (
                    isomme.get_channel(channel_input)
                    if isinstance(channel_input, str)
                    else channel_input
                )
                if channel is None:
                    continue
                if panel.unit is None:
                    panel.unit = channel.unit
                if panel.unit is None:
                    raise ValueError(f"Channel {channel.code} has no unit.")

                x = np.asarray(channel.data.index, dtype=float) * 1000.0
                y = np.asarray(channel.get_data(unit=panel.unit), dtype=float)
                if xlim is not None:
                    selected = (x >= xlim[0]) & (x <= xlim[1])
                    x = x[selected]
                    y = y[selected]
                test_name = isomme.test_number or "Unnamed ISOMME"
                name = (
                    test_name if len(group) <= 1 else f"{test_name} {channel.code}"
                )
                panel.traces.append(
                    _ChannelTrace(
                        x=x,
                        y=y,
                        name=name,
                        color=colors[isomme_index % len(colors)],
                        dash=line_dashes[channel_index % len(line_dashes)],
                        legendgroup=f"{isomme_index}:{name}",
                    )
                )
                panel.codes[isomme].append(channel.code)
                title_codes.append(channel.code)
                if not panel.y_title:
                    dimension = channel.get_info("Dimension")
                    if dimension is None:
                        dimension = (
                            channel.code.get_info().get("Physical Dimension")
                            or channel.code.physical_dimension
                        )
                    panel.y_title = f"{dimension} [{panel.unit}]"

        if title_codes:
            panel.title = str(combine_codes(*title_codes))
        if limit_sets:
            for isomme in isommes:
                panel.limits.extend(
                    limit_sets[isomme].find_limits(*panel.codes[isomme])
                )
    return panels


def _padded_range(values: Sequence[npt.NDArray[np.float64]]) -> Range:
    finite_values = [value[np.isfinite(value)] for value in values]
    finite_values = [value for value in finite_values if value.size]
    if not finite_values:
        return (0.0, 1.0)
    minimum = min(float(np.min(value)) for value in finite_values)
    maximum = max(float(np.max(value)) for value in finite_values)
    span = maximum - minimum
    padding = span * 0.05 if span else max(abs(minimum) * 0.05, 0.5)
    return minimum - padding, maximum + padding


def _limit_dash(dash: str) -> str:
    return {
        "-": "solid",
        "--": "dash",
        "-.": "dashdot",
        ":": "dot",
    }.get(dash, dash)


def _ordered_limits(
    limits: Sequence[Limit], x: npt.NDArray[np.float64], unit: Unit | None
) -> list[Limit]:
    ordered = limit_list_sort(list(limits), x=x, x_unit="ms", y_unit=unit)
    return limit_list_unique(ordered, x=x, x_unit="ms", y_unit=unit)


def _add_limit_fills(
    fig: go.Figure,
    limits: Sequence[Limit],
    x: npt.NDArray[np.float64],
    y_range: Range,
    unit: Unit | None,
    row: int,
    col: int,
) -> None:
    for index, limit in enumerate(limits):
        y = np.asarray(limit.get_data(x, x_unit="ms", y_unit=unit), dtype=float)
        boundaries: list[npt.NDArray[np.float64]] = []
        if limit.upper:
            if index == 0:
                boundaries.append(np.full_like(x, y_range[0]))
            elif not limits[index - 1].lower:
                boundaries.append(
                    np.asarray(
                        limits[index - 1].get_data(
                            x, x_unit="ms", y_unit=unit
                        ),
                        dtype=float,
                    )
                )
        if limit.lower:
            if index == len(limits) - 1:
                boundaries.append(np.full_like(x, y_range[1]))
            else:
                boundaries.append(
                    np.asarray(
                        limits[index + 1].get_data(
                            x, x_unit="ms", y_unit=unit
                        ),
                        dtype=float,
                    )
                )
        for boundary in boundaries:
            fig.add_trace(
                go.Scatter(
                    x=np.concatenate((x, x[::-1])),
                    y=np.concatenate((y, boundary[::-1])),
                    mode="lines",
                    line={"width": 0},
                    fill="toself",
                    fillcolor=limit.color,
                    opacity=0.2,
                    hoverinfo="skip",
                    showlegend=False,
                ),
                row=row,
                col=col,
            )


def _add_line_panels(
    fig: go.Figure,
    panels: Sequence[_LinePanel],
    positions: Sequence[tuple[int, int]],
    xlim: Range | None,
    ylim: Range | None,
    sharex: bool,
    sharey: bool,
    legend: bool,
) -> None:
    x_ranges: list[Range] = []
    y_ranges: list[Range] = []
    ordered_limits: list[list[Limit]] = []
    legend_entries: set[tuple[str, str]] = set()

    for panel in panels:
        trace_x = [trace.x for trace in panel.traces]
        panel_x_range = xlim or _padded_range(trace_x)
        x_ranges.append(panel_x_range)
        limit_x = np.linspace(
            panel_x_range[0], panel_x_range[1], num=1000, dtype=float
        )
        panel_limits = _ordered_limits(panel.limits, limit_x, panel.unit)
        ordered_limits.append(panel_limits)
        trace_y = [trace.y for trace in panel.traces]
        limit_y = [
            np.asarray(limit.get_data(limit_x, x_unit="ms", y_unit=panel.unit), dtype=float)
            for limit in panel_limits
        ]
        y_ranges.append(ylim or _padded_range(trace_y + limit_y))

    if sharex and xlim is None:
        shared_x_range = (
            min(value[0] for value in x_ranges),
            max(value[1] for value in x_ranges),
        )
        x_ranges = [shared_x_range] * len(x_ranges)
    if sharey and ylim is None:
        shared_y_range = (
            min(value[0] for value in y_ranges),
            max(value[1] for value in y_ranges),
        )
        y_ranges = [shared_y_range] * len(y_ranges)

    for index, (panel, position) in enumerate(zip(panels, positions)):
        row, col = position
        for trace in panel.traces:
            legend_key = (trace.legendgroup, trace.name)
            show_legend_entry = legend and legend_key not in legend_entries
            legend_entries.add(legend_key)
            fig.add_trace(
                go.Scatter(
                    x=trace.x,
                    y=trace.y,
                    mode="lines",
                    name=trace.name,
                    legendgroup=trace.legendgroup,
                    line={"color": trace.color, "dash": trace.dash},
                    hovertemplate="%{x:.3f} ms<br>%{y:.4g}<extra>%{fullData.name}</extra>",
                    showlegend=show_legend_entry,
                ),
                row=row,
                col=col,
            )

        limit_x = np.linspace(
            x_ranges[index][0], x_ranges[index][1], num=1000, dtype=float
        )
        for limit in ordered_limits[index]:
            limit_y = np.asarray(
                limit.get_data(limit_x, x_unit="ms", y_unit=panel.unit), dtype=float
            )
            fig.add_trace(
                go.Scatter(
                    x=limit_x,
                    y=limit_y,
                    mode="lines",
                    line={"color": limit.color, "dash": _limit_dash(limit.linestyle)},
                    name=limit.name,
                    hoverinfo="skip",
                    showlegend=False,
                ),
                row=row,
                col=col,
            )
        _add_limit_fills(
            fig,
            ordered_limits[index],
            limit_x,
            y_ranges[index],
            panel.unit,
            row,
            col,
        )
        for limit in ordered_limits[index]:
            if limit.name is None:
                continue
            y = float(limit.get_data(limit_x[0], x_unit="ms", y_unit=panel.unit))
            if not y_ranges[index][0] <= y <= y_ranges[index][1]:
                logger.warning("Label of %s not visible.", limit)
                continue
            fig.add_annotation(
                x=limit_x[0],
                y=y,
                text=limit.name,
                showarrow=False,
                bgcolor=limit.color,
                bordercolor="black",
                borderwidth=1,
                xanchor="left",
                xshift=4,
                yanchor="top" if limit.upper else "bottom" if limit.lower else "middle",
                row=row,
                col=col,
            )
        fig.update_xaxes(
            title_text="Time [ms]", range=x_ranges[index], showgrid=True, row=row, col=col
        )
        fig.update_yaxes(
            title_text=panel.y_title or None,
            range=y_ranges[index],
            showgrid=True,
            row=row,
            col=col,
        )


def plot_line(
    channels: ChannelPanels,
    nrows: int | None = None,
    ncols: int | None = None,
    xlim: Range | None = None,
    ylim: Range | None = None,
    sharex: bool = True,
    sharey: bool = False,
    figsize: FigureSize = DEFAULT_CONFIG.linechart_figsize,
    legend: bool = True,
    limits: LimitSet | Mapping[Isomme, LimitSet] | None = None,
    colors: Sequence[str] = DEFAULT_CONFIG.colors,
    line_dashes: Sequence[str] = DEFAULT_CONFIG.line_dashes,
    template: str | None = None,
) -> go.Figure:
    """Plot ISO-MME channels as one or more interactive Plotly line charts."""
    panels = _prepare_line_panels(channels, xlim, colors, line_dashes, limits)
    nrows, ncols = _resolve_grid(len(panels), nrows, ncols)
    fig = make_subplots(
        rows=nrows,
        cols=ncols,
        shared_xaxes=sharex,
        shared_yaxes=sharey,
        subplot_titles=[panel.title for panel in panels],
        horizontal_spacing=DEFAULT_CONFIG.horizontal_spacing,
        vertical_spacing=DEFAULT_CONFIG.vertical_spacing,
    )
    positions = [(index // ncols + 1, index % ncols + 1) for index in range(len(panels))]
    _add_line_panels(fig, panels, positions, xlim, ylim, sharex, sharey, legend)
    fig.update_layout(
        width=figsize[0],
        height=figsize[1],
        template=template,
        font={"family": DEFAULT_CONFIG.font_family},
        showlegend=legend,
        margin={"l": 60, "r": 20, "t": 50, "b": 50},
    )
    return fig


__all__ = ["ChannelInput", "ChannelPanels", "FigureSize", "plot_line"]
