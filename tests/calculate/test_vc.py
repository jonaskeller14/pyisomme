import pandas as pd
import pytest

import pyisomme


class TestCalculateVC:
    @pytest.fixture
    def isomme(self):
        time = [0.0, 0.01, 0.02, 0.03, 0.04]
        channel = pyisomme.Channel(
            code="11CHSTLE00WSDSXC",
            data=pd.DataFrame([0.01, 0.02, 0.03, 0.04, 0.05], index=time),
            unit="m",
        )
        return pyisomme.Isomme(channels=[channel])

    def test_calculate_vc(self, isomme):
        direct, direct_peak = pyisomme.calculate_vc(isomme.channels[0])
        assert direct.code.main_location == "VCCR"
        assert direct_peak.code.filter_class == "X"

    def test_calculate_vc_provider(self, isomme):
        provided = isomme.get_channel("11VCCRLE00WSVEXX")
        assert provided is not None
        assert provided.code.filter_class == "X"
