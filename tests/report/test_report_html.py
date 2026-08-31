from __future__ import annotations

import re
from pathlib import Path

import pytest

from pyisomme.report import ALL_REPORTS
from tests.report.report_factory import REPORT_FACTORIES


@pytest.mark.html
class TestReportHtml:
    def test_requested_reports(self, pytestconfig: pytest.Config) -> None:
        html_report = pytestconfig.getoption("--report")
        if html_report is None:
            report_clss = ALL_REPORTS
        else:
            requested_report = html_report.strip()
            report_cls = next(
                (r for r in ALL_REPORTS if r.__name__ == requested_report), None
            )
            assert report_cls is not None, f"Unknown Report: {requested_report}"
            report_clss = [report_cls]

        output_dir = Path("out")
        output_dir.mkdir(exist_ok=True)

        for report_cls in report_clss:
            path = output_dir / f"{report_cls.__name__}.html"
            old_modified_ns = path.stat().st_mtime_ns if path.is_file() else 0

            report = REPORT_FACTORIES[report_cls]()
            report.calculate()
            report.export_html(path=path)

            html = path.read_text(encoding="utf-8")
            assert html.startswith("<!DOCTYPE html>")
            page_count = sum(
                "page" in classes.split()
                for classes in re.findall(r'class="([^"]*)"', html)
            )
            assert page_count == len(report.selected_pages)
            assert path.stat().st_mtime_ns > old_modified_ns
