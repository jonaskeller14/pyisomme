from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import plotly.graph_objects as go

import pyisomme.report.page2.hic as hic_module
from pyisomme import Isomme
from pyisomme.plotting2 import DEFAULT_CONFIG
from pyisomme.report.page2.hic import HICPage, HICSpec
from tests.report.report_factory import build_head_acceleration_channels

TRANSPARENT = (0.0, 0.0, 0.0, 0.0)


def test_report_factory_head_channels_derive_hic() -> None:
    isomme = Isomme(
        test_number="test",
        channels=build_head_acceleration_channels(),
    )

    assert {channel.code.direction for channel in isomme.channels} == {"X", "Y", "Z"}
    assert all(channel.code.main_location == "HEAD" for channel in isomme.channels)
    assert isomme.get_channel("?1HICR0015??00RX") is not None


class StubIsomme:
    def __init__(self, test_number: str) -> None:
        self.test_number = test_number

    def get_channel(self, *_patterns: str) -> None:
        return None


def test_hic_value_cell_uses_criterion_result_color(monkeypatch: Any) -> None:
    isomme = StubIsomme("test-1")
    criterion = SimpleNamespace(result=SimpleNamespace(color="red"))
    report = SimpleNamespace(isomme_list=[isomme], limits={})
    captured: dict[str, Any] = {}

    def capture_plot_line_table(**kwargs: Any) -> go.Figure:
        captured.update(kwargs)
        return go.Figure()

    monkeypatch.setattr(hic_module, "plot_line_table", capture_plot_line_table)
    page = HICPage(
        report,
        spec=HICSpec(
            name="HIC",
            title="HIC",
            position=lambda _report, _isomme: "01",
            criterion=lambda _report, _isomme: criterion,
            timespan=15,
        ),
    )

    page.figure((800, 600))

    assert captured["cell_colors"] == [
        [[(1.0, 0.0, 0.0, 0.2), TRANSPARENT, TRANSPARENT]],
    ]
    assert captured["row_labels_colors"] == [[DEFAULT_CONFIG.colors[0]]]
