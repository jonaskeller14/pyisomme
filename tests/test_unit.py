import pyisomme

import unittest
import logging


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


if __name__ == '__main__':
    unittest.main()
