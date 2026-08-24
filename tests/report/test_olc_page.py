import pandas as pd

from pyisomme import Channel, Isomme, g0
from pyisomme.report.page.olc import Page_OLC
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
