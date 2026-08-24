import numpy as np
import pytest

import pyisomme


class TestCalculateTibiaIndex:
    @pytest.fixture
    def isomme(self):
        isomme = pyisomme.Isomme(test_number="SYNTHETIC-LEGS")
        tibia_peaks = {
            ("11", "LE", "UP"): (-37.0, -31.0, -2260.0),
            ("11", "LE", "LO"): (23.0, -77.0, -1850.0),
            ("11", "RI", "UP"): (-49.0, -65.0, -2330.0),
            ("11", "RI", "LO"): (35.0, 39.0, -2970.0),
            ("13", "RI", "LO"): (-7.5, -35.5, -2320.0),
        }
        seed = 10
        for occupant, side, level in tibia_peaks:
            peak_mx, peak_my, peak_fz = tibia_peaks[(occupant, side, level)]
            prefix = f"{occupant}TIBI{side}{level}H3"
            for suffix, unit, peak, noise, frequency, channel_seed in (
                ("MOXP", "N*m", peak_mx, 0.3, 6.0, seed),
                ("MOYP", "N*m", peak_my, 0.5, 10.0, seed + 1),
                ("FOZP", "N", peak_fz, 4.0, 5.0, seed + 2),
            ):
                isomme.add_sample_channel(
                    code=prefix + suffix,
                    t_range=(-0.05, 0.3, 7001),
                    y_range=(0.0, peak),
                    mode="pulse",
                    unit=unit,
                    frequency=frequency,
                    noise=noise,
                    seed=channel_seed,
                )
            seed += 3
        return isomme

    def test_calculate_tibia_index(self, isomme):
        mx = isomme.get_channel("11TIBILEUPH3MOXB")
        my = isomme.get_channel("11TIBILEUPH3MOYB")
        fz = isomme.get_channel("11TIBILEUPH3FOZB")
        assert mx is not None and my is not None and fz is not None
        result = pyisomme.calculate_tibia_index(mx, my, fz)
        assert result.code.main_location == "TIIN"
        assert result.get_data().shape == mx.get_data().shape

    def test_calculate_tibia_index_provider(self, isomme):
        tibia_index = isomme.get_channel("11TIINLU00H3000B")
        mx = isomme.get_channel("11TIBILEUPH3MOXB")
        my = isomme.get_channel("11TIBILEUPH3MOYB")
        fz = isomme.get_channel("11TIBILEUPH3FOZB")

        assert tibia_index is not None
        assert mx is not None and my is not None and fz is not None
        m_r = np.hypot(mx.get_data(unit="N*m"), my.get_data(unit="N*m"))
        f_z = fz.get_data(unit="kN")
        expected = np.where(
            (f_z < 0) & (m_r != 0),
            m_r / 225.0 + np.abs(f_z) / 35.9,
            0,
        )
        np.testing.assert_allclose(tibia_index.get_data(), expected)

    def test_tibia_index_aggregate_providers(self, isomme):
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
            assert isomme.get_channel(pattern) is not None, pattern
