import numpy as np
import pytest

import pyisomme


class TestCalculateNeckMOC:
    @pytest.fixture
    def isomme(self):
        isomme = pyisomme.Isomme(test_number="SYNTHETIC-NECK")
        for code, unit, peak, noise, frequency, seed in (
            ("11NECKUP00WSFOXP", "N", 1050.0, 1.4, 8.0, 1),
            ("11NECKUP00WSFOYP", "N", 92.0, 2.8, 6.0, 2),
            ("11NECKUP00WSMOXP", "N*m", -8.3, 0.09, 6.0, 3),
            ("11NECKUP00WSMOYP", "N*m", -20.0, 0.05, 3.0, 4),
        ):
            isomme.add_sample_channel(
                code=code,
                t_range=(-0.05, 0.3, 7001),
                y_range=(0.0, peak),
                mode="pulse",
                unit=unit,
                frequency=frequency,
                noise=noise,
                seed=seed,
            )
        return isomme

    def test_calculate_neck_moc_x(self, isomme):
        mx = isomme.get_channel("11NECKUP00WSMOXB")
        fy = isomme.get_channel("11NECKUP00WSFOYB")
        assert mx is not None and fy is not None
        moc, moc_peak = pyisomme.calculate_neck_MOCx(mx, fy)
        assert moc.code.main_location == "TMON"
        assert len(moc_peak.data) == 1

    def test_calculate_neck_moc_x_provider(self, isomme):
        moc = isomme.get_channel("11TMONUP00WSMOXB")
        moc_peak = isomme.get_channel("11TMONUP00WSMOXX")
        mx = isomme.get_channel("11NECKUP00WSMOXB")
        fy = isomme.get_channel("11NECKUP00WSFOYB")

        assert moc is not None and moc_peak is not None
        assert mx is not None and fy is not None
        expected = mx.get_data(unit="N*m") + fy.get_data(unit="N") * 0.0195
        np.testing.assert_allclose(moc.get_data(unit="N*m"), expected)
        assert len(moc_peak.data) == 1
        assert abs(moc_peak.get_data()[0]) == pytest.approx(np.max(np.abs(expected)))

    def test_calculate_neck_moc_y(self, isomme):
        my = isomme.get_channel("11NECKUP00WSMOYB")
        fx = isomme.get_channel("11NECKUP00WSFOXB")
        assert my is not None and fx is not None
        moc, moc_peak = pyisomme.calculate_neck_MOCy(my, fx)
        assert moc.code.main_location == "TMON"
        assert len(moc_peak.data) == 1

    def test_calculate_neck_moc_y_provider(self, isomme):
        moc = isomme.get_channel("11TMONUP00WSMOYB")
        moc_peak = isomme.get_channel("11TMONUP00WSMOYX")
        my = isomme.get_channel("11NECKUP00WSMOYB")
        fx = isomme.get_channel("11NECKUP00WSFOXB")

        assert moc is not None and moc_peak is not None
        assert my is not None and fx is not None
        expected = my.get_data(unit="N*m") - fx.get_data(unit="N") * 0.0195
        np.testing.assert_allclose(moc.get_data(unit="N*m"), expected)
        assert len(moc_peak.data) == 1
        assert moc_peak.get_data()[0] == pytest.approx(np.min(expected))
