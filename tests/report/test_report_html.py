from __future__ import annotations

from pathlib import Path

import pytest

from pyisomme.report import ALL_REPORTS
from tests.report.report_factory import REPORT_FACTORIES


@pytest.mark.html
class TestReportHtml:
    def test_requested_reports(self) -> None:
        output_dir = Path("out")
        output_dir.mkdir(exist_ok=True)

        for report_cls in ALL_REPORTS:
            path = output_dir / f"{report_cls.__name__}.html"
            old_modified_ns = path.stat().st_mtime_ns if path.is_file() else 0

            report = REPORT_FACTORIES[report_cls]()
            report.calculate()
            report.export_html(path=path)

            html = path.read_text(encoding="utf-8")
            assert html.startswith("<!DOCTYPE html>")
            assert html.count('class="page') == len(report.selected_pages)
            assert path.stat().st_mtime_ns > old_modified_ns
