from __future__ import annotations

from typing import Callable

import pytest

import pyisomme
from pyisomme.report.fmvss import FMVSS_208, DummyType

ReportFactory = Callable[..., FMVSS_208]


def threshold(criterion) -> float:
    return float(criterion.limits.limit_list[0].func(0.0))


def limit_patterns(criterion) -> list[str]:
    return [
        pattern
        for _, node in criterion.walk()
        for limit in node.limits.limit_list
        for pattern in limit.code_patterns or ()
    ]


@pytest.fixture
def build_report() -> ReportFactory:
    """Factory fixture to generate FMVSS_208 reports with variable channel codes."""

    def _build(*codes: str) -> FMVSS_208:
        isomme = pyisomme.Isomme(test_number="FMVSS-208")
        for code in codes:
            isomme.channels.append(
                pyisomme.create_sample(
                    code,
                    t_range=(-0.01, 0.01, 3),
                    y_range=(0.0, 1.0),
                    unit=pyisomme.Code(code).get_default_unit(),  # pyright: ignore[reportArgumentType]
                )
            )
        return FMVSS_208([isomme])

    return _build


class TestFMVSS208:
    def test_conservative_female_fallback_without_identifying_channels(
        self, build_report: ReportFactory
    ) -> None:
        report = build_report()
        occupant = report.overall(report.isomme_list[0]).criterion_driver

        assert occupant.dummy_type == DummyType.FEMALE_5TH.value
        assert not occupant.criterion_containment.contained
        assert threshold(occupant.criterion_hic15) == 700
        assert threshold(occupant.criterion_chest_a3ms) == 60
        assert threshold(occupant.criterion_chest_deflection) == -52
        assert threshold(occupant.criterion_nij) == 1.0
        assert threshold(occupant.criterion_neck_tension) == 2620
        assert threshold(occupant.criterion_neck_compression) == -2520
        assert threshold(occupant.criterion_femur_axial_force.criterion_left) == -6805

        patterns = limit_patterns(occupant)
        assert patterns
        assert all("HF" in pattern for pattern in patterns)

    def test_detects_mixed_driver_and_passenger_dummies(
        self, build_report: ReportFactory
    ) -> None:
        report = build_report("11HEAD0000H3ACXA", "13HEAD0000HFACXA")
        overall = report.overall(report.isomme_list[0])
        driver = overall.criterion_driver
        passenger = overall.criterion_passenger

        assert driver.dummy_type == DummyType.MALE_50TH.value
        assert passenger.dummy_type == DummyType.FEMALE_5TH.value
        assert threshold(driver.criterion_chest_deflection) == -63
        assert threshold(driver.criterion_neck_tension) == 4170
        assert threshold(driver.criterion_neck_compression) == -4000
        assert threshold(driver.criterion_femur_axial_force.criterion_right) == -10008

        driver_patterns = limit_patterns(driver)
        passenger_patterns = limit_patterns(passenger)
        assert driver_patterns
        assert passenger_patterns
        assert all("H3" in pattern for pattern in driver_patterns)
        assert all("HF" in pattern for pattern in passenger_patterns)

    def test_explicit_occupant_override_wins_over_detection(
        self, build_report: ReportFactory
    ) -> None:
        report = build_report("11HEAD0000HFACXA", "13HEAD0000HFACXA")
        driver = report.overall(report.isomme_list[0]).criterion_driver

        driver.dummy_type = DummyType.MALE_50TH.value
        driver.build_limits()

        assert threshold(driver.criterion_chest_deflection) == -63
        assert all("H3" in pattern for pattern in limit_patterns(driver))

    def test_containment_requires_positive_confirmation(
        self, build_report: ReportFactory
    ) -> None:
        report = build_report()
        containment = report.overall(
            report.isomme_list[0]
        ).criterion_driver.criterion_containment

        containment.calculate()
        assert containment.rating == 0.0

        containment.contained = True
        containment.calculate()
        assert containment.rating == 1.0
