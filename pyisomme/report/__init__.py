from pyisomme.report import correlation, euro_ncap, fmvss, iihs, un, us_ncap
from pyisomme.report.euro_ncap import (
    EuroNCAP_Frontal_50kmh,
    EuroNCAP_Frontal_MPDB,
    EuroNCAP_Side_Barrier,
    EuroNCAP_Side_FarSide,
    EuroNCAP_Side_Pole,
)
from pyisomme.report.un import (
    UN_Frontal_50kmh_R137,
    UN_Frontal_56kmh_ODB_R94,
    UN_Side_Barrier_R95,
    UN_Side_Pole_R135,
)


REPORTS = [
    EuroNCAP_Frontal_MPDB,
    EuroNCAP_Frontal_50kmh,
    EuroNCAP_Side_Barrier,
    EuroNCAP_Side_Pole,
    EuroNCAP_Side_FarSide,
    UN_Frontal_50kmh_R137,
    UN_Frontal_56kmh_ODB_R94,
    UN_Side_Pole_R135,
    UN_Side_Barrier_R95,
]
