from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal, Union

import numpy as np
import numpy.typing as npt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing_extensions import TypeAlias

from pyisomme.plotting2.config import DEFAULT_CONFIG
from pyisomme.plotting2.plot_line import FigureSize, _resolve_grid

MatrixLike: TypeAlias = Union[npt.NDArray[Any], Sequence[Sequence[Any]]]
VectorLike: TypeAlias = Union[npt.NDArray[Any], Sequence[Any]]


def _plotly_color(color: Any) -> Any:
    if color is None or isinstance(color, str):
        return "rgba(0,0,0,0)" if color is None else color
    if isinstance(color, (Sequence, np.ndarray)) and len(color) in (3, 4):
        components = [float(component) for component in color]
        rgb = components[:3]
        if max(rgb) <= 1:
            rgb = [component * 255 for component in rgb]
        red, green, blue = (round(component) for component in rgb)
        alpha = components[3] if len(components) == 4 else 1
        if alpha > 1:
            alpha /= 255
        return f"rgba({red},{green},{blue},{alpha:g})"
    return color


def _validate_table_inputs(
    cell_texts: Sequence[MatrixLike],
    row_labels: Sequence[VectorLike],
    col_labels: Sequence[VectorLike],
    cell_colors: Sequence[MatrixLike | None] | None,
    row_labels_colors: Sequence[VectorLike | None] | None,
    col_labels_colors: Sequence[VectorLike | None] | None,
) -> None:
    table_count = len(cell_texts)
    if table_count == 0:
        raise ValueError("cell_texts must contain at least one table.")
    inputs = {
        "row_labels": row_labels,
        "col_labels": col_labels,
        "cell_colors": cell_colors,
        "row_labels_colors": row_labels_colors,
        "col_labels_colors": col_labels_colors,
    }
    for name, values in inputs.items():
        if values is not None and len(values) != table_count:
            raise ValueError(
                f"{name} contains {len(values)} entries; expected {table_count}."
            )

    for index, cell_values in enumerate(cell_texts):
        cells = np.asarray(cell_values, dtype=object)
        if cells.ndim != 2:
            raise ValueError(f"cell_texts[{index}] must be two-dimensional.")
        if len(row_labels[index]) != cells.shape[0]:
            raise ValueError(
                f"row_labels[{index}] has {len(row_labels[index])} labels; "
                f"expected {cells.shape[0]}."
            )
        if len(col_labels[index]) != cells.shape[1]:
            raise ValueError(
                f"col_labels[{index}] has {len(col_labels[index])} labels; "
                f"expected {cells.shape[1]}."
            )
        if cell_colors is not None and cell_colors[index] is not None:
            colors = cell_colors[index]
            assert colors is not None
            if len(colors) != cells.shape[0] or any(
                len(row) != cells.shape[1] for row in colors
            ):
                raise ValueError(
                    f"cell_colors[{index}] must match its cell_texts shape."
                )
        if row_labels_colors is not None and row_labels_colors[index] is not None:
            label_colors = row_labels_colors[index]
            assert label_colors is not None
            if len(label_colors) != cells.shape[0]:
                raise ValueError(
                    f"row_labels_colors[{index}] must match its row count."
                )
        if col_labels_colors is not None and col_labels_colors[index] is not None:
            header_colors = col_labels_colors[index]
            assert header_colors is not None
            if len(header_colors) != cells.shape[1]:
                raise ValueError(
                    f"col_labels_colors[{index}] must match its column count."
                )


def _make_table_trace(
    cell_text: MatrixLike,
    row_labels: VectorLike,
    col_labels: VectorLike,
    cell_colors: MatrixLike | None,
    row_labels_colors: VectorLike | None,
    col_labels_colors: VectorLike | None,
    col_labels_fontweight: Literal["normal", "bold"],
) -> go.Table:
    cells = np.asarray(cell_text, dtype=object)
    columns_data = [list(row_labels)] + [
        cells[:, column].tolist() for column in range(cells.shape[1])
    ]

    if cell_colors is None:
        color_columns: str | list[list[Any]] = "white"
    else:
        color_columns = [["white"] * cells.shape[0]] + [
            [_plotly_color(cell_colors[row][column]) for row in range(cells.shape[0])]
            for column in range(cells.shape[1])
        ]

    headers = [""] + list(col_labels)
    formatted_headers = [str(header) for header in headers]
    header_font_colors: str | list[Any]
    if col_labels_colors is None:
        header_font_colors = "black"
    else:
        header_font_colors = ["black"] + [
            _plotly_color(color) for color in col_labels_colors
        ]

    cell_font_colors: str | list[list[Any]]
    if row_labels_colors is None:
        cell_font_colors = "black"
    else:
        cell_font_colors = [
            [_plotly_color(color) for color in row_labels_colors],
            *[["black"] * cells.shape[0] for _ in range(cells.shape[1])],
        ]

    return go.Table(
        header={
            "values": formatted_headers,
            "align": "center",
            "font": {
                "size": 14,
                "color": header_font_colors,
                "weight": 700 if col_labels_fontweight == "bold" else 400,
            },
            "fill_color": "rgb(240, 240, 240)",
        },
        cells={
            "values": columns_data,
            "align": "center",
            "font": {"size": 12, "color": cell_font_colors},
            "fill_color": color_columns,
            "height": 30,
        },
    )


def plot_table(
    cell_texts: Sequence[MatrixLike],
    row_labels: Sequence[VectorLike],
    col_labels: Sequence[VectorLike],
    cell_colors: Sequence[MatrixLike | None] | None = None,
    row_labels_colors: Sequence[VectorLike | None] | None = None,
    col_labels_colors: Sequence[VectorLike | None] | None = None,
    col_labels_fontweight: Literal["normal", "bold"] = "bold",
    nrows: int | None = None,
    ncols: int | None = None,
    figsize: FigureSize = DEFAULT_CONFIG.table_figsize,
    template: str | None = None,
) -> go.Figure:
    """Plot one or more tables in a flexibly sized Plotly subplot grid."""
    _validate_table_inputs(
        cell_texts,
        row_labels,
        col_labels,
        cell_colors,
        row_labels_colors,
        col_labels_colors,
    )
    nrows, ncols = _resolve_grid(len(cell_texts), nrows, ncols)
    fig = make_subplots(
        rows=nrows,
        cols=ncols,
        specs=[[{"type": "table"} for _ in range(ncols)] for _ in range(nrows)],
        horizontal_spacing=DEFAULT_CONFIG.horizontal_spacing,
        vertical_spacing=DEFAULT_CONFIG.vertical_spacing,
    )

    for index, cell_text in enumerate(cell_texts):
        table = _make_table_trace(
            cell_text,
            row_labels[index],
            col_labels[index],
            None if cell_colors is None else cell_colors[index],
            None if row_labels_colors is None else row_labels_colors[index],
            None if col_labels_colors is None else col_labels_colors[index],
            col_labels_fontweight,
        )
        fig.add_trace(table, row=index // ncols + 1, col=index % ncols + 1)

    fig.update_layout(
        width=figsize[0],
        height=figsize[1],
        template=template,
        font={"family": DEFAULT_CONFIG.font_family},
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
    )
    return fig


__all__ = ["MatrixLike", "VectorLike", "plot_table"]
