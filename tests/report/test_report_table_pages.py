from __future__ import annotations

from typing import Any

import plotly.graph_objects as go
import pytest

from pyisomme import Isomme
from pyisomme.errors import MissingData
from pyisomme.report import REPORTS
from pyisomme.report.criterion import Criterion, sub
from pyisomme.report.criterion_result import CriterionResult
from pyisomme.report.euro_ncap.frontal_50kmh import EuroNCAP_Frontal_50kmh
from pyisomme.report.euro_ncap.side_farside_vtc import EuroNCAP_Side_Farside_VTC
from pyisomme.report.manual import Manual, manual
from pyisomme.report.page2 import (
    ManualInputsPage,
    ReportStatusPage,
    manual_inputs_spec_for,
    report_status_spec_for,
)
from pyisomme.report.report import Report


class Leaf(Criterion):
    name = "Leaf"
    displacement: Manual[
        float,
        manual(0.0, unit="mm", source="measurement"),
    ]
    observation: Manual[
        bool,
        manual(False, source="video", doc="Whether the event was observed."),
    ]

    def calculation(self) -> CriterionResult:
        raise MissingData("leaf channel")


class Overall(Criterion):
    name = "Overall"
    position: Manual[str, manual("1", source="test report")]
    leaf = sub(Leaf)

    def calculation(self) -> CriterionResult:
        return CriterionResult(channel=None, value=0.0, rating=0.0, color=None)


class SmallReport(Report[Overall]):
    _name = "Small"
    Criterion_Overall = Overall


class NoInputs(Criterion):
    name = "No Inputs"

    def calculation(self) -> CriterionResult:
        return CriterionResult(channel=None, value=0.0, rating=0.0, color=None)


class NoInputsReport(Report[NoInputs]):
    _name = "No Inputs"
    Criterion_Overall = NoInputs


def _table(figure: go.Figure) -> go.Table:
    table = figure.data[0]
    assert isinstance(table, go.Table)
    return table


def test_status_page_shows_the_complete_tree_and_missing_reason() -> None:
    isomme = Isomme(test_number="T0")
    report = SmallReport([isomme]).calculate()
    page = ReportStatusPage(report, spec=report_status_spec_for(report))

    table = _table(page.figure((800, 600)))

    assert list(table.cells.values[0]) == ["Overall", "\u00a0\u00a0Leaf"]
    assert list(table.cells.values[1]) == ["OK", "N/A: missing required input data: 'leaf channel'"]
    assert table.cells.height == 30
    assert table.cells.font.size == 12


def test_manual_inputs_page_shows_metadata_and_value_origin() -> None:
    isomme = Isomme(test_number="T0")
    report = SmallReport([isomme])
    report.overall(isomme).position = "3"
    report.overall(isomme).leaf.set_derived_input("observation", True)
    page = ManualInputsPage(report, spec=manual_inputs_spec_for(report))

    table = _table(page.figure((1000, 600)))

    assert list(table.cells.values[0]) == [
        "position",
        "displacement",
        "observation",
    ]
    assert list(table.cells.values[1]) == ["'1'", "0.0 mm", "False"]
    assert list(table.cells.values[2]) == ["test report", "measurement", "video"]
    assert list(table.cells.values[3]) == [
        "'3' (user)",
        "0.0 mm",
        "True (derived)",
    ]


def test_manual_inputs_page_handles_a_report_without_declared_inputs() -> None:
    report = NoInputsReport([Isomme(test_number="T0")])
    page = ManualInputsPage(report, spec=manual_inputs_spec_for(report))

    table = _table(page.figure((800, 600)))

    assert list(table.cells.values[0]) == ["No manual inputs declared"]


def test_frontal_50kmh_exposes_both_reusable_pages() -> None:
    report = EuroNCAP_Frontal_50kmh([Isomme(test_number="T0")])

    status_page = next(
        page for page in report.available_pages if isinstance(page, ReportStatusPage)
    )
    inputs_page = next(
        page for page in report.available_pages if isinstance(page, ManualInputsPage)
    )

    assert isinstance(_table(status_page.figure((1200, 800))), go.Table)
    assert isinstance(_table(inputs_page.figure((1200, 800))), go.Table)


@pytest.mark.parametrize(
    "report_type",
    [*REPORTS, EuroNCAP_Side_Farside_VTC],
    ids=lambda report_type: report_type.__name__,
)
def test_every_criterion_report_exposes_status_and_manual_input_pages(
    report_type: type[Report[Any]],
) -> None:
    report = report_type([Isomme(test_number="T0")])

    assert [type(page) for page in report.available_pages[1:3]] == [
        ReportStatusPage,
        ManualInputsPage,
    ]
