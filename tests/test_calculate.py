import pyisomme

import unittest
import logging
import numpy as np
import pandas as pd


logger = logging.getLogger(__name__)
logging.basicConfig(format='%(module)-12s %(levelname)-8s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S', level=logging.WARNING)


CRASH_TIME_RANGE = (-0.05, 0.3, 7001)


def add_crash_channel(isomme, code, unit, peak, noise, frequency, seed):
    """Add a deterministic pulse modelled on the corresponding NHTSA 11391 signal."""
    isomme.add_sample_channel(
        code=code,
        t_range=CRASH_TIME_RANGE,
        y_range=(0., peak),
        mode="pulse",
        unit=unit,
        frequency=frequency,
        noise=noise,
        seed=seed,
    )


def build_neck_isomme():
    isomme = pyisomme.Isomme(test_number="SYNTHETIC-NECK")
    # 11391 neck channels peak at roughly 1.05 kN / 90 N and 8 / 20 N*m.
    # Their dominant spectral components lie between about 3 and 14 Hz.
    add_crash_channel(isomme, "11NECKUP00WSFOXP", "N", 1050., 1.4, 8., 1)
    add_crash_channel(isomme, "11NECKUP00WSFOYP", "N", 92., 2.8, 6., 2)
    add_crash_channel(isomme, "11NECKUP00WSMOXP", "N*m", -8.3, 0.09, 6., 3)
    add_crash_channel(isomme, "11NECKUP00WSMOYP", "N*m", -20., 0.05, 3., 4)
    return isomme


def build_leg_isomme():
    isomme = pyisomme.Isomme(test_number="SYNTHETIC-LEGS")
    # Corrected H3 codes and approximate peaks from 11391. Four locations are
    # required to exercise the individual and aggregate tibia-index providers.
    tibia_peaks = {
        ("11", "LE", "UP"): (-37., -31., -2260.),
        ("11", "LE", "LO"): (23., -77., -1850.),
        ("11", "RI", "UP"): (-49., -65., -2330.),
        ("11", "RI", "LO"): (35., 39., -2970.),
        ("13", "RI", "LO"): (-7.5, -35.5, -2320.),
    }
    seed = 10
    for occupant, side, level in tibia_peaks:
        peak_mx, peak_my, peak_fz = tibia_peaks[(occupant, side, level)]
        prefix = f"{occupant}TIBI{side}{level}H3"
        add_crash_channel(isomme, prefix + "MOXP", "N*m", peak_mx, 0.3, 6., seed)
        add_crash_channel(isomme, prefix + "MOYP", "N*m", peak_my, 0.5, 10., seed + 1)
        add_crash_channel(isomme, prefix + "FOZP", "N", peak_fz, 4., 5., seed + 2)
        seed += 3

    # Femur compression in 11391 is predominantly negative, with peaks near
    # -1.2 kN left and -1.65 kN right and a few newtons of baseline noise.
    add_crash_channel(isomme, "11FEMRLE0000FOZP", "N", -1160., 3., 3., 30)
    add_crash_channel(isomme, "11FEMRRI0000FOZP", "N", -1650., 3., 5., 31)
    return isomme


class TestCalculate(unittest.TestCase):
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
        isomme = build_neck_isomme()
        moc = isomme.get_channel("11TMONUP00WSMOXB")
        moc_peak = isomme.get_channel("11TMONUP00WSMOXX")
        mx = isomme.get_channel("11NECKUP00WSMOXB")
        fy = isomme.get_channel("11NECKUP00WSFOYB")

        assert moc is not None and moc_peak is not None
        assert mx is not None and fy is not None
        expected = mx.get_data(unit="N*m") + fy.get_data(unit="N") * 0.0195
        np.testing.assert_allclose(moc.get_data(unit="N*m"), expected)
        self.assertEqual(len(moc_peak.data), 1)
        self.assertAlmostEqual(abs(moc_peak.get_data()[0]), np.max(np.abs(expected)))

    def test_calculate_neck_MOCy(self):
        isomme = build_neck_isomme()
        moc = isomme.get_channel("11TMONUP00WSMOYB")
        moc_peak = isomme.get_channel("11TMONUP00WSMOYX")
        my = isomme.get_channel("11NECKUP00WSMOYB")
        fx = isomme.get_channel("11NECKUP00WSFOXB")

        assert moc is not None and moc_peak is not None
        assert my is not None and fx is not None
        expected = my.get_data(unit="N*m") - fx.get_data(unit="N") * 0.0195
        np.testing.assert_allclose(moc.get_data(unit="N*m"), expected)
        self.assertEqual(len(moc_peak.data), 1)
        self.assertAlmostEqual(moc_peak.get_data()[0], np.min(expected))

    def test_get_channel_returns_none_for_unsupported_nij_dummy(self):
        isomme = pyisomme.Isomme(test_number="UNSUPPORTED-NIJ")
        isomme.add_sample_channel(
            code="11NECKUP0000FOZB", unit="N", mode="linear", y_range=(-100., 100.)
        )
        isomme.add_sample_channel(
            code="11NECKUP0000MOYB", unit="N*m", mode="linear", y_range=(-10., 10.)
        )

        self.assertIsNone(isomme.get_channel("11NIJCIPCF0000YB"))

    def test_fn_provider_handles_unsupported_dummy_for_other_calculations(self):
        isomme = pyisomme.Isomme(test_number="UNSUPPORTED-MOC")
        isomme.add_sample_channel(
            code="11NECKUP00H3MOXB", unit="N*m", mode="linear", y_range=(-10., 10.)
        )
        isomme.add_sample_channel(
            code="11NECKUP00H3FOYB", unit="N", mode="linear", y_range=(-100., 100.)
        )

        self.assertIsNone(isomme.get_channel("11TMONUP00H3MOXB"))

    def test_get_channel_does_not_hide_inconsistent_nij_inputs(self):
        isomme = pyisomme.Isomme(test_number="INCONSISTENT-NIJ")
        isomme.add_sample_channel(
            code="11NECKUP00H3FOZB", unit="N", mode="linear", y_range=(-100., 100.)
        )
        isomme.add_sample_channel(
            code="11NECKUP00HFMOYB", unit="N*m", mode="linear", y_range=(-10., 10.)
        )

        with self.assertRaisesRegex(ValueError, "Multiple dummy types"):
            isomme.get_channel("11NIJCIPCF??00YB")

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
        isomme = build_leg_isomme()
        tibia_index = isomme.get_channel("11TIINLU00H3000B")
        mx = isomme.get_channel("11TIBILEUPH3MOXB")
        my = isomme.get_channel("11TIBILEUPH3MOYB")
        fz = isomme.get_channel("11TIBILEUPH3FOZB")

        assert tibia_index is not None
        assert mx is not None and my is not None and fz is not None
        expected = np.hypot(mx.get_data(unit="N*m"), my.get_data(unit="N*m")) / 225.
        expected += np.abs(fz.get_data(unit="kN")) / 35.9
        np.testing.assert_allclose(tibia_index.get_data(), expected)

        for pattern in (
            "13TIINRL00H3000B",
            "11TIINL000H3000B",
            "11TIINR000H3000B",
            "11TIIN0U00H3000B",
            "11TIIN0L00H3000B",
            "11TIIN0000H3000B",
            "11TIINLUTOH3000B",
            "13TIINRLTOH3000B",
            "11TIINL0TOH3000B",
            "11TIINR0TOH3000B",
            "11TIIN0UTOH3000B",
            "11TIIN0LTOH3000B",
            "11TIIN00TOH3000B",
        ):
            self.assertIsNotNone(isomme.get_channel(pattern), pattern)

    def test_calculate_femur_impulse(self):
        isomme = build_leg_isomme()
        source = isomme.get_channel("11FEMRLE0000FOZP")
        assert source is not None

        direct = pyisomme.calculate_femur_impulse(source)
        left = isomme.get_channel("11KTHCLE0000IMZX")
        right = isomme.get_channel("11KTHCRI0000IMZX")
        minimum = isomme.get_channel("11KTHC000000IMZX")

        assert left is not None and right is not None and minimum is not None
        self.assertTrue(np.isfinite(direct.get_data()[0]))
        self.assertLess(direct.get_data()[0], 0.)
        self.assertEqual(
            minimum.get_data()[0],
            min(left.get_data()[0], right.get_data()[0]),
        )

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
