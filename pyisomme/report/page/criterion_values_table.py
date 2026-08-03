from __future__ import annotations

import numpy as np

from pyisomme.report.criterion import Criterion
from pyisomme.report.page.criterion_table import Page_Criterion_Table


class Page_Criterion_Values_Table(Page_Criterion_Table):
    """Criterion table showing measured values, labelled with the channel's unit."""

    @staticmethod
    def row_label(criterion: Criterion) -> str:
        return f"{criterion.name} [{criterion.channel.unit if criterion.channel is not None else np.nan}]"

    @staticmethod
    def cell_text(criterion: Criterion) -> str:
        return f"{criterion.value:.4g}"
