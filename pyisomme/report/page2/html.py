from __future__ import annotations

from functools import lru_cache

import plotly.graph_objects as go
from jinja2 import Environment, PackageLoader, select_autoescape


@lru_cache(maxsize=1)
def environment() -> Environment:
    return Environment(
        loader=PackageLoader("pyisomme.report.page2", "templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )


def render_figure_page(
    *, title: str, figure: go.Figure, footer: str | None = None
) -> str:
    """Render one interactive Plotly page as an embeddable HTML fragment.

    Plotly is loaded once by the containing report document, rather than once
    for every chart.
    """
    html_figure = go.Figure(figure)
    html_figure.update_layout(autosize=True, width=None, height=None)
    chart = html_figure.to_html(
        full_html=False,
        include_plotlyjs=False,
        config={"responsive": True, "displaylogo": False},
        default_width="100%",
        default_height="100%",
    )
    return (
        environment()
        .get_template("figure.html")
        .render(
            title=title,
            chart=chart,
            footer=footer,
        )
    )


__all__ = ["environment", "render_figure_page"]
