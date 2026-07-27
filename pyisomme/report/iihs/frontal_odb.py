from __future__ import annotations

from pyisomme.isomme import Isomme
from pyisomme.report.page import Page_Cover
from pyisomme.report.criterion import Criterion
from pyisomme.report.report import Report
from typing import Any


class Overall(Criterion):
    name = "Overall"

    def __init__(self, report: Report, isomme: Isomme) -> None:
        super().__init__(report, isomme)

    def calculation(self) -> None:
        pass


class IIHS_Frontal_ODB(Report[Overall]):
    #: The report's criterion tree, defined at module level (see `Overall`).
    Criterion_Overall = Overall

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.pages = [
            Page_Cover(self),
        ]

