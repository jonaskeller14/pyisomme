from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable
from typing_extensions import override
from matplotlib.colors import to_rgb
from matplotlib.figure import Figure

from pyisomme.isomme import Isomme
from pyisomme.plotting import Plot, Plot_Table
from pyisomme.report.criterion import Criterion
from pyisomme.report.page.figure import Page_Figure

if TYPE_CHECKING:
    from pyisomme.report.report import Report


TRANSPARENT = (0.0, 0.0, 0.0, 0.0)


class Page_Criterion_Table(Page_Figure):
    """One row per criterion, one column per test, cells tinted by criterion colour."""

    criteria: dict[Isomme, list[Criterion]]
    row_label: Callable[[Any], str]
    cell_text: Callable[[Any], str]

    def __init__(self, report: Report[Any]) -> None:
        super().__init__(report)
        self.criteria = {}

    @override
    def figure(self, figsize: tuple[float, float]) -> Figure:
        isomme_list = list(self.criteria)
        rows = self.criteria[isomme_list[0]]

        cell_text = [
            [self.cell_text(self.criteria[isomme][idx]) for isomme in isomme_list]
            for idx in range(len(rows))
        ]
        cell_colors = [
            [
                (*to_rgb(criterion.color), 0.5)
                if criterion.color is not None
                else TRANSPARENT
                for criterion in (self.criteria[isomme][idx] for isomme in isomme_list)
            ]
            for idx in range(len(rows))
        ]

        row_labels = [self.row_label(criterion) for criterion in rows]
        col_labels = [isomme.test_number for isomme in isomme_list]
        col_colors = list(Plot.colors)[: len(isomme_list)]

        return Plot_Table(
            cell_texts=[cell_text],
            cell_colors=[cell_colors],
            row_labels=[row_labels],
            col_labels=[col_labels],
            col_labels_colors=[col_colors],
            col_labels_fontweight="bold",
            nrows=1,
            ncols=1,
            figsize=figsize,
        ).fig
