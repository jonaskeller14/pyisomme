from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any, Generic, TypeVar

import plotly.graph_objects as go

from pyisomme.isomme import Isomme
from pyisomme.plotting2 import DEFAULT_CONFIG, plot_table
from pyisomme.plotting2.plot_line import FigureSize
from pyisomme.report.criterion import Criterion
from pyisomme.report.manual import InputSpec
from pyisomme.report.page2.figure import FigurePage
from pyisomme.report.report import Report

R = TypeVar("R", bound=Report[Any])
S_contra = TypeVar("S_contra", bound=Report[Any], contravariant=True)
InputRow = tuple[str, Criterion, InputSpec]
InputSelector = Callable[[S_contra], Mapping[Isomme, Sequence[InputRow]]]

TRANSPARENT = (0.0, 0.0, 0.0, 0.0)
USER_SET_COLOR = (0.2, 0.45, 0.9, 0.18)
DERIVED_COLOR = (1.0, 0.75, 0.0, 0.18)


def _all_inputs(report: R) -> Mapping[Isomme, Sequence[InputRow]]: # pyright: ignore[reportInvalidTypeVarUse]
    return {
        isomme: list(report.overall(isomme).iter_inputs())
        for isomme in report.isomme_list
    }


def _format_value(value: Any, unit: str | None) -> str:
    suffix = f" {unit}" if unit else ""
    return f"{value!r}{suffix}"


def _input_text(criterion: Criterion, spec: InputSpec) -> str:
    value = _format_value(getattr(criterion, spec.name), spec.unit)
    if criterion.input_is_set(spec.name):
        return f"{value} (user)"
    if getattr(criterion, spec.name) != spec.default:
        return f"{value} (derived)"
    return value


def _input_color(criterion: Criterion, spec: InputSpec) -> Any:
    if criterion.input_is_set(spec.name):
        return USER_SET_COLOR
    if getattr(criterion, spec.name) != spec.default:
        return DERIVED_COLOR
    return TRANSPARENT


@dataclass(frozen=True)
class ManualInputsSpec(Generic[S_contra]):
    """Reusable rules for selecting the declared inputs shown on an input page."""

    name: str
    title: str
    inputs: InputSelector[S_contra]
    footer: str | None = None

    def with_inputs(
        self, inputs: InputSelector[S_contra]
    ) -> ManualInputsSpec[S_contra]:
        """Return a copy with a report-specific input selector."""
        return replace(self, inputs=inputs)


def manual_inputs_spec_for(
    _report: R,
    *,
    name: str = "Manual Inputs",
    title: str = "Manual Inputs",
    footer: str | None = None,
) -> ManualInputsSpec[R]:
    """Create a complete manual-input spec bound to a concrete report type."""
    return ManualInputsSpec(
        name=name,
        title=title,
        inputs=_all_inputs,
        footer=footer,
    )


def _manual_inputs_figure(
    inputs: Mapping[Isomme, Sequence[InputRow]],
    figsize: FigureSize,
) -> go.Figure:
    if not inputs:
        raise ValueError("Manual-input selector returned no tests.")

    isommes = list(inputs)
    rows = inputs[isommes[0]]
    paths = [path for path, _criterion, _spec in rows]
    for isomme in isommes[1:]:
        if [path for path, _criterion, _spec in inputs[isomme]] != paths:
            raise ValueError("Manual-input selector returned inconsistent input paths.")

    if rows:
        row_labels = [spec.name for _path, _criterion, spec in rows]
        cell_text = [
            [
                _format_value(spec.default, spec.unit),
                spec.source or "",
                *[
                    _input_text(inputs[isomme][index][1], inputs[isomme][index][2])
                    for isomme in isommes
                ],
            ]
            for index, (_path, _criterion, spec) in enumerate(rows)
        ]
        cell_colors = [
            [
                TRANSPARENT,
                TRANSPARENT,
                *[
                    _input_color(inputs[isomme][index][1], inputs[isomme][index][2])
                    for isomme in isommes
                ],
            ]
            for index in range(len(rows))
        ]
    else:
        row_labels = ["No manual inputs declared"]
        cell_text = [["", "", *([""] * len(isommes))]]
        cell_colors = [[TRANSPARENT] * (2 + len(isommes))]
    column_labels = [
        "Default",
        "Source",
        *[str(isomme.test_number) for isomme in isommes],
    ]
    column_colors = [
        "black",
        "black",
        *[
            DEFAULT_CONFIG.colors[index % len(DEFAULT_CONFIG.colors)]
            for index in range(len(isommes))
        ],
    ]
    figure = plot_table(
        cell_texts=[cell_text],
        cell_colors=[cell_colors],
        row_labels=[row_labels],
        col_labels=[column_labels],
        col_labels_colors=[column_colors],
        figsize=figsize,
    )
    table = figure.data[0]
    if isinstance(table, go.Table):
        table.columnwidth = [2.5, 1, 1.2, *([1.5] * len(isommes))]
    return figure


class ManualInputsPage(FigurePage[R], Generic[R]):
    """Declared input values and provenance, aligned across a report's tests."""

    spec: ManualInputsSpec[R]

    def __init__(self, report: R, *, spec: ManualInputsSpec[R]) -> None:
        self.spec = spec
        super().__init__(
            report,
            name=spec.name,
            title=spec.title,
            figure_builder=lambda current_report, figsize: _manual_inputs_figure(
                spec.inputs(current_report), figsize
            ),
            footer=spec.footer,
        )


__all__ = [
    "ManualInputsPage",
    "ManualInputsSpec",
    "manual_inputs_spec_for",
]
