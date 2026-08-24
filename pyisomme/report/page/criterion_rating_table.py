from __future__ import annotations

from pyisomme.report.criterion import Criterion
from pyisomme.report.page.criterion_table import Page_Criterion_Table


class Page_Criterion_Rating_Table(Page_Criterion_Table):
    """Criterion table showing awarded points rather than measured values."""

    @staticmethod
    def row_label(criterion: Criterion) -> str:
        return f"{criterion.name}"

    @staticmethod
    def cell_text(criterion: Criterion) -> str:
        return "n/a" if criterion.result is None else f"{criterion.result.rating:.1f}"
