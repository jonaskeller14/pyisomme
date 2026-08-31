from __future__ import annotations

from typing import TypeVar

import numpy as np

from pyisomme.isomme import Isomme
from pyisomme.report.base_report import BaseReport
from pyisomme.report.criterion import Criterion
from pyisomme.report.page2.criterion_rating_table import (
    CriterionTablePage,
    CriterionTableSpec,
    _criteria_required,
    _rating_cell_color,
)

R = TypeVar("R", bound=BaseReport)


def _value_row_label(criterion: Criterion) -> str:
    unit = (
        criterion.result.channel.unit
        if criterion.result is not None and criterion.result.channel is not None
        else np.nan
    )
    return f"{criterion.name} [{unit}]"


def _value_cell_text(criterion: Criterion) -> str:
    return "n/a" if criterion.result is None else f"{criterion.result.value:.4g}"


def values_table_spec_for(_report: R) -> CriterionTableSpec[R]:
    """Create a measured-value table spec for a report's criterion selector."""
    return CriterionTableSpec(
        criteria=_criteria_required,
        row_label=_value_row_label,
        cell_text=_value_cell_text,
        cell_color=_rating_cell_color,
    )


class CriterionValuesTablePage(CriterionTablePage):
    """Inheritable measured-value table for report-local page definitions."""

    criteria: dict[Isomme, list[Criterion]]
    name: str
    title: str
    footer: str | None = None

    def __init__(self, report: BaseReport) -> None:
        super().__init__(
            report,
            name=self.name,
            title=self.title,
            spec=values_table_spec_for(report).with_criteria(
                lambda _report: self.criteria
            ),
            footer=self.footer,
        )

__all__ = [
    "CriterionValuesTablePage",
    "values_table_spec_for",
]
