import pytest

import pyisomme


class TestCalculateNeckNIJ:
    @pytest.fixture
    def isomme(self):
        isomme = pyisomme.Isomme(test_number="NIJ")
        isomme.add_sample_channel(
            code="11NECKUP00H3FOZB", unit="N", mode="linear", y_range=(-100.0, 100.0)
        )
        isomme.add_sample_channel(
            code="11NECKUP00H3MOYB", unit="N*m", mode="linear", y_range=(-10.0, 10.0)
        )
        return isomme

    @pytest.fixture
    def unsupported_isomme(self):
        isomme = pyisomme.Isomme(test_number="UNSUPPORTED-NIJ")
        isomme.add_sample_channel(
            code="11NECKUP0000FOZB", unit="N", mode="linear", y_range=(-100.0, 100.0)
        )
        isomme.add_sample_channel(
            code="11NECKUP0000MOYB", unit="N*m", mode="linear", y_range=(-10.0, 10.0)
        )
        return isomme

    @pytest.fixture
    def inconsistent_isomme(self):
        isomme = pyisomme.Isomme(test_number="INCONSISTENT-NIJ")
        isomme.add_sample_channel(
            code="11NECKUP0000FOZB", unit="N", mode="linear", y_range=(-100.0, 100.0)
        )
        isomme.add_sample_channel(
            code="11NECKUP00HFMOYB", unit="N*m", mode="linear", y_range=(-10.0, 10.0)
        )
        return isomme

    def test_calculate_neck_nij(self, isomme):
        source_fz = isomme.get_channel("11NECKUP00H3FOZB")
        source_mocy = isomme.get_channel("11NECKUP00H3MOYB")
        assert source_fz is not None and source_mocy is not None

        direct = pyisomme.calculate_neck_nij(source_fz, source_mocy, oop=False)
        assert len(direct) == 10

    def test_calculate_neck_nij_provider(self, isomme):
        provided = isomme.get_channel("11NIJCIPCF??00YB")
        assert provided is not None
        assert provided.code.main_location == "NIJC"

    def test_get_channel_returns_none_for_unsupported_nij_dummy(self, unsupported_isomme):
        assert unsupported_isomme.get_channel("11NIJCIPCF0000YB") is None

    def test_get_channel_does_not_hide_inconsistent_nij_inputs(self, inconsistent_isomme):
        with pytest.raises(ValueError, match="Multiple dummy types"):
            inconsistent_isomme.get_channel("11NIJCIPCF??00YB")
