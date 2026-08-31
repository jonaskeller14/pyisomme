from __future__ import annotations

from typing import Any

import numpy as np

from pyisomme.isomme import Isomme
from pyisomme.report.page2.line_table import LineTablePage, TableData
from pyisomme.report.report import Report
from pyisomme.unit import Unit, g0


class OLCPage(LineTablePage[Report[Any]]):
    """Standard Occupant Load Criterion line chart and value table."""

    @staticmethod
    def cell_text(isomme: Isomme) -> str:
        channel = isomme.get_channel(
            "10VEHC0OLC??VEXX", "14BPIL0OLC??VEXX", "10SEAT0OLC??VEXX"
        )
        if channel is None:
            return f"{np.nan:.2f}"
        return f"{channel.get_data(unit=Unit(g0))[0]:.2f}"

    def __init__(self, report: Report[Any]) -> None:
        super().__init__(
            report,
            name="OLC",
            title="Occupant Load Criterion (OLC)",
            channels=lambda current_report: {
                isomme: [
                    [
                        isomme.get_channel(
                            "10VEHCCG00??VEXA",
                            "14BPIL??????VEXA",
                            "10SEATLERE??VEXA",
                        ),
                        isomme.get_channel(
                            "10VEHC0OLC??VEXA",
                            "14BPIL0OLC??VEXA",
                            "10SEAT0OLC??VEXA",
                        ),
                    ]
                ]
                for isomme in current_report.isomme_list
            },
            table=lambda current_report: TableData(
                cell_texts=[
                    [
                        [self.cell_text(isomme)]
                        for isomme in current_report.isomme_list
                    ]
                ],
                col_labels=[["OLC [g]"]],
                row_labels=[
                    [isomme.test_number for isomme in current_report.isomme_list]
                ],
            ),
            nrows=1,
            ncols=2,
        )


__all__ = ["OLCPage"]
