from __future__ import annotations

import unittest

import pandas as pd

from pyisomme.channel import Channel
from pyisomme.errors import Status
from pyisomme.isomme import Isomme
from pyisomme.report.iihs.frontal import _kth_demerits
from pyisomme.report.iihs.frontal_small_overlap import IIHS_Frontal_Small_Overlap
from pyisomme.report.iihs.limits import Limit_A, Limit_G, Limit_M, Limit_P
from pyisomme.report.iihs.frontal_moderate_overlap import IIHS_Frontal_Moderate_Overlap
from pyisomme.report.iihs.side_impact import IIHS_Side_Impact


class TestIIHSBoundaries(unittest.TestCase):
    def test_kth_force_impulse_corridors(self) -> None:
        self.assertEqual(_kth_demerits(5.22, 200.0), (0.0, Limit_G.color))
        self.assertEqual(_kth_demerits(5.69, 113.5), (0.0, Limit_G.color))
        self.assertEqual(_kth_demerits(5.70, 113.5), (-2.0, Limit_A.color))
        self.assertEqual(_kth_demerits(8.92, 137.1), (-6.0, Limit_M.color))
        self.assertEqual(_kth_demerits(8.93, 137.1), (-10.0, Limit_P.color))

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

        driver.criterion_chest.criterion_vc.calculation()
        driver.criterion_head_neck.criterion_shear_corridor.calculation()

        self.assertEqual(driver.criterion_chest.criterion_vc.rating, -10.0)
        self.assertEqual(driver.criterion_chest.criterion_vc.color, Limit_M.color)
        self.assertEqual(
            driver.criterion_head_neck.criterion_shear_corridor.rating, -2.0
        )
        self.assertEqual(
            driver.criterion_head_neck.criterion_shear_corridor.color, Limit_A.color
        )


class TestIIHSModerateOverlap(unittest.TestCase):
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
        criterion.calculation()

        self.assertEqual(criterion.value, 44.0)
        self.assertEqual(criterion.rating, -10.0)
        self.assertEqual(criterion.color, Limit_M.color)


class TestIIHSSideImpact(unittest.TestCase):
    def setUp(self) -> None:
        self.isomme = Isomme(test_number="side")
        self.report = IIHS_Side_Impact([self.isomme])

    def test_structure_boundaries_and_door_downgrade(self) -> None:
        criterion = self.report.overall(self.isomme).criterion_structure
        for distance, expected in (
            (18.01, 0.0),
            (18.0, -2.0),
            (14.0, -2.0),
            (13.9, -10.0),
            (10.0, -10.0),
            (9.9, -22.0),
        ):
            with self.subTest(distance=distance):
                criterion.b_pillar_to_seat_centerline_cm = distance
                criterion.door_opened = False
                criterion.integrity_failure = False
                criterion.calculation()
                self.assertEqual(criterion.rating, expected)

        criterion.b_pillar_to_seat_centerline_cm = 18.01
        criterion.door_opened = True
        criterion.calculation()
        self.assertEqual(criterion.rating, -2.0)

    def test_pelvis_requires_both_force_channels(self) -> None:
        self.isomme.channels.append(
            Channel(
                "11ACTBLE00S2FOYB",
                pd.DataFrame([3000.0], index=[0.0]),
                "N",
            )
        )
        criterion = self.report.overall(self.isomme).criterion_driver.criterion_pelvis

        criterion.calculate()

        self.assertIs(criterion.status, Status.NA)

    def test_head_protection_decision_logic(self) -> None:
        criterion = self.report.overall(
            self.isomme
        ).criterion_driver.criterion_head_protection

        criterion.interior_contact = True
        criterion.calculation()
        self.assertEqual(criterion.rating, -2.0)

        criterion.head_acceleration_over_70g = True
        criterion.calculation()
        self.assertEqual(criterion.rating, -10.0)

        criterion.direct_mdb_contact = True
        criterion.calculation()
        self.assertEqual(criterion.rating, -22.0)


if __name__ == "__main__":
    unittest.main()
