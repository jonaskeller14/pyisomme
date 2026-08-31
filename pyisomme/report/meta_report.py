from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Any

import numpy as np

from pyisomme.report.base_report import BaseReport
from pyisomme.report.page import Page
from pyisomme.report.page2.cover import CoverPage
from pyisomme.report.report import Report
from pyisomme.report.report_protocol import ReportProtocol
from pyisomme.report.validate import Issue
from pyisomme.utils import json_encode


class MetaReport(BaseReport):
    """A report composed from independently configured subreports."""

    _name = "Meta Report"
    max_rating: float | None = None

    def __init__(
        self,
        reports: Mapping[str, BaseReport],
        title: str = "Unnamed Report",
        pages: Sequence[Page[Any]] = (),
        include_cover: bool = True,
        name: str | None = None,
    ) -> None:
        super().__init__(title=title)
        if name is not None:
            self._name = name
        if not reports:
            raise ValueError("A MetaReport requires at least one subreport.")
        if any(not key or "/" in key for key in reports):
            raise ValueError("Subreport keys must be non-empty and cannot contain '/'.")

        self._reports = dict(reports)
        self.rating: float | None = None
        self.ratings: dict[str, float] = {}

        own_pages: tuple[Page[Any], ...] = (
            (CoverPage(self),) if include_cover else ()
        ) + tuple(pages)
        child_pages = tuple(
            page for report in self._reports.values() for page in report.available_pages
        )
        self._own_pages = own_pages
        self._available_pages = own_pages + child_pages
        self.reset_pages()

    @property
    def subreports(self) -> Mapping[str, BaseReport]:
        return MappingProxyType(self._reports)

    @property
    def reports(self) -> tuple[BaseReport, ...]:
        """Subreports in deterministic calculation and export order."""
        return tuple(self._reports.values())

    @property
    def coverage_labels(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                label
                for report in self._reports.values()
                for label in report.coverage_labels
            )
        )

    def _page_entries(self) -> tuple[tuple[str, Page[Any]], ...]:
        entries = [(page.name, page) for page in self._own_pages]
        for key, report in self._reports.items():
            entries.extend(
                (f"{key}/{path}", page) for path, page in report._page_entries()
            )
        return tuple(entries)

    def calculate(self) -> MetaReport:
        for report in self._reports.values():
            report.calculate()
        self.aggregate_results()
        return self

    def aggregate_results(self) -> None:
        """Optionally combine subreport results into :attr:`rating` and :attr:`ratings`."""

    def sub_rating(self, report: Report[Any]) -> float:
        """Return the NaN-propagating mean overall rating of a criterion report."""
        ratings = [
            (
                report.criterion_overall[isomme].result.rating
                if report.criterion_overall[isomme].result is not None
                else float("nan")
            )
            for isomme in report.isomme_list
        ]
        return float(np.mean(ratings)) if ratings else float(np.nan)

    def print_results(self) -> None:
        for report in self._reports.values():
            report.print_results()

        if self.ratings:
            print(f"\n{self.name}")
            for label, points in self.ratings.items():
                print(f"  {label:<34}{points:>8.5g}")
            rating = "n/a" if self.rating is None else f"{self.rating:.5g}"
            maximum = "n/a" if self.max_rating is None else f"{self.max_rating:.5g}"
            print(f"  {'TOTAL':<34}{rating:>8} / {maximum}")

    def json_results(self) -> dict[str, Any]:
        return {
            "Overall": {
                "result": {
                    "name": "Overall",
                    "value": json_encode(self.rating),
                    "rating": json_encode(self.rating),
                    "color": None,
                    "status": "OK",
                }
            },
            **{name: report.json_results() for name, report in self._reports.items()},
        }

    def validate(self, errors_only: bool = False) -> list[Issue]:
        """Return every child issue with its stable subreport key prefixed."""
        return [
            Issue(
                issue.check,
                issue.severity,
                f"{key}/{issue.path}" if issue.path else key,
                issue.message,
            )
            for key, report in self._reports.items()
            for issue in report.validate(errors_only=errors_only)
        ]

    def describe(self) -> str:
        sections = [f"# {type(self).__name__}", ""]
        for key, report in self._reports.items():
            sections.extend(
                (f"## `{key}` — {report.name}", "", report.describe().rstrip(), "")
            )
        return "\n".join(sections).rstrip() + "\n"

    def get_inputs(self) -> dict[str, Any]:
        return {key: report.get_inputs() for key, report in self._reports.items()}

    def set_inputs(self, inputs: dict[str, Any]) -> MetaReport:
        for key, values in inputs.items():
            if key not in self._reports:
                raise KeyError(
                    f"{self}: no subreport {key!r}. Available: {sorted(self._reports)}"
                )
            self._reports[key].set_inputs(values)
        return self

    def print_inputs(self) -> MetaReport:
        for key, report in self._reports.items():
            print(f"{key}: {report.name}")
            report.print_inputs()
        return self

    @property
    def subreport_protocols(self) -> Mapping[str, ReportProtocol]:
        """Protocols of criterion subreports; configure each subreport directly."""
        return MappingProxyType(
            {
                key: report.protocol
                for key, report in self._reports.items()
                if isinstance(report, Report)
            }
        )
