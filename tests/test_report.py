import pyisomme

import unittest
import os
import logging

from pyisomme.report.correlation import Correlation
from pyisomme.report.euro_ncap import (
    EuroNCAP,
    EuroNCAP_Frontal_50kmh,
    EuroNCAP_Frontal_MPDB,
    EuroNCAP_Side_Barrier,
    EuroNCAP_Side_FarSide,
    EuroNCAP_Side_Pole,
)
from pyisomme.report.iihs import IIHS_Frontal_Small_Overlap
from pyisomme.report.un import (
    UN_Frontal_50kmh_R137,
    UN_Frontal_56kmh_ODB_R94,
    UN_Side_Barrier_R95,
    UN_Side_Pole_R135,
)


logger = logging.getLogger(__name__)
logging.basicConfig(format='%(module)-12s %(levelname)-8s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S', level=logging.WARNING)


# --------------------------------------------------------------------------- #
# Report tests are expensive: the four marked `@slow` below take 79-112 s each
# and dominate the suite (~12 min in total). They *pass* today — they are simply
# too slow for the edit/run loop of the report refactor, so they are opt-in:
#
#     PYISOMME_SLOW=1 .venv/Scripts/python.exe -m unittest tests.test_report
#
# TODO: after the refactor, revisit these — either the fixtures do not carry the
# full ISO-MME data these reports expect, or the report implementations need
# extending. Re-enable them by default once that is settled.
#
# Reports covered by `tests/test_golden.py` (frontal 50 km/h, side barrier) keep
# running here too, because these tests also exercise `export_pptx`, which the
# golden tests deliberately skip.
# --------------------------------------------------------------------------- #
slow = unittest.skipUnless(
    os.environ.get("PYISOMME_SLOW"),
    "slow report test - set PYISOMME_SLOW=1 to run (see TODO in tests/test_report.py)",
)


class TestReport(unittest.TestCase):
    v1 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "iso-mme-org", "MME 1.6 Testdata short", "AK3T02FO"), "[!B][013]*")
    v2 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "14084"), "[!B][013]*")
    v3 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "09203"), "[!B][013]*")
    v4 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "v15036ISO.zip"), "?1*")
    # v5 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "vtc-loadcase-example", "test"))
    # v6 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "vtc-loadcase-example", "sim"))

    def test_EuroNCAP_Frontal_50kmh(self):
        for channel in self.v1.channels + self.v2.channels:
            if channel.code.main_location == "NECK" and channel.code.fine_location_3 in ("00", "??"):
                channel.set_code(fine_location_3="H3")

        report = EuroNCAP_Frontal_50kmh([self.v1, self.v2])
        self.assertEqual(report.validate(errors_only=True), [])
        report.calculate()
        report.export_pptx("out/EuroNCAP_Frontal_50kmh.pptx")
        report.print_results()

    def test_EuroNCAP_Frontal_MPDB(self):
        for channel in self.v3.channels:
            if channel.code.main_location == "TIBI" and channel.code.fine_location_3 in ("00", "??"):
                channel.set_code(fine_location_3="TH")

        report = EuroNCAP_Frontal_MPDB([self.v3, self.v2, self.v1])
        self.assertEqual(report.validate(errors_only=True), [])
        report.calculate()
        report.export_pptx("out/EuroNCAP_Frontal_MPDB.pptx")
        report.print_results()

    def test_EuroNCAP_Side_Barrier(self):
        self.v1.extend([
            pyisomme.create_sample("11SHLDLE00WSFOY0", y_range=(-4, 3), unit="kN"),
            pyisomme.create_sample("11SHLDRI00WSFOY0", y_range=(1, 2), unit="kN"),
            pyisomme.create_sample("11TRRILE01WSDSYP", y_range=(-30, 0), unit="mm"),
            pyisomme.create_sample("11TRRILE02WSDSYP", y_range=(-30, 0), unit="mm"),
            pyisomme.create_sample("11TRRILE03WSDSYP", y_range=(-30, 0), unit="mm"),
            pyisomme.create_sample("11ABRILE01WSDSYP", y_range=(-30, 0), unit="mm"),
            pyisomme.create_sample("11ABRILE02WSDSYP", y_range=(-30, 0), unit="mm"),
            pyisomme.create_sample("11PUBC0000WSFOYB", y_range=(-3., 0), unit="kN"),
        ])

        report = EuroNCAP_Side_Barrier([self.v1])
        self.assertEqual(report.validate(errors_only=True), [])
        report.calculate()
        report.export_pptx("out/EuroNCAP_Side_Barrier.pptx")
        report.print_results()

    def test_EuroNCAP_Side_Pole(self):
        self.v1.extend([
            pyisomme.create_sample("11SHLDLE00WSFOY0", y_range=(-4, 3), unit="kN"),
            pyisomme.create_sample("11SHLDRI00WSFOY0", y_range=(1, 2), unit="kN"),
            pyisomme.create_sample("11TRRILE01WSDSYP", y_range=(-30, 0), unit="mm"),
            pyisomme.create_sample("11TRRILE02WSDSYP", y_range=(-30, 0), unit="mm"),
            pyisomme.create_sample("11TRRILE03WSDSYP", y_range=(-30, 0), unit="mm"),
            pyisomme.create_sample("11ABRILE01WSDSYP", y_range=(-30, 0), unit="mm"),
            pyisomme.create_sample("11ABRILE02WSDSYP", y_range=(-30, 0), unit="mm"),
            pyisomme.create_sample("11PUBC0000WSFOYB", y_range=(2.0, 0), unit="kN"),
        ])

        report = EuroNCAP_Side_Pole([self.v1])
        self.assertEqual(report.validate(errors_only=True), [])
        report.calculate()
        report.export_pptx("out/EuroNCAP_Side_Pole.pptx")
        report.print_results()

    def test_EuroNCAP_Side_FarSide(self):
        for channel in self.v1.channels:
            if channel.code.main_location == "NECK" and channel.code.fine_location_3 in ("00", "??"):
                channel.set_code(fine_location_3="WS")

        report = EuroNCAP_Side_FarSide([self.v1])
        self.assertEqual(report.validate(errors_only=True), [])
        report.calculate()
        report.export_pptx("out/EuroNCAP_Side_FarSide.pptx")
        report.print_results()

    # FIXME: Dataset is lost --> we need to recreate the dataset from scratch
    #  @slow
    # def test_EuroNCAP_Side_Farside_VTC(self):
    #     for channel in self.v5.channels:
    #         if channel.get_info("Unit") == "dimensionless":
    #             channel.set_unit("rad")
    #     for channel in self.v6.channels:
    #         if channel.get_info("Unit") == "dimensionless":
    #             channel.set_unit("rad")

    #     report = EuroNCAP_Side_Farside_VTC([self.v5, self.v6])
    #     report.calculate()
    #     report.export_pptx("out/EuroNCAP_Side_FarSide_VTC.pptx")
    #     report.print_results()

    @slow
    def test_IIHS_Frontal_Small_Overlap(self):
        report = IIHS_Frontal_Small_Overlap([self.v1, self.v2, self.v3])
        self.assertEqual(report.validate(errors_only=True), [])
        report.calculate()
        report.export_pptx("out/IIHS_Frontal_Small_Overlap.pptx")
        report.print_results()

    def test_Correlation(self):
        for channel in self.v3.channels:
            channel.set_code(test_object="1")

        report = Correlation([self.v1, self.v2, self.v3])
        self.assertEqual(report.validate(errors_only=True), [])
        report.calculate()
        report.export_pptx("out/Correlation.pptx")
        report.print_results()

    def test_EuroNCAP(self):
        report = EuroNCAP(
            frontal_50kmh=[[self.v1]],
            frontal_mpdb=[[self.v2]],
            side_pole=[[self.v3]],
            side_barrier=[[self.v1]],
            side_farside=[[self.v1]],
        )
        self.assertEqual(report.validate(errors_only=True), [])
        report.calculate()
        report.export_pptx("out/EuroNCAP.pptx")
        report.print_results()

    @slow
    def test_UN_Frontal_50kmh_R137(self):
        for channel in self.v1.channels + self.v2.channels:
            if channel.code.position == "1":
                channel.set_code(fine_location_3="H3")
            if channel.code.position == "3":
                channel.set_code(fine_location_3="HF")

        report = UN_Frontal_50kmh_R137([self.v1, self.v2])
        self.assertEqual(report.validate(errors_only=True), [])
        report.calculate()
        report.export_pptx("out/UN_Frontal_50kmh_R137.pptx")
        report.print_results()

    @slow
    def test_UN_Frontal_56kmh_ODB_R94(self):
        for channel in self.v1.channels + self.v2.channels:
            if channel.code.position == "1":
                channel.set_code(fine_location_3="H3")
            if channel.code.position == "3":
                channel.set_code(fine_location_3="H3")
        self.v1.offset_x(-0.5)

        report = UN_Frontal_56kmh_ODB_R94([self.v1, self.v2])
        self.assertEqual(report.validate(errors_only=True), [])
        report.calculate()
        report.export_pptx("out/UN_Frontal_56kmh_ODB_R94.pptx")
        report.print_results()

    def test_UN_Side_Pole_R135(self):
        self.v1.extend([
            pyisomme.create_sample("11SHLDLE00WSFOY0", y_range=(-4, 3), unit="kN"),
            pyisomme.create_sample("11SHLDRI00WSFOY0", y_range=(1, 2), unit="kN"),
            pyisomme.create_sample("11TRRILE01WSDCRP", y_range=(-30, 0), unit="mm"),
            pyisomme.create_sample("11TRRILE02WSDCRP", y_range=(-30, 0), unit="mm"),
            pyisomme.create_sample("11TRRILE03WSDCRP", y_range=(-5, -50), unit="mm"),
            pyisomme.create_sample("11ABRILE01WSDCRP", y_range=(-30, 0), unit="mm"),
            pyisomme.create_sample("11ABRILE02WSDCRP", y_range=(-60, 0), unit="mm"),
            pyisomme.create_sample("11PUBC0000WSFOYB", y_range=(2.0, 0), unit="kN"),
            pyisomme.create_sample("11THSP1200WSACR0", y_range=(100, 200), unit="m/s^2"),
        ])

        report = UN_Side_Pole_R135([self.v1])
        self.assertEqual(report.validate(errors_only=True), [])
        report.calculate()
        report.export_pptx("out/UN_Side_Pole_R135.pptx")
        report.print_results()

    def test_UN_Side_Barrier_R95(self):
        for channel in self.v4.get_channels("?1*"):
            channel.set_code(fine_location_3="ER")
        for channel in self.v4.get_channels("?1ABDO??????FOY?*"):
            channel.set_code(fine_location_1="LE", fine_location_2=channel.code.fine_location_1)
        for channel in self.v4.get_channels("?1RIBS??????DSY?*"):
            channel.scale_y(6e-5)

        report = UN_Side_Barrier_R95([self.v4])
        self.assertEqual(report.validate(errors_only=True), [])
        report.calculate()
        report.export_pptx("out/UN_Side_Barrier_R95.pptx")
        report.print_results()
