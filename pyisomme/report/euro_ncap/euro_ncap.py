from pyisomme.report.report import MetaReport
from pyisomme.report.page import Page_Cover
from pyisomme.report.euro_ncap.frontal_50kmh import EuroNCAP_Frontal_50kmh
from pyisomme.report.euro_ncap.frontal_mpdb import EuroNCAP_Frontal_MPDB
from pyisomme.report.euro_ncap.side_pole import EuroNCAP_Side_Pole
from pyisomme.report.euro_ncap.side_barrier import EuroNCAP_Side_Barrier
from pyisomme.report.euro_ncap.side_farside import EuroNCAP_Side_FarSide


class EuroNCAP(MetaReport):
    name = "Euro-NCAP"
    title = "Euro-NCAP"
    protocol = "9.3"
    protocols = {
        "9.3": "Version 9.3 (05.12.2023) [references/Euro-NCAP/euro-ncap-assessment-protocol-aop-v93.pdf]"
    }

    def __init__(self, frontal_50kmh: list, frontal_mpdb: list, side_pole: list, side_barrier: list, side_farside: list, *args, **kwargs):
        super().__init__(isomme_list=[], *args, **kwargs)

        self.frontal_50kmh = EuroNCAP_Frontal_50kmh(*frontal_50kmh)
        self.frontal_mpdb = EuroNCAP_Frontal_MPDB(*frontal_mpdb)
        self.side_pole = EuroNCAP_Side_Pole(*side_pole)
        self.side_barrier = EuroNCAP_Side_Barrier(*side_barrier)
        self.side_farside = EuroNCAP_Side_FarSide(*side_farside)

        self.reports = [
            self.frontal_50kmh,
            self.frontal_mpdb,
            self.side_pole,
            self.side_barrier,
            self.side_farside,
        ]

        self.pages = [
            Page_Cover(self),
            *[page for report in self.reports for page in report.pages],
        ]
