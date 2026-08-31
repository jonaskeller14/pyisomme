from __future__ import annotations

from pathlib import Path

import pytest

from pyisomme.report import ALL_REPORTS
from tests.report.report_factory import REPORT_FACTORIES


@pytest.mark.pdf
class TestReportPdf:
    def test_requested_reports(self, pytestconfig: pytest.Config) -> None:
        pdf_report = pytestconfig.getoption("--report")
        if pdf_report is None:
            report_clss = ALL_REPORTS
        else:
            requested_report = pdf_report.strip()
            report_cls = next(
                (r for r in ALL_REPORTS if r.__name__ == requested_report), None
            )
            assert report_cls is not None, f"Unknown Report: {requested_report}"
            report_clss = [report_cls]

        output_dir = Path("out")
        output_dir.mkdir(exist_ok=True)

        for report_cls in report_clss:
            path = output_dir / f"{report_cls.__name__}.pdf"
            old_modified_ns = path.stat().st_mtime_ns if path.is_file() else 0

            report = REPORT_FACTORIES[report_cls]()
            report.calculate()
            report.export_pdf(path=path)

            assert path.read_bytes().startswith(b"%PDF-")
            assert path.stat().st_mtime_ns > old_modified_ns
