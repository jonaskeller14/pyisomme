from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import plotly.graph_objects as go

import pyisomme.report.page2.plot_nxn as plot_nxn_module
from pyisomme import Isomme
from pyisomme.limit_set import LimitSet
from pyisomme.report.page2.plot_nxn import ChannelPlotPage, ChannelPlotSpec


def test_report_specific_limits_are_resolved_when_figure_is_built(
    monkeypatch: Any,
) -> None:
    isomme = Isomme(test_number="test")
    expected_limits = {isomme: LimitSet(name="selected")}
    report: Any = SimpleNamespace(
        isomme_list=[isomme],
        limits={isomme: LimitSet(name="report-wide")},
    )
    captured: dict[str, Any] = {}

    def capture_plot_line(*args: Any, **kwargs: Any) -> go.Figure:
        captured.update(kwargs)
        return go.Figure()

    monkeypatch.setattr(plot_nxn_module, "plot_line", capture_plot_line)
    page = ChannelPlotPage(
        report,
        spec=ChannelPlotSpec(
            name="Channels",
            title="Channels",
            channels=lambda current_report: {current_report.isomme_list[0]: [[]]},
        ).with_limits(lambda _report: expected_limits),
    )

    page.figure((800, 600))

    assert captured["limits"] is expected_limits
