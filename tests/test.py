import pyisomme

import unittest
import os
import logging
import pandas as pd
import numpy as np
import shutil


logger = logging.getLogger(__name__)
logging.basicConfig(format='%(module)-12s %(levelname)-8s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S', level=logging.WARNING)


class TestUnit(unittest.TestCase):
    def test_unit(self):
        pyisomme.Unit("Nm")
        assert pyisomme.Unit("Nm") == pyisomme.Unit("N*m")
        pyisomme.Unit(1)
        pyisomme.Unit("1")
        pyisomme.Unit("")
        assert pyisomme.Unit("°C") == pyisomme.Unit("Celsius") == pyisomme.Unit("deg_C")
        assert pyisomme.Unit("°") == pyisomme.Unit("deg")
        assert pyisomme.Unit("°/s2") == pyisomme.Unit("deg/s^2")
        assert pyisomme.Unit("°/s") == pyisomme.Unit("deg/s")
        assert pyisomme.Unit(pyisomme.Unit("m")) == pyisomme.Unit("m")


class TestParsing(unittest.TestCase):
    def check_if_isomme_not_empty(self, isomme):
        logger.info(isomme.test_info)
        logger.info(isomme.channel_info)
        logger.info(isomme.channels)
        logger.info(isomme.channels[0].info)
        assert len(isomme.test_info) != 0
        assert len(isomme.channel_info) != 0
        assert len(isomme.channels) != 0
        assert len(isomme.channels[0].info) != 0

    def test_utf_8(self):
        isomme = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "utf-8"))
        self.check_if_isomme_not_empty(isomme)

    def test_ascii(self):
        isomme = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "ascii"))
        self.check_if_isomme_not_empty(isomme)

    def test_windows_1252(self):
        isomme = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "windows-1252"))
        self.check_if_isomme_not_empty(isomme)

    def test_iso_8859_1(self):
        isomme = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "iso-8859-1"))
        self.check_if_isomme_not_empty(isomme)

    def test_utf_8_zip(self):
        isomme = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "utf-8.zip"))
        self.check_if_isomme_not_empty(isomme)

    def test_ascii_zip(self):
        isomme = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "ascii.zip"))
        self.check_if_isomme_not_empty(isomme)

    def test_windows_1252_zip(self):
        isomme = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "windows-1252.zip"))
        self.check_if_isomme_not_empty(isomme)

    def test_iso_8859_1_zip(self):
        isomme = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "iso-8859-1.zip"))
        self.check_if_isomme_not_empty(isomme)


class TestIsomme(unittest.TestCase):
    def test_init(self):
        pyisomme.Isomme()
        pyisomme.Isomme(test_number="999", test_info=[], channels=[], channel_info=[])

    def test_read(self):
        pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "11391"), "11HEAD??????ACX?")
        pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "11391", "11391.mme"), "11HEAD??????ACX?")
        pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "v11391ISO.zip"), "11HEAD??????ACX?")
        pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "11391", "Channel", "11391.chn"), "11HEAD??????ACX?")
        pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "11391", "Channel", "11391.001"), "11HEAD??????ACX?")
        pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "11391.tar"), "11HEAD??????ACX?")
        pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "11391.tar.gz"), "11HEAD??????ACX?")

    def test_write(self):
        isomme = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "11391"), "11HEAD*")
        shutil.rmtree("out/write")
        isomme.write("out/write/01/v11391.mme")
        isomme.write("out/write/02/v11391.zip")
        isomme.write("out/write/03/v11391")
        isomme.write("out/write/04/v11391.mme", "11HEAD??????ACX?")

    def test_get_test_info(self):
        isomme = pyisomme.Isomme(test_info=[("Laboratory test ref. number", "98/7707")])
        assert isomme.get_test_info("Laboratory test ref. number") == isomme.get_test_info("[XL]abo?atory * ref. number")
        assert isomme.get_test_info("Laboratory test ref. number") == isomme.get_test_info("[XL]abo.atory .* ref. number")

    def test_get_channel_info(self):
        isomme = pyisomme.Isomme(channel_info=[("Laboratory test ref. number", "98/7707")])
        assert isomme.get_test_info("Laboratory test ref. number") == isomme.get_test_info("[XL]abo?atory * ref. number")
        assert isomme.get_test_info("Laboratory test ref. number") == isomme.get_test_info("[XL]abo.atory .* ref. number")

    def test_extend(self):
        isomme_1 = pyisomme.Isomme(channels=[pyisomme.Channel(code="11HEAD0000H3ACXA", data=pd.DataFrame([])),
                                             pyisomme.Channel(code="11HEAD0000H3ACYA", data=pd.DataFrame([])),])
        isomme_2 = pyisomme.Isomme(channels=[pyisomme.Channel(code="11HEAD0000H3ACZA", data=pd.DataFrame([])),])
        isomme_1.extend(isomme_2)
        assert len(isomme_1.channels) == 3
        channel = pyisomme.Channel(code="13HEAD0000H3ACXA", data=pd.DataFrame([]))
        isomme_1.extend(channel)
        assert len(isomme_1.channels) == 4
        channel_list = [pyisomme.Channel(code="13HEAD0000H3ACYA", data=pd.DataFrame([])),
                        pyisomme.Channel(code="13HEAD0000H3ACZA", data=pd.DataFrame([]))]
        isomme_1.extend(channel_list)
        assert len(isomme_1.channels) == 6

    def test_delete_duplicates(self):
        isomme = pyisomme.Isomme(channels=[
            pyisomme.Channel(code="11HEAD0000H3ACXA", data=pd.DataFrame([1])),
            pyisomme.Channel(code="11HEAD0000H3ACYA", data=pd.DataFrame([2])),
            pyisomme.Channel(code="11HEAD0000H3ACZA", data=pd.DataFrame([3])),
            pyisomme.Channel(code="11HEAD0000H3ACXA", data=pd.DataFrame([4])),
            pyisomme.Channel(code="11HEAD0000H3ACX0", data=pd.DataFrame([5])),
            pyisomme.Channel(code="11HEAD0000H3ACXP", data=pd.DataFrame([6])),
        ])
        isomme.delete_duplicates()
        assert len(isomme.channels) == 5
        isomme.delete_duplicates(filter_class_duplicates=True)
        assert len(isomme.channels) == 3 and "11HEAD0000H3ACX0" in [c.code for c in isomme.channels]


class TestCode(unittest.TestCase):
    def test_init(self):
        pyisomme.Code("11HEAD0000H3ACXA")

        # 15 chars
        with self.assertRaises(AssertionError):
            pyisomme.Code("11HEAD0000H3ACX")
        # 17 chars
        with self.assertRaises(AssertionError):
            pyisomme.Code("11HEAD0000H3ACXA?")
        # invalid chars
        with self.assertRaises(AssertionError):
            pyisomme.Code("11HEAD0000H3ACX*")

    def test_combine_codes(self):
        assert pyisomme.code.combine_codes("11HEAD0000H3ACXA", "11HEAD0000H3ACXB") == "11HEAD0000H3ACX?"
        assert pyisomme.code.combine_codes("11HEAD0000H3ACXA", "11HEAD0000H3ACXB", "11HEAD0000H3DSXB", "11HEAD0000H3ACXA") == "11HEAD0000H3??X?"


class TestChannel(unittest.TestCase):
    def test_init(self):
        pyisomme.Channel(code="11HEAD0000H3ACXP", data=pd.DataFrame([]))
        # < 16 chars
        pyisomme.Channel(code="11HEAD0000H3", data=pd.DataFrame([]))
        # > 16 chars
        pyisomme.Channel(code="11HEAD0000H3ACXP123", data=pd.DataFrame([]))
        # invalid chars
        pyisomme.Channel(code="TOTAL_ENERGY", data=pd.DataFrame([]))

    def test_get_info(self):
        channel = pyisomme.Channel(code="11HEAD0000H3ACXP",
                                   data=pd.DataFrame([]),
                                   info=[("Time of first sample", -0.030399999)])
        assert channel.get_info("Time of first sample") == channel.get_info("[XT]ime * f?rst sample")
        assert channel.get_info("Time of first sample") == channel.get_info("[XT]ime .* f.rst sample")

    def test_eq(self):
        c_1 = pyisomme.Channel(code="????????????????", data=pd.DataFrame([1]), unit="m")
        c_2 = pyisomme.Channel(code="????????????????", data=pd.DataFrame([1000]), unit="mm")

        self.assertTrue(c_1 == c_2)

    def test_ne(self):
        c_1 = pyisomme.Channel(code="????????????????", data=pd.DataFrame([1]), unit="m")
        c_2 = pyisomme.Channel(code="????????????????", data=pd.DataFrame([1]), unit="mm")

        self.assertTrue(c_1 != c_2)

    def test_add(self):
        c_1 = pyisomme.Channel(code="????????????????", data=pd.DataFrame([1]), unit="m")
        c_2 = pyisomme.Channel(code="????????????????", data=pd.DataFrame([1000]), unit="mm")

        self.assertEqual((c_1 + c_2).get_data(unit="m"), 2)
        self.assertEqual((c_1 + 1).get_data(unit="m"), 2)

    def test_sub(self):
        c_1 = pyisomme.Channel(code="????????????????", data=pd.DataFrame([1]), unit="m")
        c_2 = pyisomme.Channel(code="????????????????", data=pd.DataFrame([1000]), unit="mm")

        self.assertEqual((c_1 - c_2).get_data(unit="m"), 0)
        self.assertEqual((c_1 - 1).get_data(unit="m"), 0)


class TestLimits(unittest.TestCase):
    def test_get_limits(self):
        limits = pyisomme.Limits(limit_list=[pyisomme.Limit(code_patterns=["11NECKUP????FOX?"], func=lambda x: 500, name="sdfsdf", color="yellow", linestyle="--"),
                                             pyisomme.Limit(code_patterns=["11NECKUP.*FOX[AB]"], func=lambda x: 500, name="sdfsdf", color="yellow", linestyle="--"),
                                             pyisomme.Limit(code_patterns=["11NECKUP????FOY?"], func=lambda x: 750 - 7.5*x, name="da", color="red", linestyle="-"), ])
        assert len(limits.find_limits("11NECKUP00H3FOXA")) == 2


class TestCalculate(unittest.TestCase):
    v1 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "11391"), "??TIBI*", "??FEMR*")

    def test_calculate_damage(self):
        iso = pyisomme.Isomme(test_number="1234")
        iso.add_sample_channel(code="11HEAD0000THAAXP", unit="rad/s^2", y_range=[0, 8e5])
        iso.add_sample_channel(code="11HEAD0000THAAYP", unit="rad/s^2", y_range=[0, 5e5])
        iso.add_sample_channel(code="11HEAD0000THAAZP", unit="rad/s^2", y_range=[0, 3e5])
        assert iso.get_channel(f"?1HEADDAMA??AAX?") is not None
        assert iso.get_channel(f"?1HEADDAMA??AAY?") is not None
        assert iso.get_channel(f"?1HEADDAMA??AAZ?") is not None
        assert iso.get_channel(f"?1HEADDAMA??AAR?") is not None

    def test_calculate_neck_MOCx(self):
        v1 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "11391"), "??NECK*")
        for channel in v1:
            channel.set_code(fine_location_3="WS")

        assert v1.get_channel("??TMONUP????MOXB") is not None
        assert v1.get_channel("??TMONUP????MOXX") is not None

    def test_calculate_neck_MOCy(self):
        v1 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "11391"), "??NECK*")
        for channel in v1:
            channel.set_code(fine_location_3="WS")

        assert v1.get_channel("??TMONUP????MOYB") is not None
        assert v1.get_channel("??TMONUP????MOYX") is not None

    def test_calculate_chest_pc_score(self):
        iso = pyisomme.Isomme(test_number="1234")
        iso.add_sample_channel(code="11CHSTLEUPTHDSRA", unit="mm", y_range=[0, -20])
        iso.add_sample_channel(code="11CHSTRIUPTHDSRA", unit="mm", y_range=[0, -20])
        iso.add_sample_channel(code="11CHSTLELOTHDSRA", unit="mm", y_range=[0, -20])
        iso.add_sample_channel(code="11CHSTRILOTHDSRA", unit="mm", y_range=[0, -20])
        channel = iso.get_channel("11CHST00PCTHDSRA")
        assert channel is not None
        assert channel.code == "11CHST00PCTHDSRA"

    def test_calculate_tibia_index(self):
        # Repair wring data
        for channel in self.v1.channels:
            if channel.code.main_location == "TIBI" and channel.code.fine_location_3 == "00":
                channel.set_code(fine_location_3="H3")

        assert self.v1.get_channel("?1TIINLEUP??000B") is not None
        assert self.v1.get_channel("?3TIINRILO??000B") is not None

    def test_calculate_femur_impulse(self):
        assert pyisomme.calculate_femur_impulse(self.v1.get_channel("??FEMR??????FOZ?")) is not None
        assert self.v1.get_channel("??KTHCLE????IMZX") is not None
        assert self.v1.get_channel("??KTHCRI????IMZX") is not None
        assert self.v1.get_channel("??KTHC00????IMZX") is not None

class TestReport(unittest.TestCase):
    v1 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "11391"), "[!B][013]*")
    v2 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "14084"), "[!B][013]*")
    v3 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "09203"), "[!B][013]*")

    def test_EuroNCAP_Frontal_50kmh(self):
        for channel in self.v1.channels + self.v2.channels:
            if channel.code.main_location == "NECK" and channel.code.fine_location_3 in ("00", "??"):
                channel.set_code(fine_location_3="H3")

        report = pyisomme.report.euro_ncap.frontal_50kmh.EuroNCAP_Frontal_50kmh([self.v1, self.v2])
        report.calculate()
        report.export_pptx("out/EuroNCAP_Frontal_50kmh.pptx")
        report.print_results()

    def test_EuroNCAP_Frontal_MPDB(self):
        for channel in self.v3.channels:
            if channel.code.main_location == "TIBI" and channel.code.fine_location_3 in ("00", "??"):
                channel.set_code(fine_location_3="TH")

        report = pyisomme.report.euro_ncap.frontal_mpdb.EuroNCAP_Frontal_MPDB([self.v3, self.v2, self.v1])
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

        report = pyisomme.report.euro_ncap.side_barrier.EuroNCAP_Side_Barrier([self.v1])
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

        report = pyisomme.report.euro_ncap.side_pole.EuroNCAP_Side_Pole([self.v1])
        report.calculate()
        report.export_pptx("out/EuroNCAP_Side_Pole.pptx")
        report.print_results()

    def test_EuroNCAP_Side_FarSide(self):
        for channel in self.v1.channels:
            if channel.code.main_location == "NECK" and channel.code.fine_location_3 in ("00", "??"):
                channel.set_code(fine_location_3="WS")

        report = pyisomme.report.euro_ncap.EuroNCAP_Side_FarSide([self.v1])
        report.calculate()
        report.export_pptx("out/EuroNCAP_Side_FarSide.pptx")
        report.print_results()

    def test_EuroNCAP(self):
        report = pyisomme.report.euro_ncap.euro_ncap.EuroNCAP(
            frontal_50kmh=[[self.v1]],
            frontal_mpdb=[[self.v2]],
            side_pole=[[self.v3]],
            side_barrier=[[self.v1]],
        )
        report.calculate()
        report.export_pptx("out/EuroNCAP.pptx")
        report.print_results()

    def test_UN_Frontal_50kmh_R137(self):
        for channel in self.v1.channels + self.v2.channels:
            if channel.code.position == "1":
                channel.set_code(fine_location_3="H3")
            if channel.code.position == "3":
                channel.set_code(fine_location_3="HF")

        report = pyisomme.report.un.frontal_50kmh_r137.UN_Frontal_50kmh_R137([self.v1, self.v2])
        report.calculate()
        report.export_pptx("out/UN_Frontal_50kmh_R137.pptx")
        report.print_results()

    def test_UN_Frontal_56kmh_ODB_R94(self):
        for channel in self.v1.channels + self.v2.channels:
            if channel.code.position == "1":
                channel.set_code(fine_location_3="H3")
            if channel.code.position == "3":
                channel.set_code(fine_location_3="H3")

        report = pyisomme.report.un.frontal_56kmh_odb_r94.UN_Frontal_56kmh_ODB_R94([self.v1, self.v2])
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

        report = pyisomme.report.un.side_pole_r135.UN_Side_Pole_R135([self.v1])
        report.calculate()
        report.export_pptx("out/UN_Side_Pole_R135.pptx")
        report.print_results()

class TestPlotting(unittest.TestCase):
    pass


class TestCorrelation(unittest.TestCase):
    def test_correlation(self):
        reference_channel = pyisomme.create_sample(t_range=(0, 0.1, 1000), y_range=(0, 10))
        comparison_channel = pyisomme.create_sample(t_range=(0, 0.11, 1000), y_range=(0, 11))
        correlation = pyisomme.Correlation_ISO18571(reference_channel, comparison_channel)
        logger.info(f"Correlation overall rating: {correlation.overall_rating()}")

    def test_correlation2(self):
        time = np.arange(0, 0.150, 0.0001)
        reference = np.sin(time * 20)
        comparison = np.sin(time * 20) * 1.3 + 0.00

        reference_channel = pyisomme.Channel(code="????????????????",
                                             data=pd.DataFrame(reference, index=time))
        comparison_channel = pyisomme.Channel(code="????????????????",
                                              data=pd.DataFrame(comparison, index=time))

        correlation = pyisomme.Correlation_ISO18571(reference_channel, comparison_channel)
        overall_rating = correlation.overall_rating()
        assert np.abs(overall_rating - 0.713) < 1e-6
        logger.info(f"Correlation Overall Rating {correlation.overall_rating()}")


if __name__ == '__main__':
    unittest.main()
