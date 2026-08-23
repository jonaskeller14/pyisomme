from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from fnmatch import fnmatch
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
                # TODO(step-11): resolve page data in construct() and remove this re-initialisation.
                page.__init__(page.report)
                page.construct(presentation)

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

    def __repr__(self) -> str:
        return f"{type(self).__name__}(title={self.title!r}, name={self.name!r})"
