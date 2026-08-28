from __future__ import annotations

import pytest
from matplotlib import pyplot as plt

from pyisomme.report.euro_ncap.protocols import PROTOCOL_FARSIDE_2_5
from pyisomme.report.page import Page_Plot_nxn
from tests.report.report_factory import build_euroncap_side_farside


def test_farside_uses_protocol_25_by_default() -> None:
    report = build_euroncap_side_farside()

    assert report.protocol is PROTOCOL_FARSIDE_2_5
    assert tuple(protocol.version for protocol in report.protocols) == ("2.4", "2.5")


@pytest.mark.parametrize(
    ("countermeasure", "zone", "red_line_over_125", "expected"),
    [
        (True, "capping", False, (0.0, 0.0, 0.0)),
        (True, "red", False, (0.0, 4.0, 0.0)),
        (True, "red", True, (2.0, 4.0, 0.0)),
        (True, "orange", False, (3.0, 3.0, 3.0)),
        (False, "red", False, (0.0, 1.0, 0.0)),
        (False, "orange", False, (1.0, 1.0, 1.0)),
    ],
)
def test_farside_head_excursion_score_caps(
    countermeasure: bool,
    zone: str,
    red_line_over_125: bool,
    expected: tuple[float, float, float],
) -> None:
    report = build_euroncap_side_farside()
    isomme = report.isomme_list[0]
    excursion = report.overall(isomme).criterion_head_excursion
    excursion.far_side_countermeasure = countermeasure
    excursion.excursion_zone = zone
    excursion.red_line_more_than_125_mm_outboard = red_line_over_125

    report.calculate()

    assert (
        excursion.max_head_score,
        excursion.max_neck_score,
        excursion.max_chest_score,
    ) == expected
    assert excursion.result is not None
    assert excursion.result.value == sum(expected)


def test_farside_occupant_interaction_deduction_is_applied_once() -> None:
    report = build_euroncap_side_farside()
    isomme = report.isomme_list[0]
    report.calculate()
    baseline = report.overall(isomme).result
    assert baseline is not None

    modifier = report.overall(isomme).criterion_occupant_to_occupant_protection
    modifier.dual_occupancy_head_interaction = True
    modifier.protection_zone_not_met = True
    report.calculate()

    result = report.overall(isomme).result
    assert result is not None
    assert modifier.result is not None
    assert modifier.result.rating == -1.0
    assert result.rating == pytest.approx(max(0.0, baseline.rating - 1.0))


def test_farside_damage_is_calculated_and_does_not_affect_head_score() -> None:
    report = build_euroncap_side_farside()
    isomme = report.isomme_list[0]
    head = report.overall(isomme).criterion_head
    head.hard_contact = False

    report.calculate()

    assert head.criterion_damage.result is not None
    assert head.criterion_damage.result.rating == 0.0
    assert head.result is not None
    assert head.result.rating == pytest.approx(head.criterion_head_a3ms.result.rating)  # pyright: ignore[reportOptionalMemberAccess]
