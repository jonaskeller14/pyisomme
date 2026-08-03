# python-pptx ships no type information: `slides`/`shapes`/`placeholders` hang off a
# `lazyproperty` descriptor no checker can see through.
# pyright: reportAttributeAccessIssue=false, reportIndexIssue=false
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pptx.presentation import Presentation

from pyisomme.report.page.base import Page

if TYPE_CHECKING:
    from pyisomme.report.report import Report


class Page_Cover(Page):
    """Title slide: the report's title over its name and the tests it covers."""

    name = "Cover"
    title: str
    subtitle: str

    def __init__(self, report: Report[Any]) -> None:
        super().__init__(report)
        self.title = report.title
        self.subtitle = f'{report.name}\n{" | ".join([str(isomme.test_number) for isomme in report.isomme_list])}'

    def construct(self, presentation: Presentation) -> None:
        title_slide_layout = presentation.slide_layouts[0]
        slide = presentation.slides.add_slide(title_slide_layout)
        slide.shapes.title.text = self.title
        slide.placeholders[1].text = self.subtitle
