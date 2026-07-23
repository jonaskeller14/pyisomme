import pyisomme

import unittest
import logging
import pandas as pd


logger = logging.getLogger(__name__)
logging.basicConfig(format='%(module)-12s %(levelname)-8s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S', level=logging.WARNING)


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


if __name__ == '__main__':
    unittest.main()
