from __future__ import annotations

import unittest

import pyisomme
from pyisomme.report.fmvss import DummyType, FMVSS_208


def threshold(criterion) -> float:
    return float(criterion.limits.limit_list[0].func(0.0))


def limit_patterns(criterion) -> list[str]:
    return [
        pattern
        for _, node in criterion.walk()
        for limit in node.limits.limit_list
        for pattern in limit.code_patterns or ()
    ]


class TestFMVSS208(unittest.TestCase):
    def build(self, *codes: str) -> FMVSS_208:
        isomme = pyisomme.Isomme(test_number="FMVSS-208")
        for code in codes:
            isomme.channels.append(pyisomme.create_sample(
                code,
                t_range=(-0.01, 0.01, 3),
                y_range=(0.0, 1.0),
                unit=pyisomme.Code(code).get_default_unit(),
            ))
        return FMVSS_208([isomme])

    def test_conservative_female_fallback_without_identifying_channels(self) -> None:
        report = self.build()
        occupant = report.overall(report.isomme_list[0]).criterion_driver

        self.assertEqual(occupant.dummy_type, DummyType.FEMALE_5TH.value)
        self.assertFalse(occupant.criterion_containment.contained)
        self.assertEqual(threshold(occupant.criterion_hic15), 700)
        self.assertEqual(threshold(occupant.criterion_chest_a3ms), 60)
        self.assertEqual(threshold(occupant.criterion_chest_deflection), -52)
        self.assertEqual(threshold(occupant.criterion_nij), 1.0)
        self.assertEqual(threshold(occupant.criterion_neck_tension), 2620)
        self.assertEqual(threshold(occupant.criterion_neck_compression), -2520)
        self.assertEqual(
            threshold(occupant.criterion_femur_axial_force.criterion_left), -6805
        )
        patterns = limit_patterns(occupant)
        self.assertTrue(patterns)
        self.assertTrue(all("HF" in pattern for pattern in patterns))

    def test_detects_mixed_driver_and_passenger_dummies(self) -> None:
        report = self.build("11HEAD0000H3ACXA", "13HEAD0000HFACXA")
        overall = report.overall(report.isomme_list[0])
        driver = overall.criterion_driver
        passenger = overall.criterion_passenger

        self.assertEqual(driver.dummy_type, DummyType.MALE_50TH.value)
        self.assertEqual(passenger.dummy_type, DummyType.FEMALE_5TH.value)
        self.assertEqual(threshold(driver.criterion_chest_deflection), -63)
        self.assertEqual(threshold(driver.criterion_neck_tension), 4170)
        self.assertEqual(threshold(driver.criterion_neck_compression), -4000)
        self.assertEqual(
            threshold(driver.criterion_femur_axial_force.criterion_right), -10008
        )
        driver_patterns = limit_patterns(driver)
        passenger_patterns = limit_patterns(passenger)
        self.assertTrue(driver_patterns)
        self.assertTrue(passenger_patterns)
        self.assertTrue(all("H3" in pattern for pattern in driver_patterns))
        self.assertTrue(all("HF" in pattern for pattern in passenger_patterns))

    def test_explicit_occupant_override_wins_over_detection(self) -> None:
        report = self.build("11HEAD0000HFACXA", "13HEAD0000HFACXA")
        driver = report.overall(report.isomme_list[0]).criterion_driver

        driver.dummy_type = DummyType.MALE_50TH.value
        driver.build_limits()

        self.assertEqual(threshold(driver.criterion_chest_deflection), -63)
        self.assertTrue(all("H3" in pattern for pattern in limit_patterns(driver)))

    def test_containment_requires_positive_confirmation(self) -> None:
        report = self.build()
        containment = report.overall(report.isomme_list[0]).criterion_driver.criterion_containment

        containment.calculate()
        self.assertEqual(containment.rating, 0.0)

        containment.contained = True
        containment.calculate()
        self.assertEqual(containment.rating, 1.0)


if __name__ == "__main__":
    unittest.main()
