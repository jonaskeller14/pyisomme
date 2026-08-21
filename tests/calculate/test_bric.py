import pandas as pd
import pytest

import pyisomme


class TestCalculateBrIC:
    @pytest.fixture
    def isomme(self):
        time = [0.0, 0.01]
        channels = []
        for code, values in (
            ("11HEAD000000AVXD", [10.0, 10.0]),
            ("11HEAD000000AVYD", [10.0, 100.0]),
            ("11HEAD000000AVZD", [10.0, 10.0]),
        ):
            channels.append(
                pyisomme.Channel(
                    code=code,
                    data=pd.DataFrame(values, index=time),
                    unit="rad/s",
                )
            )
        return pyisomme.Isomme(channels=channels)

    def test_calculate_bric(self, isomme):
        bric = pyisomme.calculate_bric(*isomme.channels)
        assert bric.code.main_location == "BRIC"
        assert bric.get_data()[0] > 1.0

    def test_calculate_bric_provider(self, isomme):
        bric = isomme.get_channel("11BRIC00000000XX")
        assert bric is not None
        assert bric.code.main_location == "BRIC"
        assert bric.code.direction == "0"
        assert bric.get_data()[0] > 0
