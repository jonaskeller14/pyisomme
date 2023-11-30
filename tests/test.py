import unittest
import sys
import os
sys.path.append(os.path.join(__file__, "..", ".."))
import pyisomme


class TestUnit(unittest.TestCase):
    def test_unit(self):
        pyisomme.Unit("Nm")


class TestIsomme(unittest.TestCase):
    def test_init(self):
        pyisomme.Isomme()
        pyisomme.Isomme(test_number="999", test_info={}, channels=[], channel_info={})

    def test_read(self):
        pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "iso-mme-org", "MME 1.6 Testdata short", "98_7707"))
        pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "iso-mme-org", "MME 1.6 Testdata short", "3239"))
        pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "iso-mme-org", "MME 1.6 Testdata short", "AK3T02FO"))
        pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "iso-mme-org", "MME 1.6 Testdata short", "AK3T02SI"))
        pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "iso-mme-org", "MME 1.6 Testdata short", "VW1FGS15"))

        pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "11391"))
        pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "14065"))
        pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "14084"))
        pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "14531"))
        pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "v11391ISO.zip"))
        pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "v14065ISO.zip"))
        pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "v14084ISO.zip"))
        pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "v14531ISO.zip"))

    def test_get_test_info(self):
        isomme = pyisomme.Isomme(test_info={"Laboratory test ref. number": "98/7707"})
        assert isomme.get_test_info("Laboratory test ref. number") == isomme.get_test_info("[XL]abo?atory * ref. number")
        assert isomme.get_test_info("Laboratory test ref. number") == isomme.get_test_info("[XL]abo.atory .* ref. number")

    def test_get_channel_info(self):
        isomme = pyisomme.Isomme(channel_info={"Laboratory test ref. number": "98/7707"})
        assert isomme.get_test_info("Laboratory test ref. number") == isomme.get_test_info("[XL]abo?atory * ref. number")
        assert isomme.get_test_info("Laboratory test ref. number") == isomme.get_test_info("[XL]abo.atory .* ref. number")


class TestChannel(unittest.TestCase):
    def test_init(self):
        pyisomme.Channel(code="11HEAD0000H3ACXP", data=None)

    def test_get_info(self):
        channel = pyisomme.Channel(code="11HEAD0000H3ACXP", data=None, info={"Time of first sample": -0.030399999})
        assert channel.get_info("Time of first sample") == channel.get_info("[XT]ime * f?rst sample")
        assert channel.get_info("Time of first sample") == channel.get_info("[XT]ime .* f.rst sample")


class TestLimits(unittest.TestCase):
    def test_get_limits(self):
        limits = pyisomme.Limits(limits=[pyisomme.Limit(code_patterns=["11NECKUP????FOX?"], points=((0,500),), name="sdfsdf", color="yellow", linestyle="--"),
                                         pyisomme.Limit(code_patterns=["11NECKUP.*FOX[AB]"], points=((0,500),), name="sdfsdf", color="yellow", linestyle="--"),
                                         pyisomme.Limit(code_patterns=["11NECKUP????FOY?"], points=((0,750),(100,0)), name="da", color="red", linestyle="-"), ])
        assert len(limits.get_limits("11NECKUP00H3FOXA")) == 2


class TestCalculate(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
