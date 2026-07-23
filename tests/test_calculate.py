import pyisomme

import unittest
import os
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(format='%(module)-12s %(levelname)-8s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S', level=logging.WARNING)


class TestCalculate(unittest.TestCase):
    v1 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "11391"), "??TIBI*", "??FEMR*")

    def test_calculate_damage(self):
        iso = pyisomme.Isomme(test_number="1234")
        iso.add_sample_channel(code="11HEAD0000THAAXP", unit="rad/s^2", y_range=[0, 8e5])
        iso.add_sample_channel(code="11HEAD0000THAAYP", unit="rad/s^2", y_range=[0, 5e5])
        iso.add_sample_channel(code="11HEAD0000THAAZP", unit="rad/s^2", y_range=[0, 3e5])
        assert iso.get_channel(f"?1HEADDAMA??AAX?") is not None
        assert iso.get_channel(f"?1HEADDAMA??AAY?") is not None
        assert iso.get_channel(f"?1HEADDAMA??AAZ?") is not None
        assert iso.get_channel(f"?1HEADDAMA??AAR?") is not None

    def test_calculate_neck_MOCx(self):
        v1 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "11391"), "??NECK*")
        for channel in v1:
            channel.set_code(fine_location_3="WS")

        assert v1.get_channel("??TMONUP????MOXB") is not None
        assert v1.get_channel("??TMONUP????MOXX") is not None

    def test_calculate_neck_MOCy(self):
        v1 = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "nhtsa", "11391"), "??NECK*")
        for channel in v1:
            channel.set_code(fine_location_3="WS")

        assert v1.get_channel("??TMONUP????MOYB") is not None
        assert v1.get_channel("??TMONUP????MOYX") is not None

    def test_calculate_chest_pc_score(self):
        iso = pyisomme.Isomme(test_number="1234")
        iso.add_sample_channel(code="11CHSTLEUPTHDSRA", unit="mm", y_range=[0, -20])
        iso.add_sample_channel(code="11CHSTRIUPTHDSRA", unit="mm", y_range=[0, -20])
        iso.add_sample_channel(code="11CHSTLELOTHDSRA", unit="mm", y_range=[0, -20])
        iso.add_sample_channel(code="11CHSTRILOTHDSRA", unit="mm", y_range=[0, -20])
        channel = iso.get_channel("11CHST00PCTHDSRA")
        assert channel is not None
        assert channel.code == "11CHST00PCTHDSRA"

    def test_calculate_tibia_index(self):
        # Repair wring data
        for channel in self.v1.channels:
            if channel.code.main_location == "TIBI" and channel.code.fine_location_3 == "00":
                channel.set_code(fine_location_3="H3")

        assert self.v1.get_channel("?1TIINLEUP??000B") is not None
        assert self.v1.get_channel("?3TIINRILO??000B") is not None

    def test_calculate_femur_impulse(self):
        assert pyisomme.calculate_femur_impulse(self.v1.get_channel("??FEMR??????FOZ?")) is not None
        assert self.v1.get_channel("??KTHCLE????IMZX") is not None
        assert self.v1.get_channel("??KTHCRI????IMZX") is not None
        assert self.v1.get_channel("??KTHC00????IMZX") is not None


if __name__ == '__main__':
    unittest.main()
