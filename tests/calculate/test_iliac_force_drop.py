import numpy as np
import pandas as pd
import pytest

import pyisomme


class TestCalculateIliacForceDrop:
    @pytest.fixture
    def channel(self):
        time = [0.0, 0.001, 0.002]
        return pyisomme.Channel(
            code="11PELVLE00WSFOZB",
            data=pd.DataFrame([10.0, 14.0, 20.0], index=time),
            unit="N",
        )

    def test_calculate_iliac_force_drop(self, channel):
        result = pyisomme.calculate_iliac_force_drop(channel)
        np.testing.assert_allclose(result.get_data(), [4.0, 6.0])
        assert result.data.index.tolist() == [0.0, 0.001]
        assert result.unit == channel.unit
