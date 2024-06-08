import pyisomme

import unittest
import os
import logging
import pandas as pd
import numpy as np


logger = logging.getLogger(__name__)
logging.basicConfig(format='%(module)-12s %(levelname)-8s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S', level=logging.INFO)


class TestUnit(unittest.TestCase):
    def test_unit(self):
        pyisomme.Unit("Nm")
        assert pyisomme.Unit("Nm") == pyisomme.Unit("N*m")
        pyisomme.Unit(1)
        pyisomme.Unit("1")
        pyisomme.Unit("")


class TestParsing(unittest.TestCase):
    def test_utf_8(self):
        iso = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "utf-8"))
        logger.info(iso.test_info)
        logger.info(iso.channel_info)
        logger.info(iso.channels)
        logger.info(iso.channels[0].info)
        assert len(iso.test_info) != 0
        assert len(iso.channel_info) != 0
        assert len(iso.channels) != 0
        assert len(iso.channels[0].info) != 0

    def test_ascii(self):
        iso = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "ascii"))
        logger.info(iso.test_info)
        logger.info(iso.channel_info)
        logger.info(iso.channels)
        logger.info(iso.channels[0].info)
        assert len(iso.test_info) != 0
        assert len(iso.channel_info) != 0
        assert len(iso.channels) != 0
        assert len(iso.channels[0].info) != 0

    def test_windows_1252(self):
        iso = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "windows-1252"))
        logger.info(iso.test_info)
        logger.info(iso.channel_info)
        logger.info(iso.channels)
        logger.info(iso.channels[0].info)
        assert len(iso.test_info) != 0
        assert len(iso.channel_info) != 0
        assert len(iso.channels) != 0
        assert len(iso.channels[0].info) != 0

    def test_iso_8859_1(self):
        iso = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "iso-8859-1"))
        logger.info(iso.test_info)
        logger.info(iso.channel_info)
        logger.info(iso.channels)
        logger.info(iso.channels[0].info)
        assert len(iso.test_info) != 0
        assert len(iso.channel_info) != 0
        assert len(iso.channels) != 0
        assert len(iso.channels[0].info) != 0

    def test_utf_8_zip(self):
        iso = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "utf-8.zip"))
        logger.info(iso.test_info)
        logger.info(iso.channel_info)
        logger.info(iso.channels)
        logger.info(iso.channels[0].info)
        assert len(iso.test_info) != 0
        assert len(iso.channel_info) != 0
        assert len(iso.channels) != 0
        assert len(iso.channels[0].info) != 0

    def test_ascii_zip(self):
        iso = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "ascii.zip"))
        logger.info(iso.test_info)
        logger.info(iso.channel_info)
        logger.info(iso.channels)
        logger.info(iso.channels[0].info)
        assert len(iso.test_info) != 0
        assert len(iso.channel_info) != 0
        assert len(iso.channels) != 0
        assert len(iso.channels[0].info) != 0

    def test_windows_1252_zip(self):
        iso = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "windows-1252.zip"))
        logger.info(iso.test_info)
        logger.info(iso.channel_info)
        logger.info(iso.channels)
        logger.info(iso.channels[0].info)
        assert len(iso.test_info) != 0
        assert len(iso.channel_info) != 0
        assert len(iso.channels) != 0
        assert len(iso.channels[0].info) != 0

    def test_iso_8859_1_zip(self):
        iso = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "iso-8859-1.zip"))
        logger.info(iso.test_info)
        logger.info(iso.channel_info)
        logger.info(iso.channels)
        logger.info(iso.channels[0].info)
        assert len(iso.test_info) != 0
        assert len(iso.channel_info) != 0
        assert len(iso.channels) != 0
        assert len(iso.channels[0].info) != 0


class TestIsomme(unittest.TestCase):
    def test_init(self):
        pyisomme.Isomme()
        pyisomme.Isomme(test_number="999", test_info={}, channels=[], channel_info={})

    def test_read(self):
        pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "11391"))
        pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "11391", "11391.mme"))
        pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "v11391ISO.zip"))

    def test_get_test_info(self):
        isomme = pyisomme.Isomme(test_info={"Laboratory test ref. number": "98/7707"})
        assert isomme.get_test_info("Laboratory test ref. number") == isomme.get_test_info("[XL]abo?atory * ref. number")
        assert isomme.get_test_info("Laboratory test ref. number") == isomme.get_test_info("[XL]abo.atory .* ref. number")

    def test_get_channel_info(self):
        isomme = pyisomme.Isomme(channel_info={"Laboratory test ref. number": "98/7707"})
        assert isomme.get_test_info("Laboratory test ref. number") == isomme.get_test_info("[XL]abo?atory * ref. number")
        assert isomme.get_test_info("Laboratory test ref. number") == isomme.get_test_info("[XL]abo.atory .* ref. number")

    def test_extend(self):
        isomme_1 = pyisomme.Isomme(channels=[pyisomme.Channel(code="11HEAD0000H3ACXA", data=None),
                                             pyisomme.Channel(code="11HEAD0000H3ACYA", data=None),])
        isomme_2 = pyisomme.Isomme(channels=[pyisomme.Channel(code="11HEAD0000H3ACZA", data=None),])
        isomme_1.extend(isomme_2)
        assert len(isomme_1.channels) == 3
        channel = pyisomme.Channel(code="13HEAD0000H3ACXA", data=None)
        isomme_1.extend(channel)
        assert len(isomme_1.channels) == 4
        channel_list = [pyisomme.Channel(code="13HEAD0000H3ACYA", data=None),
                        pyisomme.Channel(code="13HEAD0000H3ACZA", data=None)]
        isomme_1.extend(channel_list)
        assert len(isomme_1.channels) == 6


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


class TestChannel(unittest.TestCase):
    def test_init(self):
        pyisomme.Channel(code="11HEAD0000H3ACXP", data=None)

    def test_get_info(self):
        channel = pyisomme.Channel(code="11HEAD0000H3ACXP", data=None, info={"Time of first sample": -0.030399999})
        assert channel.get_info("Time of first sample") == channel.get_info("[XT]ime * f?rst sample")
        assert channel.get_info("Time of first sample") == channel.get_info("[XT]ime .* f.rst sample")


class TestLimits(unittest.TestCase):
    def test_get_limits(self):
        limits = pyisomme.Limits(limit_list=[pyisomme.Limit(code_patterns=["11NECKUP????FOX?"], func=lambda x: 500, name="sdfsdf", color="yellow", linestyle="--"),
                                             pyisomme.Limit(code_patterns=["11NECKUP.*FOX[AB]"], func=lambda x: 500, name="sdfsdf", color="yellow", linestyle="--"),
                                             pyisomme.Limit(code_patterns=["11NECKUP????FOY?"], func=lambda x: 750 - 7.5*x, name="da", color="red", linestyle="-"), ])
        assert len(limits.get_limits("11NECKUP00H3FOXA")) == 2


class TestCalculate(unittest.TestCase):
    v1 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "11391"), "??TIBI*")

    def test_calculate_tibia_index(self):
        # Repair wring data
        for channel in self.v1.channels:
            if channel.code.main_location == "TIBI" and channel.code.fine_location_3 == "00":
                channel.set_code(fine_location_3="H3")

        assert self.v1.get_channel("?1TIINLEUP??000B") is not None
        assert self.v1.get_channel("?3TIINRILO??000B") is not None


class TestReport(unittest.TestCase):
    v1 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "11391"), "?[013]*")
    v2 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "14084"), "?[013]*")
    v3 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "09203"), "?[013]*")

    def test_EuroNCAP_Frontal_50kmh(self):
        pyisomme.report.euro_ncap.frontal_50kmh.EuroNCAP_Frontal_50kmh([self.v1, self.v2]).calculate().export_pptx("out/EuroNCAP_Frontal_50kmh.pptx")

    def test_EuroNCAP_Frontal_MPDB(self):
        for channel in self.v3.channels:
            if channel.code.main_location == "TIBI" and channel.code.fine_location_3 in ("00", "??"):
                channel.set_code(fine_location_3="TH")
        pyisomme.report.euro_ncap.frontal_mpdb.EuroNCAP_Frontal_MPDB([self.v3, self.v2, self.v1]).calculate().export_pptx("out/EuroNCAP_Frontal_MPDB.pptx")

    def test_EuroNCAP_Side_Barrier(self):
        pyisomme.report.euro_ncap.side_barrier.EuroNCAP_Side_Barrier([self.v1]).calculate().export_pptx("out/EuroNCAP_Side_Barrier.pptx")

    def test_EuroNCAP_Side_Pole(self):
        pyisomme.report.euro_ncap.side_pole.EuroNCAP_Side_Pole([self.v1]).calculate().export_pptx("out/EuroNCAP_Side_Pole.pptx")


class TestPlotting(unittest.TestCase):
    v1 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "11391"), "11NECKUP????FO??", "11TIBI*FO*")
    v2 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "14084"), "11NECKUP????FO??", "11TIBI*FO*")
    v3 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "14065"), "11NECKUP????FO??", "11TIBI*FO*")


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
