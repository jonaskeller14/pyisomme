from pyisomme.report.report import MetaReport
from pyisomme.report.page import Page_Cover

class USNCAP(MetaReport):
    name = "US-NCAP"
    title = "US-NCAP"

    def __init__(self, frontal_56kmh: list, frontal_mpdb: list, side_pole: list, side_barrier: list, side_farside: list, *args, **kwargs):
        super().__init__(isomme_list=[], *args, **kwargs)

        self.pages = [
            Page_Cover(self),
            *[page for report in self.reports for page in report.pages],
        ]