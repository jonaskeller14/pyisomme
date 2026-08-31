from __future__ import annotations

from pathlib import Path

import pytest
from pptx import Presentation

from pyisomme.report import ALL_REPORTS
from tests.report.report_factory import REPORT_FACTORIES


@pytest.mark.pptx
class TestReportPptx:
    def test_requested_reports(self, pytestconfig: pytest.Config) -> None:
        pptx_report = pytestconfig.getoption("--report")
        if pptx_report is None:
            report_clss = ALL_REPORTS
        else:
            requested_report = pptx_report.strip()
            report_cls = next(
                (r for r in ALL_REPORTS if r.__name__ == requested_report), None
            )
            assert report_cls is not None, f"Unknown Report: {requested_report}"
            report_clss = [report_cls]

        output_dir = Path("out")
        output_dir.mkdir(exist_ok=True)

        for report_cls in report_clss:
            path = output_dir / f"{report_cls.__name__}.pptx"
            old_modified_ns = path.stat().st_mtime_ns if path.is_file() else 0

            report = REPORT_FACTORIES[report_cls]()

            report.calculate()
            report.export_pptx(path=path)

            presentation = Presentation(path)
            assert len(presentation.slides) >= 1
            assert len(presentation.slides) == len(report.selected_pages)
            assert path.is_file()
            assert path.stat().st_mtime_ns > old_modified_ns
