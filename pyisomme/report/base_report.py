from __future__ import annotations

import asyncio
import logging
import sys
import tempfile
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from fnmatch import fnmatch
from html import escape
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pptx import Presentation
from pptx.presentation import Presentation as PptxPresentation
from tqdm.auto import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

if TYPE_CHECKING:
    from pyisomme.report.page import Page
    from pyisomme.report.validate import Issue


logger = logging.getLogger(__name__)


class BaseReport(ABC):
    """Common lifecycle and presentation behaviour for reports and composites."""

    _name = "Unnamed Report"

    def __init__(self, title: str = "Unnamed Report") -> None:
        self.title = title
        self._available_pages: tuple[Page[Any], ...] = ()
        self._selected_pages: list[Page[Any]] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def coverage_labels(self) -> tuple[str, ...]:
        """Short identifiers rendered on a cover page."""
        return ()

    @abstractmethod
    def calculate(self) -> BaseReport:
        """Calculate this report and return it for optional call chaining."""

    @abstractmethod
    def get_inputs(self) -> dict[str, Any]:
        """Return all manual inputs in a JSON-serialisable mapping."""

    @abstractmethod
    def set_inputs(self, inputs: dict[str, Any]) -> BaseReport | None:
        """Apply a mapping produced by :meth:`get_inputs`."""

    @abstractmethod
    def print_inputs(self) -> BaseReport | None:
        """Print every manual input and its current source."""

    @abstractmethod
    def print_results(self) -> None:
        """Print the calculated results."""

    @abstractmethod
    def json_results(self) -> dict[str, Any]:
        """Return the results in json dictionary format"""

    @abstractmethod
    def validate(self, errors_only: bool = False) -> list[Issue]:
        """Validate the report definition."""

    @abstractmethod
    def describe(self) -> str:
        """Describe the report definition as Markdown."""

    def print_validation(self) -> None:
        from pyisomme.report.validate import format_issues

        issues = self.validate()
        print(format_issues(issues) if issues else f"{self}: no issues found.")

    @property
    def available_pages(self) -> tuple[Page[Any], ...]:
        return self._available_pages

    @property
    def selected_pages(self) -> tuple[Page[Any], ...]:
        return tuple(self._selected_pages)

    def _page_entries(self) -> tuple[tuple[str, Page[Any]], ...]:
        """Selection name and page, in export order."""
        return tuple((page.name, page) for page in self.available_pages)

    @staticmethod
    def _matches_page(
        path: str, page: Page[Any], name_patterns: tuple[str, ...]
    ) -> bool:
        return any(
            fnmatch(path, pattern) or fnmatch(page.name, pattern)
            for pattern in name_patterns
        )

    def select_pages(self, *name_patterns: str) -> None:
        """Add matching pages while preserving :attr:`available_pages` order."""
        selected = set(self._selected_pages)
        self._selected_pages = [
            page
            for path, page in self._page_entries()
            if page in selected or self._matches_page(path, page, name_patterns)
        ]

    def deselect_pages(self, *name_patterns: str) -> None:
        """Remove pages matching a page name or a composite-qualified path."""
        selected = set(self._selected_pages)
        self._selected_pages = [
            page
            for path, page in self._page_entries()
            if page in selected and not self._matches_page(path, page, name_patterns)
        ]

    def clear_pages(self) -> None:
        self._selected_pages = []

    def reset_pages(self) -> None:
        self._selected_pages = list(self.available_pages)

    def export_pptx(self, path: str | Path, template: str | Path | None = None) -> None:
        presentation: PptxPresentation = Presentation(template)

        with logging_redirect_tqdm():
            for page_number, page in enumerate(
                tqdm(self.selected_pages, desc="Construct Pages")
            ):
                logger.info(f"{page_number}:{page.name}")
                page.construct_pptx(presentation)

        attempts = 10
        for attempt in range(1, attempts + 1):
            try:
                presentation.save(path)
                break
            except PermissionError:
                if attempt == attempts:
                    raise
                logger.warning(
                    "Could not save %s (attempt %d/%d); retrying",
                    path,
                    attempt,
                    attempts,
                )
                time.sleep(5)
        logger.info(f"pptx successfully exported: {path}")

    def _render_html_document(self) -> str:
        """Render all selected pages into one complete HTML document."""
        stylesheet_path = Path(__file__).with_name("page2") / "style.css"
        stylesheet = stylesheet_path.read_text(encoding="utf-8")

        page_fragments: list[str] = []
        with logging_redirect_tqdm():
            for page_number, page in enumerate(
                tqdm(self.selected_pages, desc="Render Pages")
            ):
                logger.info("%d:%s", page_number, page.name)
                page_fragments.append(page.render_html())

        return "\n".join(
            (
                "<!DOCTYPE html>",
                '<html lang="en">',
                "<head>",
                '  <meta charset="utf-8">',
                '  <meta name="viewport" content="width=device-width, initial-scale=1">',
                f"  <title>{escape(self.title)}</title>",
                '  <script src="https://cdn.plot.ly/plotly-3.1.0.min.js" charset="utf-8"></script>',
                "  <style>",
                stylesheet,
                "  </style>",
                "  <script>",
                "    (() => {",
                "      const media = window.matchMedia('screen and (max-width: 1154px)');",
                "      const updatePageScale = () => {",
                "        for (const page of document.querySelectorAll('.page')) {",
                "          page.style.removeProperty('--screen-page-scale');",
                "          page.style.removeProperty('--screen-page-margin');",
                "          if (!media.matches) continue;",
                "          const scale = Math.min(1, (window.innerWidth - 32) / page.offsetWidth);",
                "          page.style.setProperty('--screen-page-scale', String(scale));",
                "          page.style.setProperty(",
                "            '--screen-page-margin',",
                "            `${page.offsetHeight * (scale - 1) + 24}px`,",
                "          );",
                "        }",
                "      };",
                "      window.addEventListener('resize', updatePageScale);",
                "      window.addEventListener('load', updatePageScale);",
                "      updatePageScale();",
                "    })();",
                "  </script>",
                "</head>",
                "<body>",
                *page_fragments,
                "</body>",
                "</html>",
            )
        )

    def export_html(self, path: str | Path) -> None:
        """Export the selected pages as one UTF-8 HTML document."""
        output_path = Path(path)
        output_path.write_text(self._render_html_document(), encoding="utf-8")
        logger.info("html successfully exported: %s", output_path)

    def export(
        self,
        *paths: str | Path,
        template: str | Path | None = None,
    ) -> None:
        """Export one report to independently located HTML, PDF, and PPTX files.

        The requested format is inferred from each path's extension. When both HTML
        and PDF are requested, their shared HTML document is rendered only once.
        """
        if not paths:
            raise ValueError("at least one report output path is required")

        output_paths: dict[str, Path] = {}
        supported_suffixes = {".html", ".pdf", ".pptx"}
        for path in paths:
            output_path = Path(path)
            suffix = output_path.suffix.lower()
            if suffix not in supported_suffixes:
                formats = ", ".join(sorted(supported_suffixes))
                raise ValueError(
                    f"unsupported report output extension {suffix or '(none)'!r}; "
                    f"expected one of: {formats}"
                )
            if suffix in output_paths:
                raise ValueError(f"multiple {suffix} output paths were provided")
            output_paths[suffix] = output_path

        if template is not None and ".pptx" not in output_paths:
            raise ValueError("template requires a .pptx output path")

        html_path = output_paths.get(".html")
        pdf_path = output_paths.get(".pdf")
        if html_path is not None or pdf_path is not None:
            html_document = self._render_html_document()
            if html_path is not None:
                html_path.write_text(html_document, encoding="utf-8")
                logger.info("html successfully exported: %s", html_path)

            if pdf_path is not None:
                if html_path is not None:
                    self._export_pdf_from_html(html_path.resolve(), pdf_path.resolve())
                else:
                    with tempfile.TemporaryDirectory(
                        prefix="pyisomme-report-"
                    ) as directory:
                        temporary_html_path = Path(directory) / "report.html"
                        temporary_html_path.write_text(html_document, encoding="utf-8")
                        self._export_pdf_from_html(
                            temporary_html_path, pdf_path.resolve()
                        )

        pptx_path = output_paths.get(".pptx")
        if pptx_path is not None:
            self.export_pptx(pptx_path, template=template)

    @staticmethod
    async def _export_pdf_async(html_path: Path, output_path: Path) -> None:
        from playwright.async_api import async_playwright

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            try:
                page = await browser.new_page()
                await page.goto(html_path.as_uri(), wait_until="networkidle")
                await page.evaluate("document.fonts ? document.fonts.ready : undefined")
                if await page.locator(".plotly-graph-div").count():
                    await page.wait_for_function(
                        """() => Array.from(
                            document.querySelectorAll('.plotly-graph-div')
                        ).every(element => element.data && element.layout)"""
                    )
                await page.evaluate(
                    """() => {
                        const pages = document.querySelectorAll('body > .page');
                        if (pages.length) pages[pages.length - 1].classList.add('last-page');
                    }"""
                )
                await page.pdf(
                    path=str(output_path),
                    prefer_css_page_size=True,
                    print_background=True,
                )
            finally:
                await browser.close()

    @classmethod
    def _run_pdf_export(cls, html_path: Path, output_path: Path) -> None:
        if sys.platform == "win32":
            from asyncio.windows_events import ProactorEventLoop

            loop = ProactorEventLoop()
        else:
            loop = asyncio.new_event_loop()

        try:
            loop.run_until_complete(cls._export_pdf_async(html_path, output_path))
        finally:
            loop.close()

    def _export_pdf_from_html(self, html_path: Path, output_path: Path) -> None:
        """Export an existing HTML document to PDF."""
        try:
            from playwright.async_api import Error as PlaywrightError
        except ImportError as exc:
            raise RuntimeError(
                "PDF export requires the optional Playwright dependency. Install it "
                "with `pip install 'pyisomme[pdf]'`, then run "
                "`python -m playwright install chromium`."
            ) from exc

        try:
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                self._run_pdf_export(html_path, output_path)
            else:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    executor.submit(
                        self._run_pdf_export, html_path, output_path
                    ).result()
        except PlaywrightError as exc:
            if "playwright install" in str(exc).lower():
                raise RuntimeError(
                    "Playwright Chromium is not installed. Run "
                    "`python -m playwright install chromium` and retry."
                ) from exc
            raise

        logger.info("pdf successfully exported: %s", output_path)

    def export_pdf(self, path: str | Path) -> None:
        """Render the selected pages to PDF, including from an async notebook."""
        self.export(path)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(title={self.title!r}, name={self.name!r})"
