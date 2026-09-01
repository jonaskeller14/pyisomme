from __future__ import annotations

from pathlib import Path

import pytest

from pyisomme.report import ALL_REPORTS
from tests.report.report_factory import REPORT_FACTORIES


@pytest.mark.pdf
class TestReportPdf:
    @pytest.mark.parametrize("report_cls", ALL_REPORTS, ids=lambda cls: cls.__name__)
    def test_requested_reports(
        self, pytestconfig: pytest.Config, report_cls: type
    ) -> None:
        pdf_report = pytestconfig.getoption("--report")
        if pdf_report is not None and report_cls.__name__ != pdf_report.strip():
            pytest.skip(f"Not selected by --report={pdf_report}")

        output_dir = Path("out")
        output_dir.mkdir(exist_ok=True)

        path = output_dir / f"{report_cls.__name__}.pdf"
        old_modified_ns = path.stat().st_mtime_ns if path.is_file() else 0

        report = REPORT_FACTORIES[report_cls]()
        report.calculate()
        report.export_pdf(path=path)

        assert path.read_bytes().startswith(b"%PDF-")
        assert path.stat().st_mtime_ns > old_modified_ns
