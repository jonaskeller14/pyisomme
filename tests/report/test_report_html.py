from __future__ import annotations

import re
from pathlib import Path

import pytest

from pyisomme.report import ALL_REPORTS
from tests.report.report_factory import REPORT_FACTORIES


@pytest.mark.html
class TestReportHtml:
    @pytest.mark.parametrize("report_cls", ALL_REPORTS, ids=lambda cls: cls.__name__)
    def test_requested_reports(
        self, pytestconfig: pytest.Config, report_cls: type
    ) -> None:
        html_report = pytestconfig.getoption("--report")
        if html_report is not None and report_cls.__name__ != html_report.strip():
            pytest.skip(f"Not selected by --report={html_report}")

        output_dir = Path("out")
        output_dir.mkdir(exist_ok=True)

        path = output_dir / f"{report_cls.__name__}.html"
        old_modified_ns = path.stat().st_mtime_ns if path.is_file() else 0

        report = REPORT_FACTORIES[report_cls]()
        report.calculate()
        report.export_html(path=path)

        html = path.read_text(encoding="utf-8")
        assert html.startswith("<!DOCTYPE html>")
        page_count = sum(
            "page" in classes.split() for classes in re.findall(r'class="([^"]*)"', html)
        )
        assert page_count == len(report.selected_pages)
        assert path.stat().st_mtime_ns > old_modified_ns
