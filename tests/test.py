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


class TestChannel(unittest.TestCase):
    pass


class TestCalculate(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
