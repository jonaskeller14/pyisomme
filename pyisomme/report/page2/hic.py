from __future__ import annotations

from collections.abc import Callable
from typing import Any, Generic, TypeVar, cast

import numpy as np
import plotly.graph_objects as go

from pyisomme.isomme import Isomme
from pyisomme.plotting2 import DEFAULT_CONFIG, plot_line_table
from pyisomme.report.base_report import BaseReport
from pyisomme.report.page2.figure import FigurePage

R = TypeVar("R", bound=BaseReport)
PositionSelector = Callable[[R, Isomme], str]


class HIC15Page(FigurePage[R], Generic[R]):
    """Head-resultant plot with HIC15 interval overlay and result table."""

    def __init__(
        self,
        report: R,
        *,
        name: str,
        title: str,
        position: PositionSelector[R],
        footer: str | None = None,
    ) -> None:
        def build(
            current_report: R, figsize: tuple[float | int, float | int]
        ) -> go.Figure:
            isommes: list[Isomme] = cast(Any, current_report).isomme_list
            channels: dict[Isomme, list[list[str]]] = {}
            rows: list[list[str]] = []
            hic_data: list[tuple[Isomme, float, float | None, float | None]] = []

            for isomme in isommes:
                occupant_position = position(current_report, isomme)
                channels[isomme] = [[f"?{occupant_position}HEAD??????ACRA"]]
                hic_channel = isomme.get_channel(
                    f"?{occupant_position}HICR0015??00RX",
                    f"?{occupant_position}HICRCG15??00RX",
                )
                if hic_channel is None or len(hic_channel.data) == 0:
                    hic, start_ms, end_ms = np.nan, None, None
                else:
                    hic = float(hic_channel.get_data()[0])
                    times: list[float | None] = []
                    for label in (".Start time", ".End time"):
                        try:
                            value = float(str(hic_channel.get_info(label))) * 1000
                        except (TypeError, ValueError):
                            value = np.nan
                        times.append(value if np.isfinite(value) else None)
                    start_ms, end_ms = times
                hic_data.append((isomme, hic, start_ms, end_ms))
                rows.append(
                    [
                        f"{hic:.1f}" if np.isfinite(hic) else "n/a",
                        f"{start_ms:.2f}" if start_ms is not None else "n/a",
                        f"{end_ms:.2f}" if end_ms is not None else "n/a",
                    ]
                )

            figure = plot_line_table(
                channels=channels,
                cell_texts=[rows],
                row_labels=[[isomme.test_number for isomme in isommes]],
                col_labels=[["HIC15", "Start [ms]", "End [ms]"]],
                nrows=1,
                ncols=2,
                sharex=False,
                sharey=False,
                limits=cast(Any, current_report).limits,
                figsize=figsize,
            )
            x_range = figure.layout.xaxis.range or (0.0, 1.0)
            finite_hic = [hic for _, hic, _, _ in hic_data if np.isfinite(hic)]
            hic_max = max(finite_hic, default=1.0)
            figure.update_layout(
                yaxis2={
                    "overlaying": "y",
                    "side": "right",
                    "title": "HIC15 [-]",
                    "range": (0, max(1.0, hic_max * 1.1)),
                    "showgrid": False,
                }
            )
            for index, (isomme, hic, start_ms, end_ms) in enumerate(hic_data):
                if not np.isfinite(hic) or start_ms is None or end_ms is None:
                    continue
                figure.add_trace(
                    go.Scatter(
                        x=[
                            x_range[0],
                            start_ms,
                            start_ms,
                            end_ms,
                            end_ms,
                            x_range[1],
                        ],
                        y=[0, 0, hic, hic, 0, 0],
                        mode="lines",
                        name=f"{isomme.test_number} HIC15",
                        line={
                            "color": DEFAULT_CONFIG.colors[
                                index % len(DEFAULT_CONFIG.colors)
                            ],
                            "dash": "dash",
                            "width": 1.5,
                        },
                        yaxis="y2",
                    )
                )
            return figure

        super().__init__(
            report,
            name=name,
            title=title,
            figure_builder=build,
            footer=footer,
        )


__all__ = ["HIC15Page", "PositionSelector"]
