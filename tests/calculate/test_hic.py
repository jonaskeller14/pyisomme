import pandas as pd
import pytest

import pyisomme


class TestCalculateHIC:
    @pytest.fixture
    def isomme_r(self):
        time = [0.0, 0.01, 0.02, 0.03]
        channel = pyisomme.Channel(
            code="11HEAD000000ACRA",
            data=pd.DataFrame([0.0, 1.0, 0.5, 0.0], index=time),
            unit="g",
        )
        return pyisomme.Isomme(channels=[channel])

    def test_calculate_hic(self, isomme_r):
        result = pyisomme.calculate_hic(isomme_r.channels[0], max_delta_t=15)
        assert result.code.main_location == "HICR"
        assert result.code.fine_location_2 == "15"

    def test_calculate_hic_provider(self, isomme_r):
        provided = isomme_r.get_channel("11HICR00150000RX")
        assert provided is not None
        assert provided.code.filter_class == "X"
        assert provided.get_data()[0] >= 0

    @pytest.fixture
    def isomme_xyz(self):
        time = [0.0, 0.01, 0.02, 0.03]
        return pyisomme.Isomme(
            channels=[
                pyisomme.Channel(
                    code="11HEAD000000ACXA",
                    data=pd.DataFrame([0.0, 1.0, 0.5, 0.0], index=time),
                    unit="g",
                ),
                pyisomme.Channel(
                    code="11HEAD000000ACYA",
                    data=pd.DataFrame([0.0, 0.0, 0.0, 0.0], index=time),
                    unit="g",
                ),
                pyisomme.Channel(
                    code="11HEAD000000ACZA",
                    data=pd.DataFrame([0.0, 0.0, 0.0, 0.0], index=time),
                    unit="g",
                ),
            ]
        )

    def test_calculate_resultant_and_hic_provider(self, isomme_xyz):
        hic = isomme_xyz.get_channel("11HICR00150000RX")
        assert hic is not None
        assert hic.code.main_location == "HICR"
        assert hic.code.filter_class == "X"
        assert hic.get_data()[0] >= 0