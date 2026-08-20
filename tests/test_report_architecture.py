from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

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


class TestReportHierarchy(unittest.TestCase):
    def test_bare_report_has_no_silent_empty_criterion_tree(self) -> None:
        with self.assertRaisesRegex(TypeError, "must declare Criterion_Overall"):
            Report([Isomme(test_number="test")])

    def test_generic_meta_report_is_a_concrete_non_scoring_composite(self) -> None:
        alpha = DummyReport("alpha")
        beta = DummyReport("beta")
        report = MetaReport({"alpha": alpha, "beta": beta}, name="Bundle")

        self.assertIsInstance(report, BaseReport)
        self.assertIs(report.calculate(), report)
        self.assertEqual(alpha.overall(alpha.isomme_list[0]).rating, 1.0)
        self.assertEqual(beta.overall(beta.isomme_list[0]).rating, 1.0)
        self.assertIsNone(report.rating)
        self.assertEqual({}, report.ratings)

    def test_meta_report_instance_state_is_not_shared(self) -> None:
        first = MetaReport({"alpha": DummyReport("alpha")})
        second = MetaReport({"beta": DummyReport("beta")})

        first.ratings["score"] = 1.0
        self.assertEqual({}, second.ratings)

    def test_subreports_are_keyed_and_read_only(self) -> None:
        alpha = DummyReport("alpha")
        report = MetaReport({"alpha": alpha})

        self.assertIs(report.subreports["alpha"], alpha)
        self.assertEqual((alpha,), report.reports)
        with self.assertRaises(TypeError):
            report.subreports["other"] = DummyReport("other")  # type: ignore[index]

    def test_inputs_and_protocols_use_stable_subreport_keys(self) -> None:
        alpha = DummyReport("alpha")
        beta = DummyReport("beta")
        report = MetaReport({"alpha": alpha, "beta": beta})

        self.assertEqual(["alpha", "beta"], list(report.get_inputs()))
        self.assertEqual(PROTOCOL, report.subreport_protocols["alpha"])
        self.assertIs(report.set_inputs({"alpha": {}}), report)
        with self.assertRaises(KeyError):
            report.set_inputs({"missing": {}})

    def test_meta_page_selection_is_qualified_and_does_not_mutate_children(
        self,
    ) -> None:
        alpha = DummyReport("alpha")
        beta = DummyReport("beta")
        child_selection = alpha.selected_pages
        report = MetaReport({"alpha": alpha, "beta": beta}, name="Bundle")

        self.assertEqual(
            ["Cover", "Shared", "Only alpha", "Shared", "Only beta"],
            [page.name for page in report.available_pages],
        )
        report.clear_pages()
        report.select_pages("alpha/Shared")

        self.assertEqual(["Shared"], [page.name for page in report.selected_pages])
        self.assertEqual(child_selection, alpha.selected_pages)

        report.reset_pages()
        report.deselect_pages("beta/*")
        self.assertEqual(
            ["Cover", "Shared", "Only alpha"],
            [page.name for page in report.selected_pages],
        )

    def test_invalid_subreport_keys_fail_at_construction(self) -> None:
        with self.assertRaises(ValueError):
            MetaReport({})
        with self.assertRaises(ValueError):
            MetaReport({"invalid/key": DummyReport("alpha")})

    def test_meta_cover_exports_through_the_shared_implementation(self) -> None:
        report = MetaReport({"alpha": DummyReport("alpha")}, name="Bundle")
        report.clear_pages()
        report.select_pages("Cover")

        with TemporaryDirectory() as directory:
            path = Path(directory) / "meta.pptx"
            report.export_pptx(path)
            presentation = open_presentation(path)

        self.assertEqual(1, len(presentation.slides))


if __name__ == "__main__":
    unittest.main()
