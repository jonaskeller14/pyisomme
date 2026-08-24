from typing import Any

from pyisomme.report import correlation, euro_ncap, fmvss, iihs, un, us_ncap
from pyisomme.report.base_report import BaseReport
from pyisomme.report.correlation import Correlation
from pyisomme.report.euro_ncap import (
    EuroNCAP,
    EuroNCAP_Frontal_50kmh,
    EuroNCAP_Frontal_MPDB,
    EuroNCAP_Side_Barrier,
    EuroNCAP_Side_FarSide,
    EuroNCAP_Side_Pole,
)
from pyisomme.report.fmvss import FMVSS_208
from pyisomme.report.iihs import (
    IIHS_Frontal_Moderate_Overlap,
    IIHS_Frontal_Small_Overlap,
    IIHS_Side_Impact,
)
from pyisomme.report.meta_report import MetaReport
from pyisomme.report.report import Report
from pyisomme.report.un import (
    UN_Frontal_50kmh_R137,
    UN_Frontal_56kmh_ODB_R94,
    UN_Side_Barrier_R95,
    UN_Side_Pole_R135,
)

REPORTS: list[type[Report[Any]]] = [
    Correlation,
    EuroNCAP_Frontal_MPDB,
    EuroNCAP_Frontal_50kmh,
    EuroNCAP_Side_Barrier,
    EuroNCAP_Side_Pole,
    EuroNCAP_Side_FarSide,
    FMVSS_208,
    IIHS_Frontal_Small_Overlap,
    IIHS_Frontal_Moderate_Overlap,
    IIHS_Side_Impact,
    UN_Frontal_50kmh_R137,
    UN_Frontal_56kmh_ODB_R94,
    UN_Side_Pole_R135,
    UN_Side_Barrier_R95,
]

META_REPORTS: list[type[MetaReport]] = [
    EuroNCAP,
]

ALL_REPORTS = REPORTS + META_REPORTS
