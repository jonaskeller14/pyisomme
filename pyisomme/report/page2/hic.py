from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast

import numpy as np
import plotly.graph_objects as go
from matplotlib.colors import to_rgb

from pyisomme.isomme import Isomme
from pyisomme.plotting2 import DEFAULT_CONFIG, plot_line_table
from pyisomme.report.base_report import BaseReport
from pyisomme.report.page2.figure import FigurePage

if TYPE_CHECKING:
    from pyisomme.report.criterion import Criterion

R = TypeVar("R", bound=BaseReport)
S_contra = TypeVar("S_contra", contravariant=True)
PositionSelector = Callable[[S_contra, Isomme], str]
CriterionSelector = Callable[[S_contra, Isomme], "Criterion"]

TRANSPARENT = (0.0, 0.0, 0.0, 0.0)


def _criterion_cell_color(criterion: Criterion) -> Any:
    if criterion.result is None or criterion.result.color is None:
        return TRANSPARENT
    color = criterion.result.color
    rgb = to_rgb(color) if isinstance(color, str) else color[:3]
    return (*rgb, 0.2)


def _position_required(_: S_contra, __: Isomme) -> str:  # pyright: ignore[reportInvalidTypeVarUse]
    raise RuntimeError("HICSpec requires a position via with_position().")


def _criterion_required(_: S_contra, __: Isomme) -> Criterion:  # pyright: ignore[reportInvalidTypeVarUse]
    raise RuntimeError("HICSpec requires a criterion via with_criterion().")


@dataclass(frozen=True)
class HICSpec(Generic[S_contra]):
    """Reusable rules for a HIC interval plot and result table."""

    name: str
    title: str
    position: PositionSelector[S_contra]
    criterion: CriterionSelector[S_contra]
    timespan: int
    footer: str | None = None

    def __post_init__(self) -> None:
        if self.timespan <= 0 or self.timespan > 99:
            raise ValueError("HIC timespan must be between 1 and 99 ms.")

    def with_position(self, position: PositionSelector[S_contra]) -> HICSpec[S_contra]:
        """Return a copy with a report-specific occupant-position selector."""
        return replace(self, position=position)

    def with_criterion(
        self, criterion: CriterionSelector[S_contra]
    ) -> HICSpec[S_contra]:
        """Return a copy with the criterion that supplies the result color."""
        return replace(self, criterion=criterion)


def hic_spec_for(
    _report: R,
    *,
    name: str,
    title: str,
    timespan: int,
    footer: str | None = None,
) -> HICSpec[R]:
    """Create a HIC spec bound to the concrete report type."""
    return HICSpec(
        name=name,
        title=title,
        position=_position_required,
        criterion=_criterion_required,
        timespan=timespan,
        footer=footer,
    )


class HICPage(FigurePage[R], Generic[R]):
    """Head-resultant plot with a configurable HIC interval and result table."""

    spec: HICSpec[R]

    def __init__(
        self,
        report: R,
        *,
        spec: HICSpec[R],
    ) -> None:
        self.spec = spec
        hic_name = f"HIC{spec.timespan}"

        def build(
            current_report: R, figsize: tuple[float | int, float | int]
        ) -> go.Figure:
            isommes: list[Isomme] = cast(Any, current_report).isomme_list
            channels: dict[Isomme, list[list[str]]] = {}
            rows: list[list[str]] = []
            cell_colors: list[list[Any]] = []
            hic_data: list[tuple[Isomme, float, float | None, float | None]] = []

            for isomme in isommes:
                occupant_position = spec.position(current_report, isomme)
                channels[isomme] = [[f"?{occupant_position}HEAD??????ACRA"]]
                hic_channel = isomme.get_channel(
                    f"?{occupant_position}HICR{spec.timespan:04d}??00RX",
                    f"?{occupant_position}HICRCG{spec.timespan:02d}??00RX",
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
                criterion = spec.criterion(current_report, isomme)
                color = _criterion_cell_color(criterion)
                cell_colors.append([color, TRANSPARENT, TRANSPARENT])

            figure = plot_line_table(
                channels=channels,
                cell_texts=[rows],
                row_labels=[[isomme.test_number for isomme in isommes]],
                row_labels_colors=[
                    [
                        DEFAULT_CONFIG.colors[index % len(DEFAULT_CONFIG.colors)]
                        for index in range(len(isommes))
                    ]
                ],
                col_labels=[[hic_name, "Start [ms]", "End [ms]"]],
                cell_colors=[cell_colors],
                nrows=1,
                ncols=2,
                sharex=False,
                sharey=False,
                limits=cast(Any, current_report).limits,
                figsize=figsize,
            )
            x_range = figure.layout.xaxis.range or (0.0, 1.0)  # pyright: ignore[reportAttributeAccessIssue]
            finite_hic = [hic for _, hic, _, _ in hic_data if np.isfinite(hic)]
            hic_max = max(finite_hic, default=1.0)
            figure.update_layout(
                yaxis2={
                    "overlaying": "y",
                    "side": "right",
                    "title": f"{hic_name} [-]",
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
                        name=f"{isomme.test_number} {hic_name}",
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
            name=spec.name,
            title=spec.title,
            figure_builder=build,
            footer=spec.footer,
        )


__all__ = [
    "CriterionSelector",
    "HICPage",
    "HICSpec",
    "PositionSelector",
    "hic_spec_for",
]
