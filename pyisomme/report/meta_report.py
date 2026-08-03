from __future__ import annotations

from pyisomme.report.report import Report
from pyisomme.report.criterion import Criterion
from pyisomme.report.validate import Issue

import numpy as np
from typing import Any


class MetaReport(Report[Criterion]):
    reports: list[Report]
    rating: float = np.nan

    def calculate(self) -> MetaReport:
        for report in self.reports:
            report.calculate()
        self.calculation()
        return self

    def calculation(self) -> None:
        pass

    def print_results(self) -> MetaReport:
        for report in self.reports:
            report.print_results()
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
