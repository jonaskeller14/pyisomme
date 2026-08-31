from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pptx.presentation import Presentation

from pyisomme.report.base_report import BaseReport

R = TypeVar("R", bound=BaseReport)


class Page(ABC, Generic[R]):
    name: str
    report: R

    def __init__(self, report: R) -> None:
        self.report = report

    def __repr__(self) -> str:
        return f"Page({self.name})"

    @abstractmethod
    def render_html() -> str:
        "Return page html body as string"

    @abstractmethod
    def construct_pptx(self, presentation: Presentation) -> None:
        """Append this page's slide(s) to ``presentation``."""
