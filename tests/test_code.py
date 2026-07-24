import pyisomme
from pyisomme.errors import InvalidCodeError

import unittest
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(format='%(module)-12s %(levelname)-8s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S', level=logging.WARNING)


class TestCode(unittest.TestCase):
    def test_init(self):
        pyisomme.Code("11HEAD0000H3ACXA")

        # 15 chars
        with self.assertRaises(InvalidCodeError):
            pyisomme.Code("11HEAD0000H3ACX")
        # 17 chars
        with self.assertRaises(InvalidCodeError):
            pyisomme.Code("11HEAD0000H3ACXA?")
        # invalid chars
        with self.assertRaises(InvalidCodeError):
            pyisomme.Code("11HEAD0000H3ACX*")

    def test_combine_codes(self):
        assert pyisomme.code.combine_codes("11HEAD0000H3ACXA", "11HEAD0000H3ACXB") == "11HEAD0000H3ACX?"
        assert pyisomme.code.combine_codes("11HEAD0000H3ACXA", "11HEAD0000H3ACXB", "11HEAD0000H3DSXB", "11HEAD0000H3ACXA") == "11HEAD0000H3??X?"


if __name__ == '__main__':
    unittest.main()
