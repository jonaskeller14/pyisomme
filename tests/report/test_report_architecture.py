from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable

import pytest
from pptx import Presentation as open_presentation
from pptx.presentation import Presentation

from pyisomme import Isomme
from pyisomme.report.base_report import BaseReport
from pyisomme.report.criterion import Criterion
from pyisomme.report.meta_report import MetaReport
from pyisomme.report.page import Page
from pyisomme.report.report import Report
from pyisomme.report.report_protocol import ReportProtocol

PROTOCOL = ReportProtocol(version="test", sources=())


class Overall(Criterion):
    name = "Overall"

    def calculation(self) -> None:
        self.rating = 1.0


class NamedPage(Page[BaseReport]):
    def __init__(self, report: BaseReport, name: str) -> None:
        super().__init__(report)
        self.name = name

    def construct(self, presentation: Presentation) -> None:
        pass


class DummyReport(Report[Overall]):
    _protocol = PROTOCOL
    _protocols = (PROTOCOL,)
    Criterion_Overall = Overall

    def __init__(self, key: str) -> None:
        self._name = key.title()
        super().__init__([Isomme(test_number=key)])
        self._available_pages = (
            NamedPage(self, "Shared"),
            NamedPage(self, f"Only {key}"),
        )
        self.reset_pages()


@pytest.fixture
def dummy_report() -> Callable[[str], DummyReport]:
    def _build(key: str) -> DummyReport:
        return DummyReport(key)

    return _build


@pytest.fixture
def dummy_reports(dummy_report: Callable[[str], DummyReport]) -> dict[str, DummyReport]:
    return {key: dummy_report(key) for key in ("alpha", "beta")}


class TestReportHierarchy:
    def test_bare_report_has_no_silent_empty_criterion_tree(self) -> None:
        with pytest.raises(TypeError, match="must declare Criterion_Overall"):
            Report([Isomme(test_number="test")])

    def test_generic_meta_report_is_a_concrete_non_scoring_composite(
        self, dummy_reports: dict[str, DummyReport]
    ) -> None:
        report = MetaReport(dummy_reports, name="Bundle")

        assert isinstance(report, BaseReport)
        assert report.calculate() is report
        for child in dummy_reports.values():
            assert child.overall(child.isomme_list[0]).rating == 1.0
        assert report.rating is None
        assert report.ratings == {}

    def test_meta_report_instance_state_is_not_shared(
        self, dummy_report: Callable[[str], DummyReport]
    ) -> None:
        first = MetaReport({"alpha": dummy_report("alpha")})
        second = MetaReport({"beta": dummy_report("beta")})

        first.ratings["score"] = 1.0
        assert second.ratings == {}

    def test_subreports_are_keyed_and_read_only(
        self, dummy_report: Callable[[str], DummyReport]
    ) -> None:
        alpha = dummy_report("alpha")
        report = MetaReport({"alpha": alpha})

        assert report.subreports["alpha"] is alpha
        assert report.reports == (alpha,)
        with pytest.raises(TypeError):
            report.subreports["other"] = DummyReport("other")  # type: ignore[index]

    def test_inputs_and_protocols_use_stable_subreport_keys(
        self, dummy_reports: dict[str, DummyReport]
    ) -> None:
        report = MetaReport(dummy_reports)

        assert list(report.get_inputs()) == ["alpha", "beta"]
        assert report.subreport_protocols["alpha"] == PROTOCOL
        assert report.set_inputs({"alpha": {}}) is report
        with pytest.raises(KeyError):
            report.set_inputs({"missing": {}})

    def test_meta_page_selection_is_qualified_and_does_not_mutate_children(
        self, dummy_reports: dict[str, DummyReport]
    ) -> None:
        alpha = dummy_reports["alpha"]
        child_selection = alpha.selected_pages
        report = MetaReport(dummy_reports, name="Bundle")

        assert [page.name for page in report.available_pages] == [
            "Cover",
            "Shared",
            "Only alpha",
            "Shared",
            "Only beta",
        ]
        report.clear_pages()
        report.select_pages("alpha/Shared")

        assert [page.name for page in report.selected_pages] == ["Shared"]
        assert alpha.selected_pages == child_selection

        report.reset_pages()
        report.deselect_pages("beta/*")
        assert [page.name for page in report.selected_pages] == [
            "Cover",
            "Shared",
            "Only alpha",
        ]

    @pytest.mark.parametrize("subreport_keys", [(), ("invalid/key",)])
    def test_invalid_subreport_keys_fail_at_construction(
        self,
        subreport_keys: tuple[str, ...],
        dummy_report: Callable[[str], DummyReport],
    ) -> None:
        with pytest.raises(ValueError):
            MetaReport({key: dummy_report("alpha") for key in subreport_keys})

    def test_meta_cover_exports_through_the_shared_implementation(
        self, dummy_report: Callable[[str], DummyReport]
    ) -> None:
        report = MetaReport({"alpha": dummy_report("alpha")}, name="Bundle")
        report.clear_pages()
        report.select_pages("Cover")

        with TemporaryDirectory() as directory:
            path = Path(directory) / "meta.pptx"
            report.export_pptx(path)
            presentation = open_presentation(path)

        assert len(presentation.slides) == 1
