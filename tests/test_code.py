import logging

import pytest

from pyisomme.code import Code, combine_codes
from pyisomme.errors import InvalidCodeError
from pyisomme.unit import Unit

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(module)-12s %(levelname)-8s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S",
    level=logging.WARNING,
)


class TestCode:
    def test_init(self):
        Code("11HEAD0000H3ACXA")

        assert Code("11HEAD0000H3ACXA") == Code("11HEAD0000H3ACXA")
        assert Code("11HEAD0000H3ACXA") != Code("11HEAD0000H3ACXB")
        assert Code("11HEAD0000H3ACXA") != Code("11HEAD0000H3ACX?")

        # 15 chars
        with pytest.raises(InvalidCodeError):
            Code("11HEAD0000H3ACX")
        # 17 chars
        with pytest.raises(InvalidCodeError):
            Code("11HEAD0000H3ACXA?")
        # invalid chars
        with pytest.raises(InvalidCodeError):
            Code("11HEAD0000H3ACX*")

    def test_is_valid(self):
        assert Code("11HEAD0000H3ACXA").is_valid()
        assert not Code("11HEAD0000??ACXA").is_valid()

    def test_get_default_unit(self):
        assert Code("11HEAD0000H3ACXA").get_default_unit() == Unit("m/s^2")

    def test_get_info(self):
        info = Code("11HEAD0000H3ACXA").get_info()
        assert info == {
            "Test Object": "Vehicle 1",
            "Position": "Front left",
            "Main Location": "Head",
            "Fine Location 1": "Not defined",
            "Fine Location 2": "Not defined",
            "Fine Location 3": "Hybrid III Mid-Sized Adult Male Dummy",
            "Physical Dimension": "Acceleration",
            "Direction": "Longitudinal",
            "Filter Class": "CFC 1000",
        }

    def test_combine_codes(self):
        assert (
            combine_codes("11HEAD0000H3ACXA", "11HEAD0000H3ACXB") == "11HEAD0000H3ACX?"
        )
        assert (
            combine_codes(
                "11HEAD0000H3ACXA",
                "11HEAD0000H3ACXB",
                "11HEAD0000H3DSXB",
                "11HEAD0000H3ACXA",
            )
            == "11HEAD0000H3??X?"
        )
