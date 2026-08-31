from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

from pptx.presentation import Presentation

from pyisomme.report.base_report import BaseReport
from pyisomme.report.page import Page


class HtmlPage(Page[BaseReport]):
    name = "HTML page"

    def render_html(self) -> str:
        return '<section class="page"><p>rendered</p></section>'

    def construct_pptx(self, presentation: Presentation) -> None:
        raise NotImplementedError


class HtmlReport(BaseReport):
    _name = "HTML report"

    def __init__(self) -> None:
        super().__init__(title="A <report>")
        self._available_pages = (HtmlPage(self),)
        self.reset_pages()

    def calculate(self) -> HtmlReport:
        return self

    def get_inputs(self) -> dict[str, Any]:
        return {}

    def set_inputs(self, inputs: dict[str, Any]) -> HtmlReport:
        return self

    def print_inputs(self) -> HtmlReport:
        return self

    def print_results(self) -> None:
        return None

    def json_results(self) -> dict[str, Any]:
        return {}

    def validate(self, errors_only: bool = False) -> list[Any]:
        return []

    def describe(self) -> str:
        return ""


def test_export_html_assembles_complete_document(tmp_path: Path) -> None:
    path = tmp_path / "report.html"

    HtmlReport().export_html(path)

    html = path.read_text(encoding="utf-8")
    assert html.startswith("<!DOCTYPE html>")
    assert "<title>A &lt;report&gt;</title>" in html
    assert '<section class="page"><p>rendered</p></section>' in html
    assert 'src="https://cdn.plot.ly/plotly-3.1.0.min.js"' in html
    assert "@page" in html


def test_export_pdf_renders_temporary_html_with_chromium(
    tmp_path: Path, monkeypatch: Any
) -> None:
    import playwright.sync_api

    calls: dict[str, Any] = {}

    class Locator:
        def count(self) -> int:
            return 0

    class BrowserPage:
        def goto(self, url: str, *, wait_until: str) -> None:
            calls["url"] = url
            calls["wait_until"] = wait_until

        def evaluate(self, expression: str) -> None:
            calls["evaluate"] = expression

        def locator(self, selector: str) -> Locator:
            calls["selector"] = selector
            return Locator()

        def pdf(self, **kwargs: Any) -> None:
            calls["pdf"] = kwargs
            Path(kwargs["path"]).write_bytes(b"%PDF-1.7\n")

    class Browser:
        def new_page(self) -> BrowserPage:
            return BrowserPage()

        def close(self) -> None:
            calls["closed"] = True

    class Playwright:
        chromium = SimpleNamespace(launch=lambda: Browser())

    class PlaywrightContext:
        def __enter__(self) -> Playwright:
            return Playwright()

        def __exit__(self, *args: object) -> None:
            return None

    monkeypatch.setattr(
        playwright.sync_api, "sync_playwright", lambda: PlaywrightContext()
    )

    path = tmp_path / "report.pdf"
    HtmlReport().export_pdf(path)

    assert path.read_bytes().startswith(b"%PDF")
    assert calls["url"].startswith("file:")
    assert calls["wait_until"] == "networkidle"
    assert calls["pdf"] == {
        "path": str(path.resolve()),
        "prefer_css_page_size": True,
        "print_background": True,
    }
    assert calls["closed"] is True
