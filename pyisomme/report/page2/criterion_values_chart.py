from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Generic, TypeVar

import numpy as np
import plotly.graph_objects as go

from pyisomme.limit_set import limit_list_sort
from pyisomme.plotting2 import DEFAULT_CONFIG
from pyisomme.report.base_report import BaseReport
from pyisomme.report.page2.figure import FigurePage

if TYPE_CHECKING:
    from pyisomme.isomme import Isomme
    from pyisomme.report.criterion import Criterion


R = TypeVar("R", bound=BaseReport)
S_contra = TypeVar("S_contra", contravariant=True)
CriteriaSelector = Callable[[S_contra], Mapping["Isomme", Sequence["Criterion"]]]


def _criteria_required(
    _: S_contra, # pyright: ignore[reportInvalidTypeVarUse]
) -> Mapping[Isomme, Sequence[Criterion]]:
    raise RuntimeError(
        "CriterionValuesChartSpec requires criteria via with_criteria()."
    )


@dataclass(frozen=True)
class CriterionValuesChartSpec(Generic[S_contra]):
    """Reusable rules for selecting criteria for a values chart."""

    name: str
    title: str
    criteria: CriteriaSelector[S_contra]
    footer: str | None = None

    def with_criteria(
        self, criteria: CriteriaSelector[S_contra]
    ) -> CriterionValuesChartSpec[S_contra]:
        """Return a copy with a report-specific criteria selector."""
        return replace(self, criteria=criteria)


def criterion_values_chart_spec_for(
    _report: R,
    *,
    name: str,
    title: str,
    footer: str | None = None,
) -> CriterionValuesChartSpec[R]:
    """Create a values-chart spec bound to the concrete report type."""
    return CriterionValuesChartSpec(
        name=name,
        title=title,
        criteria=_criteria_required,
        footer=footer,
    )


def limit_x(criterion: Criterion) -> float:
    """Return the x coordinate at which a criterion's limits are evaluated."""
    if criterion.result is None or criterion.result.channel is None:
        return 0.0
    return criterion.limits.get_limit_min_x(criterion.result.channel)


def _same_limits(left: Criterion, right: Criterion) -> bool:
    left_x = limit_x(left)
    right_x = limit_x(right)
    left_limits = limit_list_sort(list(left.limits.limits), x=left_x, x_unit="s")
    right_limits = limit_list_sort(list(right.limits.limits), x=right_x, x_unit="s")
    if len(left_limits) != len(right_limits):
        return False
    return all(
        np.isclose(
            left_limit.func(left_x),
            right_limit.func(right_x),
            rtol=1e-6,
            atol=1e-12,
            equal_nan=True,
        )
        for left_limit, right_limit in zip(left_limits, right_limits)
    )


def _chart_figure(
    criteria: Mapping[Isomme, Sequence[Criterion]],
    figsize: tuple[float | int, float | int],
) -> go.Figure:
    if not criteria:
        raise ValueError("Criterion chart selector returned no tests.")
    isommes = list(criteria)
    rows = criteria[isommes[0]]
    if not rows:
        raise ValueError("Criterion chart selector returned no criteria.")
    if any(len(criteria[isomme]) != len(rows) for isomme in isommes):
        raise ValueError("Criterion chart selector returned ragged criterion rows.")

    values = np.asarray(
        [
            [
                abs(criterion.result.value) if criterion.result is not None else np.nan
                for criterion in criteria[isomme]
            ]
            for isomme in isommes
        ],
        dtype=float,
    )
    factors = np.nanmax(1.1 * np.abs(values), axis=0)
    factors[~np.isfinite(factors) | (factors == 0)] = 1.0

    unique_limits = np.asarray(
        [
            any(
                not _same_limits(row, criteria[isomme][index]) for isomme in isommes[1:]
            )
            for index, row in enumerate(rows)
        ],
        dtype=bool,
    )
    bar_width = 0.8 / len(isommes)
    offsets = np.linspace(
        -0.4 + bar_width / 2,
        0.4 - bar_width / 2,
        len(isommes),
    )
    figure = go.Figure()
    legend_limits: set[str] = set()

    for isomme_index, isomme in enumerate(isommes):
        for criterion_index, criterion in enumerate(criteria[isomme]):
            if not criterion.limits.limits:
                continue
            evaluated_x = limit_x(criterion)
            limits = limit_list_sort(
                list(criterion.limits.limits),
                x=evaluated_x,
                x_unit="s",
                sym=True,
            )
            finite_limit_values = [
                abs(float(limit.func(evaluated_x)))
                for limit in limits
                if np.isfinite(abs(float(limit.func(evaluated_x))))
            ]
            if finite_limit_values:
                factors[criterion_index] = max(
                    factors[criterion_index], 1.1 * max(finite_limit_values)
                )
            limit_values = [
                abs(float(limit.func(evaluated_x)))
                if np.isfinite(abs(float(limit.func(evaluated_x))))
                else factors[criterion_index]
                for limit in limits
            ]
            x_center = criterion_index + offsets[isomme_index]
            for limit_index, (limit, limit_value) in enumerate(
                zip(limits, limit_values)
            ):
                if limit_index == 0:
                    bottom, top = 0.0, limit_value
                elif limit_index == len(limits) - 1:
                    bottom, top = limit_value, factors[criterion_index]
                elif (limit.lower and limit.func(0) >= 0) or (
                    limit.upper and limit.func(0) < 0
                ):
                    bottom, top = limit_value, limit_values[limit_index + 1]
                elif (limit.upper and limit.func(0) >= 0) or (
                    limit.lower and limit.func(0) < 0
                ):
                    bottom, top = limit_values[limit_index - 1], limit_value
                else:
                    continue
                name = limit.name or ""
                showlegend = bool(name and name not in legend_limits)
                if showlegend:
                    legend_limits.add(name)
                figure.add_shape(
                    type="rect",
                    x0=x_center - bar_width / 2,
                    x1=x_center + bar_width / 2,
                    y0=bottom / factors[criterion_index],
                    y1=top / factors[criterion_index],
                    fillcolor=limit.color,
                    opacity=0.5,
                    layer="below",
                    line={"width": 0},
                    name=name or None,
                    showlegend=showlegend,
                )

    for isomme_index, isomme in enumerate(isommes):
        x = np.arange(len(rows), dtype=float)
        x = x + unique_limits * offsets[isomme_index]
        figure.add_trace(
            go.Scatter(
                x=x,
                y=values[isomme_index] / factors,
                mode="lines+markers",
                name=isomme.test_number,
                line={
                    "color": DEFAULT_CONFIG.colors[
                        isomme_index % len(DEFAULT_CONFIG.colors)
                    ],
                    "width": 3,
                },
                marker={"size": 9},
                customdata=values[isomme_index],
                hovertemplate="%{x}<br>%{customdata:.4g}<extra>%{fullData.name}</extra>",
            )
        )

    figure.update_xaxes(
        tickmode="array",
        tickvals=list(range(len(rows))),
        ticktext=[criterion.name for criterion in rows],
        tickangle=-30,
    )
    figure.update_yaxes(visible=False, range=(0, 1))
    figure.update_layout(
        width=figsize[0],
        height=figsize[1],
        font={"family": DEFAULT_CONFIG.font_family},
        margin={"l": 30, "r": 30, "t": 30, "b": 150},
        legend={"x": 1.01, "y": 1, "xanchor": "left", "yanchor": "top"},
    )
    return figure


class CriterionValuesChartPage(FigurePage[R], Generic[R]):
    spec: CriterionValuesChartSpec[R]

    def __init__(
        self,
        report: R,
        *,
        spec: CriterionValuesChartSpec[R],
    ) -> None:
        self.spec = spec
        super().__init__(
            report,
            name=spec.name,
            title=spec.title,
            figure_builder=lambda current_report, figsize: _chart_figure(
                spec.criteria(current_report), figsize
            ),
            footer=spec.footer,
        )


__all__ = [
    "CriterionValuesChartPage",
    "CriterionValuesChartSpec",
    "criterion_values_chart_spec_for",
    "limit_x",
]
