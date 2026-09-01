from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from pyisomme.report.base_report import BaseReport


class ExportReport(BaseReport):
    def __init__(self) -> None:
        super().__init__(title="Export test")
        self.render_calls = 0
        self.pdf_html_paths: list[Path] = []
        self.pptx_exports: list[tuple[Path, str | Path | None]] = []

    def calculate(self) -> ExportReport:
        return self

    def get_inputs(self) -> dict[str, Any]:
        return {}

    def set_inputs(self, inputs: dict[str, Any]) -> ExportReport:
        return self

    def print_inputs(self) -> ExportReport:
        return self

    def print_results(self) -> None:
        pass

    def json_results(self) -> dict[str, Any]:
        return {}

    def validate(self, errors_only: bool = False) -> list[Any]:
        return []

    def describe(self) -> str:
        return ""

    def _render_html_document(self) -> str:
        self.render_calls += 1
        return "<!DOCTYPE html><html><body>shared</body></html>"

    def _export_pdf_from_html(self, html_path: Path, output_path: Path) -> None:
        assert html_path.read_text(encoding="utf-8") == self._rendered_document
        self.pdf_html_paths.append(html_path)
        output_path.write_bytes(b"%PDF-test")

    def export_pptx(
        self, path: str | Path, template: str | Path | None = None
    ) -> None:
        output_path = Path(path)
        self.pptx_exports.append((output_path, template))
        output_path.write_bytes(b"pptx")

    @property
    def _rendered_document(self) -> str:
        return "<!DOCTYPE html><html><body>shared</body></html>"


def test_export_reuses_html_for_html_and_pdf(tmp_path: Path) -> None:
    report = ExportReport()
    html_path = tmp_path / "web.html"
    pdf_path = tmp_path / "document.pdf"
    pptx_path = tmp_path / "slides.pptx"
    template = tmp_path / "template.pptx"

    report.export(html_path, pdf_path, pptx_path, template=template)

    assert report.render_calls == 1
    assert html_path.read_text(encoding="utf-8") == report._rendered_document
    assert pdf_path.read_bytes() == b"%PDF-test"
    assert report.pdf_html_paths == [html_path.resolve()]
    assert report.pptx_exports == [(pptx_path, template)]


def test_pdf_only_export_uses_temporary_html(tmp_path: Path) -> None:
    report = ExportReport()
    pdf_path = tmp_path / "document.pdf"

    report.export(pdf_path)

    assert report.render_calls == 1
    assert pdf_path.read_bytes() == b"%PDF-test"
    assert len(report.pdf_html_paths) == 1
    assert not report.pdf_html_paths[0].exists()


@pytest.mark.parametrize(
    ("paths", "template", "message"),
    [
        ((), None, "at least one"),
        (("report.txt",), None, "unsupported"),
        (("one.pdf", "two.pdf"), None, "multiple .pdf"),
        (("report.html",), "template.pptx", "template requires"),
    ],
)
def test_export_rejects_invalid_output_requests(
    paths: tuple[str, ...], template: str | None, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        ExportReport().export(*paths, template=template)
