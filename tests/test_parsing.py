import pyisomme

import unittest
import os
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(format='%(module)-12s %(levelname)-8s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S', level=logging.WARNING)


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


if __name__ == '__main__':
    unittest.main()
