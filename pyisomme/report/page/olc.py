from __future__ import annotations

from typing import Any, TYPE_CHECKING

import numpy as np

from pyisomme.isomme import Isomme
from pyisomme.report.page.line_table import Page_Line_Table
from pyisomme.unit import Unit, g0

if TYPE_CHECKING:
    from pyisomme.report.report import Report


class Page_OLC(Page_Line_Table):
    name = "OLC"
    title = "Occupant Load Criterion (OLC)"
    nrows: int = 1
    ncols: int = 2

    @staticmethod
    def _olc_cell_text(isomme: Isomme) -> str:
        # NOTE: the availability check deliberately uses a *narrower* pattern set than the
        # lookup it guards — a test carrying only "10VEH0OLC??VEXX" renders as nan. Kept
        # as-is; see the progress log (deferred item D7).
        channel = isomme.get_channel(
            "10VEH0OLC??VEXX", "14BPIL0OLC??VEXX", "10SEAT0OLC??VEXX"
        )
        if (
            channel is None
            or isomme.get_channel("14BPIL0OLC??VEXX", "10SEAT0OLC??VEXX") is None
        ):
            return f"{np.nan:.2f}"
        return f"{channel.get_data(unit=Unit(g0))[0]:.2f}"

    def __init__(self, report: Report[Any]) -> None:
        super().__init__(report)

        self.channels = {
            isomme: [
                [
                    isomme.get_channel(
                        "10VEHCCG00??VEXA", "14BPIL??????VEXA", "10SEATLERE??VEXA"
                    ),
                    isomme.get_channel(
                        "10VEH0OLC??VEXA", "14BPIL0OLC??VEXA", "10SEAT0OLC??VEXA"
                    ),
                ]
            ]
            for isomme in self.report.isomme_list
        }
        self.cell_texts = [
            [[self._olc_cell_text(isomme)] for isomme in self.report.isomme_list]
        ]
        self.col_labels = [["OLC [g]"]]
        self.row_labels = [[isomme.test_number for isomme in self.report.isomme_list]]
