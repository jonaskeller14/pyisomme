import pyisomme

import unittest
import os
import logging
import numpy as np
import pandas as pd


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
        assert iso.get_channel("?1HEADDAMA??AAX?") is not None
        assert iso.get_channel("?1HEADDAMA??AAY?") is not None
        assert iso.get_channel("?1HEADDAMA??AAZ?") is not None
        assert iso.get_channel("?1HEADDAMA??AAR?") is not None

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

        assert self.v1.get_channel("?1TIINLU00??000B") is not None
        assert self.v1.get_channel("?3TIINRL00??000B") is not None

        assert self.v1.get_channel("?1TIINL000??000B") is not None
        assert self.v1.get_channel("?1TIINR000??000B") is not None
        assert self.v1.get_channel("?1TIIN0U00??000B") is not None
        assert self.v1.get_channel("?1TIIN0L00??000B") is not None
        assert self.v1.get_channel("?1TIIN0000??000B") is not None

        assert self.v1.get_channel("?1TIINLUTO??000B") is not None
        assert self.v1.get_channel("?3TIINRLTO??000B") is not None

        assert self.v1.get_channel("?1TIINL0TO??000B") is not None
        assert self.v1.get_channel("?1TIINR0TO??000B") is not None
        assert self.v1.get_channel("?1TIIN0UTO??000B") is not None
        assert self.v1.get_channel("?1TIIN0LTO??000B") is not None
        assert self.v1.get_channel("?1TIIN00TO??000B") is not None

    def test_calculate_femur_impulse(self):
        channel = self.v1.get_channel("??FEMR??????FOZ?")
        if channel is None: raise Exception("Channel missing")
        assert pyisomme.calculate_femur_impulse(channel) is not None
        assert self.v1.get_channel("??KTHCLE????IMZX") is not None
        assert self.v1.get_channel("??KTHCRI????IMZX") is not None
        assert self.v1.get_channel("??KTHC00????IMZX") is not None

    def test_calculate_bric(self):
        time = [0.0, 0.01]
        # Distinct per-axis peaks so the result depends on all three inputs. This guards
        # the bug where av_y/av_z were read from c_av_x (BrIC computed from X alone): with
        # the dominant Y peak the correct BrIC is ~1.86, the X-only bug gives ~0.34.
        c_x = pyisomme.Channel(code="11HEAD000000AVXD", data=pd.DataFrame([10.0, 10.0], index=time), unit="rad/s")
        c_y = pyisomme.Channel(code="11HEAD000000AVYD", data=pd.DataFrame([10.0, 100.0], index=time), unit="rad/s")
        c_z = pyisomme.Channel(code="11HEAD000000AVZD", data=pd.DataFrame([10.0, 10.0], index=time), unit="rad/s")
        bric = pyisomme.calculate_bric(c_x, c_y, c_z)
        assert bric is not None
        assert bric.code.main_location == "BRIC"
        assert bric.get_data()[0] > 1.0

    def test_calculate_xms(self):
        time = [0.0, 0.001, 0.002, 0.003, 0.004]
        channel = pyisomme.Channel(code="11HEAD0000H3ACXA", data=pd.DataFrame([0.0, 1.0, 2.0, 3.0, 4.0], index=time), unit="g")
        xms = pyisomme.calculate_xms(channel, min_delta_t=1, method="S")
        assert xms.code.fine_location_2 == "1S"
        assert xms.code.filter_class == "X"
        assert xms.get_data()[0] >= 0

    def test_calculate_vc(self):
        time = [0.0, 0.01, 0.02, 0.03, 0.04]
        channel = pyisomme.Channel(code="11CHSTLE00WSDSXA", data=pd.DataFrame([0.01, 0.02, 0.03, 0.04, 0.05], index=time), unit="m")
        channel_vc, channel_vc_x = pyisomme.calculate_vc(channel)
        assert channel_vc.code.main_location == "VCCR"
        assert channel_vc_x.code.filter_class == "X"
        assert channel_vc.data.shape[0] == len(time)

    def test_calculate_olc(self):
        # A ~20 g sled pulse: the vehicle velocity drops from 15.6 m/s so the free-flying
        # occupant (held at v_0) travels far enough relative to it to complete both the
        # free-flight (65 mm) and restraining (235 mm) phases OLC requires.
        time = np.linspace(0.0, 0.15, 151)
        velocity = np.clip(15.6 - 200.0 * time, 0.0, None)
        channel = pyisomme.Channel(code="11CHST000000VEXA", data=pd.DataFrame(velocity, index=time), unit="m/s")
        olc, olc_visual = pyisomme.calculate_olc(channel)
        assert olc is not None
        assert olc_visual is not None
        assert olc.code.fine_location_1 == "0O"
        assert olc.code.fine_location_2 == "LC"
        assert olc.unit == pyisomme.g0

    def test_calculate_damage_direct(self):
        time = [0.0, 0.01, 0.02]
        c_x = pyisomme.Channel(code="11HEAD0000THAAXA", data=pd.DataFrame([0.0, 0.0, 0.0], index=time), unit="rad/s^2")
        c_y = pyisomme.Channel(code="11HEAD0000THAAYA", data=pd.DataFrame([0.0, 0.0, 0.0], index=time), unit="rad/s^2")
        c_z = pyisomme.Channel(code="11HEAD0000THAAZA", data=pd.DataFrame([0.0, 0.0, 0.0], index=time), unit="rad/s^2")
        damage = pyisomme.calculate_damage(c_x, c_y, c_z)
        assert len(damage) == 8
        assert damage[0].code.fine_location_1 == "DA"
        assert damage[-1].code.filter_class == "X"


if __name__ == '__main__':
    unittest.main()
