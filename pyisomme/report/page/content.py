# python-pptx ships no type information: `slides`/`shapes`/`placeholders` hang off a
# `lazyproperty` descriptor no checker can see through, and the slide dimensions are
# Optional. Nothing here can be checked, so the whole file opts out.
# pyright: reportAttributeAccessIssue=false, reportIndexIssue=false, reportOptionalOperand=false
from __future__ import annotations

import getpass
import os
from abc import ABC
from datetime import datetime
from typing import Any

from pptx.presentation import Presentation
from pptx.util import Inches
from typing_extensions import override

from pyisomme.report.page.base import Page


def _current_user() -> str:
    try:
        return os.getlogin()
    except OSError:
        try:
            return getpass.getuser()
        except Exception:
            return "unknown"


class Page_Content(Page[Any], ABC):
    """A titled content slide with a footer, and nothing in the body."""

    title: str | None = None
    footer: str | None = None

    def _get_footer(self) -> str:
        if self.footer is not None:
            return self.footer
        return f"{datetime.now().strftime('%d.%m.%Y')} | {_current_user()}"

    @override
    def construct(self, presentation: Presentation) -> None:
        title_slide_layout = presentation.slide_layouts[1]
        slide = presentation.slides.add_slide(title_slide_layout)
        slide.shapes.title.text = self.title

        slide_width = presentation.slide_width
        slide_height = presentation.slide_height

        text_box = slide.shapes.add_textbox(
            0, Inches(slide_height / Inches(1) - 0.3), slide_width, Inches(0.3)
        )
        text_frame = text_box.text_frame
        text_frame.margin_top = Inches(0.05)
        text_frame.margin_bottom = Inches(0.05)
        text_frame.margin_left = Inches(0.05)
        text_frame.margin_right = Inches(0.05)
        paragraph = text_frame.paragraphs[0]
        paragraph.text = self._get_footer()
        paragraph.font.size = Inches(0.2)
