from types import SimpleNamespace
from typing import Any, cast

import pandas as pd

from pyisomme import Channel, Isomme, g0
from pyisomme.report.euro_ncap.pages import OLCTrolleyPage
from pyisomme.report.page.olc import Page_OLC
from pyisomme.report.report import Report
from pyisomme.unit import Unit


def test_olc_cell_text_accepts_vehicle_channel() -> None:
    isomme = Isomme(
        channels=[
            Channel(
                code="10VEHC0OLC00VEXX",
                data=pd.DataFrame([4.5]),
                unit=Unit(g0),
            )
        ]
    )

    assert Page_OLC._olc_cell_text(isomme) == "4.50"


def test_olc_trolley_table_uses_rows_by_columns_shape() -> None:
    report = cast(
        Report[Any],
        SimpleNamespace(
            isomme_list=[Isomme(test_number="v1"), Isomme(test_number="v2")]
        ),
    )

    table = OLCTrolleyPage._table(report)

    assert table.cell_texts == [[["nan"], ["nan"]]]
    assert table.cell_colors == [[[(0.0, 0.0, 0.0, 0.0)], [(0.0, 0.0, 0.0, 0.0)]]]
