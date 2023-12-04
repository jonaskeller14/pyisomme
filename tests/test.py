import unittest
import sys
import os
import matplotlib.pyplot as plt
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
        limits = pyisomme.Limits(limits=[pyisomme.Limit(code_patterns=["11NECKUP????FOX?"], func=lambda x: 500, name="sdfsdf", color="yellow", linestyle="--"),
                                         pyisomme.Limit(code_patterns=["11NECKUP.*FOX[AB]"], func=lambda x: 500, name="sdfsdf", color="yellow", linestyle="--"),
                                         pyisomme.Limit(code_patterns=["11NECKUP????FOY?"], func=lambda x: 750 - 7.5*x, name="da", color="red", linestyle="-"), ])
        assert len(limits.get_limits("11NECKUP00H3FOXA")) == 2


class TestCalculate(unittest.TestCase):
    pass


class TestPlotting(unittest.TestCase):
    v1 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "11391"), "11NECKUP????FO??", "11TIBI*FO*")
    v2 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "14084"), "11NECKUP????FO??", "11TIBI*FO*")
    v3 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "14065"), "11NECKUP????FO??", "11TIBI*FO*")

    def test_plot_1(self):
        pyisomme.plot_1(
            [self.v1, self.v2, self.v3],
            "11NECKUP????FOX?",
            limits=pyisomme.Limits(limits=[ pyisomme.Limit(["11NECKUP????FOX?"], func=lambda x: 560, color="green", name="Good", upper=True),
                                            pyisomme.Limit(["11NECKUP????FOX?"], func=lambda x: 700, color="yellow", name="Acceptable", upper=True),
                                            pyisomme.Limit(["11NECKUP????FOX?"], func=lambda x: 840, color="orange", name="Marginal", upper=True),
                                            pyisomme.Limit(["11NECKUP????FOX?"], func=lambda x: 840, color="red", name="Poor", lower=True),]))
        plt.savefig(os.path.join(__file__, "..", "out", "TestPlotting_test_plot_1_1.jpg"))

    def test_plot_1_xyzr(self):
        pyisomme.plot_1_xyzr(
            [self.v1, self.v2, self.v3],
            "11NECKUP????FO??",
            limits=pyisomme.Limits(limits=[ pyisomme.Limit(["11NECKUP????FOX?"], func=lambda x: 560, color="green", name="Good", upper=True),
                                            pyisomme.Limit(["11NECKUP????FOX?"], func=lambda x: 700, color="yellow", name="Acceptable", upper=True),
                                            pyisomme.Limit(["11NECKUP????FOX?"], func=lambda x: 840, color="orange", name="Marginal", upper=True),
                                            pyisomme.Limit(["11NECKUP????FOX?"], func=lambda x: 840, color="red", name="Poor", lower=True),]))
        plt.savefig(os.path.join(__file__, "..", "out", "TestPlotting_test_plot_1_xyzr_1.jpg"))

    def test_plot_4x1_xyzr(self):
        pyisomme.plot_4x1_xyzr(
            [self.v1, self.v2, self.v3],
            "11NECKUP????FO??",
            limits=pyisomme.Limits(limits=[ pyisomme.Limit(["11NECKUP????FOX?"], func=lambda x: 560, color="green", name="Good", upper=True),
                                            pyisomme.Limit(["11NECKUP????FOX?"], func=lambda x: 700, color="yellow", name="Acceptable", upper=True),
                                            pyisomme.Limit(["11NECKUP????FOX?"], func=lambda x: 840, color="orange", name="Marginal", upper=True),
                                            pyisomme.Limit(["11NECKUP????FOX?"], func=lambda x: 840, color="red", name="Poor", lower=True),]))
        plt.savefig(os.path.join(__file__, "..", "out", "TestPlotting_test_plot_4x1_xyzr_1.jpg"))


if __name__ == '__main__':
    unittest.main()
