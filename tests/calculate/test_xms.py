import pandas as pd
import pytest

import pyisomme


class TestCalculateXMS:
    @pytest.fixture
    def isomme(self):
        time = [0.0, 0.001, 0.002, 0.003, 0.004]
        channel = pyisomme.Channel(
            code="11HEAD0000H3ACXA",
            data=pd.DataFrame([0.0, 1.0, 2.0, 3.0, 4.0], index=time),
            unit="g",
        )
        return pyisomme.Isomme(channels=[channel])

    def test_calculate_xms(self, isomme):
        direct = pyisomme.calculate_xms(isomme.channels[0], min_delta_t=1, method="S")
        assert direct.code.fine_location_2 == "1S"

    def test_calculate_xms_provider(self, isomme):
        provided = isomme.get_channel("11HEAD001SH3ACXX")
        assert provided is not None
        assert provided.code.filter_class == "X"
        assert provided.get_data()[0] >= 0

        xms = isomme.get_channel("11HEAD003SH3ACXX")
        assert xms is not None
        assert xms.code.fine_location_2 == "3S"
        assert xms.code.filter_class == "X"
        assert xms.data.shape == (1, 1)
