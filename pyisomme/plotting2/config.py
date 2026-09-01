from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlotConfig:
    default_figsize: tuple[int, int] = (1000, 800)
    table_figsize: tuple[int, int] = (1000, 600)
    linechart_figsize: tuple[int, int] = (1000, 500)
    colors: tuple[str, ...] = (
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
    )
    line_dashes: tuple[str, ...] = (
        "solid",
        "dash",
        "dashdot",
        "dot",
        "longdash",
        "longdashdot",
    )
    font_family: str = "Arial, sans-serif"
    xaxis_nticks: int = 10
    yaxis_nticks: int = 10
    horizontal_spacing: float = 0.05
    vertical_spacing: float = 0.08


DEFAULT_CONFIG = PlotConfig()
