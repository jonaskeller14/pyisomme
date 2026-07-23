import unittest
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(format='%(module)-12s %(levelname)-8s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S', level=logging.WARNING)


class TestPlotting(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
