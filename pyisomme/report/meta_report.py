from __future__ import annotations

from pyisomme.report.report import Report
from pyisomme.report.criterion import Criterion
from pyisomme.report.validate import Issue

import numpy as np
from typing import Any


class MetaReport(Report[Criterion]):
    reports: list[Report]
    rating: float = np.nan
    max_rating: float = np.nan
    ratings: dict[str, float] = {}

    def calculate(self) -> MetaReport:
        for report in self.reports:
            report.calculate()
        self.calculation()
        return self

    def calculation(self) -> None:
        """
        Combine the sub-reports into :attr:`rating` and :attr:`ratings`.

        The default is a no-op: not every meta-report has a scoring scheme that
        ties its load cases together. See ``EuroNCAP`` for one that does.
        """
        pass

    def sub_rating(self, report: Report) -> float:
        """
        The overall rating ``report`` produced, as a single number.

        A load case is normally one test of one vehicle, so this is that test's
        ``Overall``. Several tests in one load case are averaged. ``nan``
        propagates on purpose: a load case whose data is missing must not read as
        a low score, it must read as unknown.
        """
        ratings = [report.criterion_overall[isomme].rating for isomme in report.isomme_list]
        return float(np.mean(ratings)) if ratings else float(np.nan)

    def print_results(self) -> MetaReport:
        for report in self.reports:
            report.print_results()

        if self.ratings:
            print(f"\n{self._report_key(self)}")
            for label, points in self.ratings.items():
                print(f"  {label:<34}{points:>8.5g}")
            print(f"  {'TOTAL':<34}{self.rating:>8.5g} / {self.max_rating:.5g}")
        return self

    def validate(self, errors_only: bool = False) -> list[Issue]:
        """Every sub-report's issues, with the sub-report prefixed onto the path."""
        return [Issue(issue.check, issue.severity,
                      f"{self._report_key(report)}/{issue.path}" if issue.path
                      else self._report_key(report),
                      issue.message)
                for report in self.reports
                for issue in report.validate(errors_only=errors_only)]

    def describe(self) -> str:
        return "\n".join(report.describe() for report in self.reports)

    def _report_key(self, report: Report) -> str:
        return report.name or type(report).__name__

    def get_inputs(self) -> dict[str, Any]:
        """``{sub-report: {test: {path: value}}}`` — a meta-report owns no criteria itself."""
        return {self._report_key(report): report.get_inputs() for report in self.reports}

    def set_inputs(self, inputs: dict[str, Any]) -> MetaReport:
        by_key = {self._report_key(report): report for report in self.reports}
        for key, values in inputs.items():
            if key not in by_key:
                raise KeyError(f"{self}: no sub-report {key!r}. Available: {sorted(by_key)}")
            by_key[key].set_inputs(values)
        return self

    def print_inputs(self) -> MetaReport:
        for report in self.reports:
            print(self._report_key(report))
            report.print_inputs()
        return self
