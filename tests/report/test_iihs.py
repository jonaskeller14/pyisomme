from __future__ import annotations

import pandas as pd
import pytest

from pyisomme.channel import Channel
from pyisomme.errors import Status
from pyisomme.isomme import Isomme
from pyisomme.report.iihs.frontal import _kth_demerits
from pyisomme.report.iihs.frontal_moderate_overlap import IIHS_Frontal_Moderate_Overlap
from pyisomme.report.iihs.frontal_small_overlap import IIHS_Frontal_Small_Overlap
from pyisomme.report.iihs.limits import Limit_A, Limit_G, Limit_M, Limit_P
from pyisomme.report.iihs.side_impact import IIHS_Side_Impact
from pyisomme.report.page2 import ChannelPlotPage


class TestIIHSBoundaries:
    def test_kth_force_impulse_corridors(self) -> None:
        assert _kth_demerits(5.22, 200.0) == (0.0, Limit_G.color)
        assert _kth_demerits(5.69, 113.5) == (0.0, Limit_G.color)
        assert _kth_demerits(5.70, 113.5) == (-2.0, Limit_A.color)
        assert _kth_demerits(8.92, 137.1) == (-6.0, Limit_M.color)
        assert _kth_demerits(8.93, 137.1) == (-10.0, Limit_P.color)

    def test_symmetric_vc_and_shear_corridor_use_worst_side(self) -> None:
        isomme = Isomme(test_number="small")
        isomme.channels.extend(
            [
                Channel("11VCCR0000H3VEXC", pd.DataFrame([1.1], index=[0.0]), "m/s"),
                Channel("11NECKUP00H3FOXB", pd.DataFrame([4.0], index=[0.0]), "kN"),
            ]
        )
        report = IIHS_Frontal_Small_Overlap([isomme])
        driver = report.overall(isomme).criterion_driver

        vc_result = driver.criterion_chest.criterion_vc.calculation()
        shear_result = driver.criterion_head_neck.criterion_shear_corridor.calculation()

        assert vc_result.rating == -10.0
        assert vc_result.color == Limit_M.color
        assert shear_result.rating == -2.0
        assert shear_result.color == Limit_A.color

    def test_small_overlap_neck_pages_select_distinct_limit_groups(self) -> None:
        isomme = Isomme(test_number="small")
        report = IIHS_Frontal_Small_Overlap([isomme])
        head_neck = report.overall(isomme).criterion_driver.criterion_head_neck

        axial_page = next(
            page
            for page in report.available_pages
            if isinstance(page, ChannelPlotPage)
            and page.name == "Driver Neck Axial Load"
        )
        corridor_page = next(
            page
            for page in report.available_pages
            if isinstance(page, ChannelPlotPage)
            and page.name == "Driver Neck Load Corridors"
        )
        assert callable(axial_page.spec.limits)
        assert callable(corridor_page.spec.limits)

        axial_limits = axial_page.spec.limits(report)[isomme]
        corridor_limits = corridor_page.spec.limits(report)[isomme]

        assert axial_limits.limits == (
            head_neck.criterion_neck_tension.limits.limits
            + head_neck.criterion_neck_compression.limits.limits
        )
        assert corridor_limits.limits == (
            head_neck.criterion_tension_corridor.limits.limits
            + head_neck.criterion_compression_corridor.limits.limits
            + head_neck.criterion_shear_corridor.limits.limits
        )


class TestIIHSModerateOverlap:
    def test_chest_index_corrects_high_belt_position_and_floors(self) -> None:
        isomme = Isomme(test_number="moderate")
        isomme.channels.append(
            Channel(
                "16CHST0000HFDSXC",
                pd.DataFrame([-0.040], index=[0.0]),
                "m",
            )
        )
        report = IIHS_Frontal_Moderate_Overlap([isomme])
        criterion = report.overall(
            isomme
        ).criterion_rear_passenger.criterion_chest.criterion_chest_index

        criterion.dynamic_belt_position_mm = 37.0
        result = criterion.calculation()

        assert result.value == 44.0
        assert result.rating == -10.0
        assert result.color == Limit_M.color


class TestIIHSSideImpact:
    @pytest.fixture
    def setup_report(self) -> tuple[Isomme, IIHS_Side_Impact]:
        isomme = Isomme(test_number="side")
        report = IIHS_Side_Impact([isomme])
        return isomme, report

    @pytest.mark.parametrize(
        "distance, expected",
        [
            (18.01, 0.0),
            (18.0, -2.0),
            (14.0, -2.0),
            (13.9, -10.0),
            (10.0, -10.0),
            (9.9, -22.0),
        ],
    )
    def test_structure_boundaries(
        self, setup_report, distance: float, expected: float
    ) -> None:
        isomme, report = setup_report
        criterion = report.overall(isomme).criterion_structure
        criterion.b_pillar_to_seat_centerline_cm = distance
        criterion.door_opened = False
        criterion.integrity_failure = False
        result = criterion.calculation()

        assert result.rating == expected

    def test_door_downgrade(self, setup_report) -> None:
        isomme, report = setup_report
        criterion = report.overall(isomme).criterion_structure
        criterion.b_pillar_to_seat_centerline_cm = 18.01
        criterion.door_opened = True
        result = criterion.calculation()

        assert result.rating == -2.0

    def test_pelvis_requires_both_force_channels(self, setup_report) -> None:
        isomme, report = setup_report
        isomme.channels.append(
            Channel(
                "11ACTBLE00S2FOYB",
                pd.DataFrame([3000.0], index=[0.0]),
                "N",
            )
        )
        criterion = report.overall(isomme).criterion_driver.criterion_pelvis

        criterion.calculate()

        assert criterion.status is Status.NA

    def test_head_protection_decision_logic(self, setup_report) -> None:
        isomme, report = setup_report
        criterion = report.overall(isomme).criterion_driver.criterion_head_protection

        criterion.interior_contact = True
        result = criterion.calculation()
        assert result.rating == -2.0

        criterion.head_acceleration_over_70g = True
        result = criterion.calculation()
        assert result.rating == -10.0

        criterion.direct_mdb_contact = True
        result = criterion.calculation()
        assert result.rating == -22.0
