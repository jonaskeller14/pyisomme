from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

import plotly.graph_objects as go
from pptx.presentation import Presentation
from typing_extensions import override

from pyisomme.plotting2 import DEFAULT_CONFIG
from pyisomme.plotting2.plot_line import FigureSize
from pyisomme.report.base_report import BaseReport
from pyisomme.report.page.page import Page
from pyisomme.report.page2.html import render_figure_page
from pyisomme.report.page2.pptx import add_content_slide, add_figure

R = TypeVar("R", bound=BaseReport)
FigureBuilder = Callable[[R, FigureSize], go.Figure]


class FigurePage(Page[R], Generic[R]):
    """A composable report page backed by a Plotly figure builder."""

    def __init__(
        self,
        report: R,
        *,
        name: str,
        title: str,
        figure_builder: FigureBuilder[R],
        footer: str | None = None,
    ) -> None:
        super().__init__(report)
        self.name = name
        self.title = title
        self.figure_builder = figure_builder
        self.footer = footer

    def figure(self, figsize: FigureSize) -> go.Figure:
        return self.figure_builder(self.report, figsize)

    @override
    def render_html(self) -> str:
        return render_figure_page(
            title=self.title,
            figure=self.figure(DEFAULT_CONFIG.default_figsize),
            footer=self.footer,
        )

    @override
    def construct_pptx(self, presentation: Presentation) -> None:
        content_slide = add_content_slide(
            presentation,
            title=self.title,
            footer=self.footer,
        )
        placeholder = content_slide.body_placeholder
        height = 800
        width = round(height * float(placeholder.width) / float(placeholder.height))
        add_figure(content_slide, self.figure((width, height)))


__all__ = ["FigureBuilder", "FigurePage"]
