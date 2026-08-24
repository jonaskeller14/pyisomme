import numpy as np
import pandas as pd
import pytest

import pyisomme


class TestCalculateResultant:
    @pytest.fixture
    def isomme(self):
        time = [0.0, 0.01, 0.02]
        channels = [
            pyisomme.Channel(
                code=code,
                data=pd.DataFrame(values, index=time),
                unit="g",
            )
            for code, values in (
                ("11HEAD0000H3ACXA", [3.0, 4.0, 0.0]),
                ("11HEAD0000H3ACYA", [4.0, 0.0, 0.0]),
                ("11HEAD0000H3ACZA", [0.0, 0.0, 12.0]),
            )
        ]
        return pyisomme.Isomme(channels=channels)

    def test_calculate_resultant(self, isomme):
        result = pyisomme.calculate_resultant(*isomme.channels)
        np.testing.assert_allclose(result.get_data(), [5.0, 4.0, 12.0])
        assert result.code.direction == "R"

    def test_calculate_resultant_provider(self, isomme):
        result = isomme.get_channel("11HEAD0000H3ACRA")
        assert result is not None
        np.testing.assert_allclose(result.get_data(), [5.0, 4.0, 12.0])
        assert result.code.direction == "R"
