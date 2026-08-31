from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Generic, TypeVar

import plotly.graph_objects as go
from matplotlib.colors import to_rgb

from pyisomme.plotting2 import DEFAULT_CONFIG, plot_table
from pyisomme.plotting2.plot_line import FigureSize
from pyisomme.report.base_report import BaseReport
from pyisomme.report.page2.figure import FigurePage

if TYPE_CHECKING:
    from pyisomme.isomme import Isomme
    from pyisomme.report.criterion import Criterion


R = TypeVar("R", bound=BaseReport)
CriteriaSelector = Callable[[R], Mapping["Isomme", Sequence["Criterion"]]]
CriterionFormatter = Callable[["Criterion"], str]
CriterionColor = Callable[["Criterion"], Any]

TRANSPARENT = (0.0, 0.0, 0.0, 0.0)


def _rating_row_label(criterion: Criterion) -> str:
    return f"{criterion.name}"


def _rating_cell_text(criterion: Criterion) -> str:
    return "n/a" if criterion.result is None else f"{criterion.result.rating:.1f}"


def _rating_cell_color(criterion: Criterion) -> Any:
    if criterion.result is None or criterion.result.color is None:
        return TRANSPARENT
    color = criterion.result.color
    rgb = to_rgb(color) if isinstance(color, str) else color[:3]
    return (*rgb, 0.2)


def _criteria_required(_: R) -> Mapping[Isomme, Sequence[Criterion]]:
    raise RuntimeError("CriterionTableSpec requires criteria via with_criteria().")


@dataclass(frozen=True)
class CriterionTableSpec(Generic[R]):
    """Reusable, immutable rules for turning criteria into a table."""

    criteria: CriteriaSelector[R]
    row_label: CriterionFormatter
    cell_text: CriterionFormatter
    cell_color: CriterionColor = _rating_cell_color

    def with_criteria(self, criteria: CriteriaSelector[R]) -> CriterionTableSpec[R]:
        """Return a copy for another report's criterion selection."""
        return replace(self, criteria=criteria)


def rating_table_spec_for(_report: R) -> CriterionTableSpec[R]:
    """Create a rating-table spec bound to the concrete report type."""
    return CriterionTableSpec(
        criteria=_criteria_required,
        row_label=_rating_row_label,
        cell_text=_rating_cell_text,
    )


class CriterionTablePage(FigurePage[R], Generic[R]):
    def __init__(
        self,
        report: R,
        *,
        name: str,
        title: str,
        spec: CriterionTableSpec[R],
        footer: str | None = None,
    ) -> None:
        self.spec = spec
        super().__init__(
            report,
            name=name,
            title=title,
            figure_builder=self._figure_for,
            footer=footer,
        )

    def _figure_for(self, report: R, figsize: FigureSize) -> go.Figure:
        criteria = self.spec.criteria(report)
        if not criteria:
            raise ValueError("Criterion table selector returned no tests.")

        isomme_list = list(criteria)
        rows = criteria[isomme_list[0]]
        expected_rows = len(rows)
        if any(len(criteria[isomme]) != expected_rows for isomme in isomme_list):
            raise ValueError("Criterion table selector returned ragged criterion rows.")

        cell_text = [
            [self.spec.cell_text(criteria[isomme][idx]) for isomme in isomme_list]
            for idx in range(len(rows))
        ]
        cell_colors = [
            [self.spec.cell_color(criteria[isomme][idx]) for isomme in isomme_list]
            for idx in range(len(rows))
        ]

        row_labels = [self.spec.row_label(criterion) for criterion in rows]
        col_labels = [isomme.test_number for isomme in isomme_list]
        col_colors = [
            DEFAULT_CONFIG.colors[index % len(DEFAULT_CONFIG.colors)]
            for index in range(len(isomme_list))
        ]

        return plot_table(
            cell_texts=[cell_text],
            cell_colors=[cell_colors],
            row_labels=[row_labels],
            col_labels=[col_labels],
            col_labels_colors=[col_colors],
            col_labels_fontweight="bold",
            nrows=1,
            ncols=1,
            figsize=figsize,
        )


class CriterionRatingTablePage(CriterionTablePage[R], Generic[R]):
    """Inheritable rating table for report-local named page definitions."""

    criteria: Mapping[Isomme, Sequence[Criterion]]
    name: str
    title: str
    footer: str | None = None

    def __init__(self, report: R) -> None:
        super().__init__(
            report,
            name=self.name,
            title=self.title,
            spec=rating_table_spec_for(report).with_criteria(
                lambda _report: self.criteria
            ),
            footer=self.footer,
        )


__all__ = [
    "CriterionRatingTablePage",
    "CriterionTablePage",
    "CriterionTableSpec",
    "rating_table_spec_for",
]
