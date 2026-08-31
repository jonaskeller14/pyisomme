from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import pytest

from pyisomme.channel import create_sample
from pyisomme.isomme import Isomme
from pyisomme.limit import Limit
from pyisomme.limit_set import LimitSet
from pyisomme.plotting2 import plot_line, plot_line_table, plot_table


def _sample_isomme(test_number: str = "TEST") -> Isomme:
    channel = create_sample(
        code="11HEAD0000H3ACXA",
        t_range=(0.0, 0.1, 11),
        y_range=(0.0, 10.0),
        mode="linear",
        unit="m/s^2",
    )
    return Isomme(test_number=test_number, channels=[channel])


def test_plot_line_resolves_channel_codes_without_mutating_channels() -> None:
    isomme = _sample_isomme()
    channel = isomme.channels[0]
    original_unit = channel.unit

    fig = plot_line(
        {isomme: [[str(channel.code)], [channel]]},
        xlim=(0.0, 100.0),
        sharex=True,
    )

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2
    assert list(fig.data[0].x) == pytest.approx(np.linspace(0.0, 100.0, 11))
    assert fig.layout.xaxis.range == fig.layout.xaxis2.range
    assert channel.unit == original_unit


def test_plot_line_deduplicates_repeated_labels_but_keeps_distinct_lines() -> None:
    isomme = _sample_isomme("TEST")
    second_channel = create_sample(
        code="11CHST0000H3ACXA",
        t_range=(0.0, 0.1, 11),
        y_range=(0.0, 5.0),
        mode="linear",
        unit="m/s^2",
    )
    isomme.channels.append(second_channel)
    group = [isomme.channels[0], second_channel]

    fig = plot_line(
        {isomme: [group, group, group, group]},
        nrows=2,
        ncols=2,
    )

    legend_traces = [trace for trace in fig.data if trace.showlegend]
    assert [trace.name for trace in legend_traces] == [
        f"TEST {isomme.channels[0].code}",
        f"TEST {second_channel.code}",
    ]
    legend_groups = {trace.legendgroup for trace in fig.data}
    assert len(legend_groups) == 2
    assert all(
        sum(trace.legendgroup == legend_group for trace in fig.data) == 4
        for legend_group in legend_groups
    )


def test_plot_line_keeps_all_requested_subplots_when_channels_are_missing() -> None:
    isomme = Isomme(test_number="EMPTY")

    fig = plot_line(
        {isomme: [["11HEAD0000H3ACXA"]] * 4},
        nrows=2,
        ncols=2,
    )

    assert [trace.xaxis for trace in fig.data] == ["x", "x2", "x3", "x4"]
    assert all(trace.showlegend is False for trace in fig.data)
    assert all(trace.marker.opacity == 0 for trace in fig.data)


def test_plot_line_shares_y_axis_across_entire_grid() -> None:
    isomme = _sample_isomme()

    fig = plot_line(
        {isomme: [[isomme.channels[0]]] * 4},
        nrows=2,
        ncols=2,
        sharey=True,
    )

    matches = [
        fig.layout.yaxis.matches, # pyright: ignore[reportAttributeAccessIssue]
        fig.layout.yaxis2.matches,
        fig.layout.yaxis3.matches,
        fig.layout.yaxis4.matches,
    ]
    assert matches.count(None) == 1
    assert len({match for match in matches if match is not None}) == 1


def test_plot_line_adds_limit_lines_fills_and_labels() -> None:
    isomme = _sample_isomme()
    limits = LimitSet(
        limits=(
            Limit(
                ("11HEAD*",),
                lambda _x: 4.0,
                color="green",
                name="acceptable",
                upper=True,
                x_unit="ms",
                y_unit="m/s^2",
            ),
            Limit(
                ("11HEAD*",),
                lambda _x: 8.0,
                color="red",
                name="poor",
                lower=True,
                x_unit="ms",
                y_unit="m/s^2",
            ),
        )
    )

    fig = plot_line(
        {isomme: [[isomme.channels[0]]]}, limits=limits, xlim=(0.0, 100.0)
    )

    assert sum(trace.fill == "toself" for trace in fig.data) == 2
    assert {annotation.text for annotation in fig.layout.annotations} >= {
        "acceptable",
        "poor",
    }
    limit_annotations = [
        annotation
        for annotation in fig.layout.annotations
        if annotation.text in {"acceptable", "poor"}
    ]
    assert all(annotation.x == 0 for annotation in limit_annotations)
    assert all(annotation.xanchor == "left" for annotation in limit_annotations)
    assert all(annotation.xshift == 4 for annotation in limit_annotations)


def test_plot_table_infers_grid_and_validates_shapes() -> None:
    fig = plot_table(
        cell_texts=[[[1]], [[2]]],
        row_labels=[["row 1"], ["row 2"]],
        col_labels=[["value"], ["value"]],
        cell_colors=[[[(1.0, 0.0, 0.0, 0.5)]], None],
        col_labels_colors=[["darkblue"], None],
    )

    assert len(fig.data) == 2
    assert all(isinstance(trace, go.Table) for trace in fig.data)
    assert fig.data[0].cells.fill.color[1][0] == "rgba(255,0,0,0.5)"
    assert list(fig.data[0].header.values) == ["", "value"]
    assert list(fig.data[0].header.font.color) == ["black", "darkblue"]
    assert fig.data[0].header.font.weight == 700
    with pytest.raises(ValueError, match="row_labels"):
        plot_table([[[1], [2]]], [["only one"]], [["value"]])


def test_plot_line_table_combines_cartesian_and_table_traces() -> None:
    isomme = _sample_isomme()

    fig = plot_line_table(
        channels={isomme: [[isomme.channels[0]]]},
        cell_texts=[[["ok"]]],
        row_labels=[["result"]],
        col_labels=[["rating"]],
        nrows=1,
        ncols=2,
    )

    assert len(fig.data) == 2
    assert isinstance(fig.data[0], go.Scatter)
    assert isinstance(fig.data[1], go.Table)
