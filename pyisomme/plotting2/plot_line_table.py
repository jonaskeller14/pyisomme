from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Literal

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from pyisomme.limit_set import LimitSet
from pyisomme.plotting2.config import DEFAULT_CONFIG
from pyisomme.plotting2.plot_line import (
    ChannelPanels,
    FigureSize,
    Range,
    _add_line_panels,
    _prepare_line_panels,
    _resolve_grid,
    _subplot_spacing,
)
from pyisomme.plotting2.plot_table import (
    MatrixLike,
    VectorLike,
    _make_table_trace,
    _validate_table_inputs,
)

if TYPE_CHECKING:
    from pyisomme.isomme import Isomme


def plot_line_table(
    channels: ChannelPanels,
    cell_texts: Sequence[MatrixLike],
    row_labels: Sequence[VectorLike],
    col_labels: Sequence[VectorLike],
    xlim: Range | None = None,
    ylim: Range | None = None,
    sharex: bool = True,
    sharey: bool = False,
    limits: LimitSet | Mapping[Isomme, LimitSet] | None = None,
    cell_colors: Sequence[MatrixLike | None] | None = None,
    row_labels_colors: Sequence[VectorLike | None] | None = None,
    col_labels_colors: Sequence[VectorLike | None] | None = None,
    col_labels_fontweight: Literal["normal", "bold"] = "bold",
    nrows: int | None = None,
    ncols: int | None = None,
    figsize: FigureSize = DEFAULT_CONFIG.default_figsize,
    legend: bool = True,
    colors: Sequence[str] = DEFAULT_CONFIG.colors,
    line_dashes: Sequence[str] = DEFAULT_CONFIG.line_dashes,
    template: str | None = None,
) -> go.Figure:
    """Plot line charts followed by tables in one Plotly subplot grid."""
    panels = _prepare_line_panels(channels, xlim, colors, line_dashes, limits)
    _validate_table_inputs(
        cell_texts,
        row_labels,
        col_labels,
        cell_colors,
        row_labels_colors,
        col_labels_colors,
    )
    item_count = len(panels) + len(cell_texts)
    nrows, ncols = _resolve_grid(item_count, nrows, ncols)
    horizontal_spacing, vertical_spacing = _subplot_spacing(nrows, ncols, figsize)

    plot_types: list[str | None] = []
    plot_types.extend(["xy"] * len(panels))
    plot_types.extend(["table"] * len(cell_texts))
    plot_types.extend([None] * (nrows * ncols - item_count))
    specs = [
        [
            None
            if plot_types[row * ncols + col] is None
            else {"type": plot_types[row * ncols + col]}
            for col in range(ncols)
        ]
        for row in range(nrows)
    ]
    fig = make_subplots(
        rows=nrows,
        cols=ncols,
        specs=specs,
        shared_xaxes=sharex,
        shared_yaxes=sharey,
        subplot_titles=[panel.title for panel in panels] + [""] * len(cell_texts),
        horizontal_spacing=horizontal_spacing,
        vertical_spacing=vertical_spacing,
    )

    line_positions = [
        (index // ncols + 1, index % ncols + 1) for index in range(len(panels))
    ]
    _add_line_panels(fig, panels, line_positions, xlim, ylim, sharex, sharey, legend)
    for table_index, cell_text in enumerate(cell_texts):
        index = len(panels) + table_index
        fig.add_trace(
            _make_table_trace(
                cell_text,
                row_labels[table_index],
                col_labels[table_index],
                None if cell_colors is None else cell_colors[table_index],
                None if row_labels_colors is None else row_labels_colors[table_index],
                None if col_labels_colors is None else col_labels_colors[table_index],
                col_labels_fontweight,
            ),
            row=index // ncols + 1,
            col=index % ncols + 1,
        )

    fig.update_layout(
        width=figsize[0],
        height=figsize[1],
        template=template,
        font={"family": DEFAULT_CONFIG.font_family},
        showlegend=legend,
        margin={"l": 60, "r": 20, "t": 50, "b": 50},
    )
    return fig


__all__ = ["plot_line_table"]
