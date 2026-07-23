import pyisomme

import unittest
import os
import logging
import pandas as pd
import shutil


logger = logging.getLogger(__name__)
logging.basicConfig(format='%(module)-12s %(levelname)-8s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S', level=logging.WARNING)


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
        shutil.rmtree("out/write", ignore_errors=True)
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


if __name__ == '__main__':
    unittest.main()
