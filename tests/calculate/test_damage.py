import pytest

from pyisomme import Isomme, calculate_damage


class TestCalculateDamage:
    @pytest.fixture
    def isomme(self) -> Isomme:
        isomme = Isomme(test_number="0")
        isomme.add_sample_channel(
            code="11HEAD0000THAAXP", unit="rad/s^2", y_range=[0, 8e5]
        )
        isomme.add_sample_channel(
            code="11HEAD0000THAAYP", unit="rad/s^2", y_range=[0, 5e5]
        )
        isomme.add_sample_channel(
            code="11HEAD0000THAAZP", unit="rad/s^2", y_range=[0, 3e5]
        )
        return isomme

    def test_calculate_damage(self, isomme):
        damage = calculate_damage(*isomme.channels)
        assert len(damage) == 8
        assert damage[0].code.fine_location_1 == "DA"
        assert damage[-1].code.filter_class == "X"

    def test_calculate_damage_provider(self, isomme):
        assert isomme.get_channel("?1HEADDAMA??AAX?") is not None
        assert isomme.get_channel("?1HEADDAMA??AAY?") is not None
        assert isomme.get_channel("?1HEADDAMA??AAZ?") is not None
        assert isomme.get_channel("?1HEADDAMA??AAR?") is not None
