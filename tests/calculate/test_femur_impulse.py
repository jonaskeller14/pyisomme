import numpy as np
import pytest

import pyisomme


class TestCalculateFemurImpulse:
    @pytest.fixture
    def isomme(self):
        isomme = pyisomme.Isomme(test_number="SYNTHETIC-LEGS")
        for code, peak, frequency, seed in (
            ("11FEMRLE0000FOZP", -1160.0, 3.0, 30),
            ("11FEMRRI0000FOZP", -1650.0, 5.0, 31),
        ):
            isomme.add_sample_channel(
                code=code,
                t_range=(-0.05, 0.3, 7001),
                y_range=(0.0, peak),
                mode="pulse",
                unit="N",
                frequency=frequency,
                noise=3.0,
                seed=seed,
            )
        return isomme

    def test_calculate_femur_impulse(self, isomme):
        source = isomme.get_channel("11FEMRLE0000FOZP")
        assert source is not None

        direct = pyisomme.calculate_femur_impulse(source)
        assert np.isfinite(direct.get_data()[0])
        assert direct.get_data()[0] < 0.0

    def test_calculate_femur_impulse_provider(self, isomme):
        left = isomme.get_channel("11KTHCLE0000IMZX")
        right = isomme.get_channel("11KTHCRI0000IMZX")
        minimum = isomme.get_channel("11KTHC000000IMZX")

        assert left is not None and right is not None and minimum is not None
        assert minimum.get_data()[0] == min(left.get_data()[0], right.get_data()[0])
