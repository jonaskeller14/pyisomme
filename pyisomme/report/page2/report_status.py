from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any, Generic, TypeVar

import plotly.graph_objects as go

from pyisomme.errors import Status
from pyisomme.isomme import Isomme
from pyisomme.plotting2 import DEFAULT_CONFIG, plot_table
from pyisomme.plotting2.plot_line import FigureSize
from pyisomme.report.criterion import Criterion
from pyisomme.report.page2.figure import FigurePage
from pyisomme.report.report import Report

R = TypeVar("R", bound=Report[Any])
S_contra = TypeVar("S_contra", bound=Report[Any], contravariant=True)
StatusRow = tuple[str, Criterion]
StatusSelector = Callable[[S_contra], Mapping[Isomme, Sequence[StatusRow]]]

STATUS_COLORS: dict[Status, tuple[float, float, float, float]] = {
    Status.OK: (0.2, 0.7, 0.3, 0.2),
    Status.NA: (0.5, 0.5, 0.5, 0.2),
    Status.ERROR: (0.9, 0.2, 0.2, 0.25),
    Status.PENDING: (1.0, 0.75, 0.0, 0.2),
}


def _status_text(criterion: Criterion) -> str:
    if criterion.status is Status.NA and criterion.na_reason is not None:
        return f"N/A: {criterion.na_reason}"
    return "N/A" if criterion.status is Status.NA else criterion.status.name


def _row_label(path: str, criterion: Criterion) -> str:
    name = criterion.name or type(criterion).__name__
    depth = path.count("/") + 1 if path else 0
    indentation = "\u00a0\u00a0" * depth
    return f"{indentation}{name}"


def _all_criteria(report: R) -> Mapping[Isomme, Sequence[StatusRow]]:
    return {
        isomme: list(report.overall(isomme).walk()) for isomme in report.isomme_list
    }


@dataclass(frozen=True)
class ReportStatusSpec(Generic[S_contra]):
    """Reusable rules for selecting the criterion tree shown on a status page."""

    name: str
    title: str
    criteria: StatusSelector[S_contra]
    footer: str | None = None

    def with_criteria(
        self, criteria: StatusSelector[S_contra]
    ) -> ReportStatusSpec[S_contra]:
        """Return a copy with a report-specific criterion selector."""
        return replace(self, criteria=criteria)


def report_status_spec_for(
    _report: R,
    *,
    name: str = "Report Status",
    title: str = "Report Status",
    footer: str | None = None,
) -> ReportStatusSpec[R]:
    """Create a complete criterion-status spec bound to a concrete report type."""
    return ReportStatusSpec(
        name=name,
        title=title,
        criteria=_all_criteria,
        footer=footer,
    )


def _status_figure(
    criteria: Mapping[Isomme, Sequence[StatusRow]],
    figsize: FigureSize,
) -> go.Figure:
    if not criteria:
        raise ValueError("Report status selector returned no tests.")

    isommes = list(criteria)
    rows = criteria[isommes[0]]
    paths = [path for path, _criterion in rows]
    for isomme in isommes[1:]:
        if [path for path, _criterion in criteria[isomme]] != paths:
            raise ValueError(
                "Report status selector returned inconsistent criterion paths."
            )

    cell_text = [
        [_status_text(criteria[isomme][index][1]) for isomme in isommes]
        for index in range(len(rows))
    ]
    cell_colors = [
        [STATUS_COLORS[criteria[isomme][index][1].status] for isomme in isommes]
        for index in range(len(rows))
    ]
    figure = plot_table(
        cell_texts=[cell_text],
        cell_colors=[cell_colors],
        row_labels=[[_row_label(path, criterion) for path, criterion in rows]],
        col_labels=[[str(isomme.test_number) for isomme in isommes]],
        col_labels_colors=[
            [
                DEFAULT_CONFIG.colors[index % len(DEFAULT_CONFIG.colors)]
                for index in range(len(isommes))
            ]
        ],
        figsize=figsize,
    )
    table = figure.data[0]
    if isinstance(table, go.Table):
        table.columnwidth = [3, *([1] * len(isommes))]
    return figure


class ReportStatusPage(FigurePage[R], Generic[R]):
    """Status of every selected criterion, aligned across a report's tests."""

    spec: ReportStatusSpec[R]

    def __init__(self, report: R, *, spec: ReportStatusSpec[R]) -> None:
        self.spec = spec
        super().__init__(
            report,
            name=spec.name,
            title=spec.title,
            figure_builder=lambda current_report, figsize: _status_figure(
                spec.criteria(current_report), figsize
            ),
            footer=spec.footer,
        )


__all__ = [
    "ReportStatusPage",
    "ReportStatusSpec",
    "report_status_spec_for",
]
