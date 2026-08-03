from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any

from pptx.presentation import Presentation

if TYPE_CHECKING:
    from pyisomme.report.report import Report


class Page:
    name: str
    report: Report[Any]

    def __init__(self, report: Report[Any]) -> None:
        self.report = report

    @abstractmethod
    def construct(self, presentation: Presentation) -> None:
        """Append this page's slide(s) to ``presentation``."""

    def __repr__(self) -> str:
        return f"Page({self.name})"
