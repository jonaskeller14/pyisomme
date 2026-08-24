import pytest

import pyisomme


class TestCalculateChestPCScore:
    @pytest.fixture
    def isomme(self):
        isomme = pyisomme.Isomme(test_number="1234")
        for code in (
            "11CHSTLEUPTHDSRA",
            "11CHSTRIUPTHDSRA",
            "11CHSTLELOTHDSRA",
            "11CHSTRILOTHDSRA",
        ):
            isomme.add_sample_channel(code=code, unit="mm", y_range=[0, -20])
        return isomme

    def test_calculate_chest_pc_score(self, isomme):
        channel_le_up, channel_ri_up, channel_le_lo, channel_ri_lo = isomme.channels
        channel = pyisomme.calculate_chest_pc_score(
            channel_le_up, channel_ri_up, channel_le_lo, channel_ri_lo
        )
        assert channel.code == "11CHST00PCTHDSRA"

    def test_calculate_chest_pc_score_provider(self, isomme):
        channel = isomme.get_channel("11CHST00PCTHDSRA")
        assert channel is not None
        assert channel.code == "11CHST00PCTHDSRA"
