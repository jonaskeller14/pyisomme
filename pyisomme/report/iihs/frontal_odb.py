from pyisomme.report.page import Page_Cover
from pyisomme.report.criterion import Criterion
from pyisomme.report.report import Report


class IIHS_Frontal_ODB(Report):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pages = [
            Page_Cover(self),
        ]

    class Criterion_Overall(Criterion):
        name = "Overall"

        def __init__(self, report, isomme):
            super().__init__(report, isomme)

        def calculation(self) -> None:
            pass
