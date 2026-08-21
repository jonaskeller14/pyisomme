import copy
import logging
import pickle

import astropy.units as u
import pandas as pd
import pytest
from astropy.constants import g0 as ASTROPY_G0_CONSTANT  # type: ignore

from pyisomme import Unit, g0
from pyisomme.channel import Channel

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(module)-12s %(levelname)-8s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S",
    level=logging.WARNING,
)


class TestUnitClassIdentity:
    """Verifies that custom Unit instantiation retains class identity."""

    def test_isinstance_check(self):
        unit_obj = Unit("m")
        assert isinstance(unit_obj, Unit), (
            "Unit('m') should be an instance of the custom Unit class, not u.UnitBase"
        )

    def test_passthrough_instantiation(self):
        unit1 = Unit("m")
        unit2 = Unit(unit1)
        assert isinstance(unit2, Unit)
        assert unit1 == unit2


class TestStringSanitizationAndEdgeCases:
    """Tests custom string replacements, degree symbols, and shorthand symbols."""

    @pytest.mark.parametrize(
        "input_str, expected_astropy_str",
        [
            ("°C", "deg_C"),
            ("°", "deg"),
            ("°/s", "deg / s"),
            ("-", "1"),
            ("Nm", "N m"),
            ("dimensionless", "1"),
        ],
    )
    def test_sanitization_mappings(self, input_str, expected_astropy_str):
        unit_obj = Unit(input_str)
        assert unit_obj._astropy_unit == u.Unit(expected_astropy_str)

    def test_compound_degree_edge_case(self):
        # Checks edge case when 'deg' and '°' appear in the same string ("deg°C" -> "degdeg_C")
        with pytest.raises(ValueError):
            Unit("deg°C")

    def test_whitespace_dash_sanitization(self):
        unit_obj = Unit(" - ")
        assert unit_obj._astropy_unit == u.Unit("1")

    def test_legacy(self):
        Unit("Nm")
        assert Unit("Nm") == Unit("N*m")
        Unit(1)
        Unit("1")
        Unit("")
        assert Unit("°C") == Unit("Celsius") == Unit("deg_C")
        assert Unit("°") == Unit("deg")
        assert Unit("°/s2") == Unit("deg/s^2")
        assert Unit("°/s") == Unit("deg/s")
        assert Unit(Unit("m")) == Unit("m")

    def test_channel_unit(self):
        channel = Channel(
            code="11HEAD0000H3ACXA",
            data=pd.DataFrame([1, 2, 3]),
            unit="g",
        )
        assert channel.unit == Unit(g0)


class TestGravityConstantHandling:
    """Tests Earth gravity (g0) unit integration and conversions."""

    def test_g0_object_behavior(self):
        unit_g0 = Unit(g0)
        assert isinstance(unit_g0, Unit)
        assert unit_g0.is_equivalent(u.m / (u.s**2))  # type: ignore

    def test_g0_scaling_equivalence(self):
        # 1 g0 must equal ~9.80665 m/s^2
        unit_g0 = Unit(g0)
        converted_val = (1 * unit_g0._astropy_unit).to(u.m / (u.s**2)).value  # type: ignore
        assert converted_val == pytest.approx(ASTROPY_G0_CONSTANT.value, abs=1e-5)

    def test_astropy_constant_quantity_passthrough(self):
        # Passing raw astropy Constant/Quantity directly
        unit_from_quantity = Unit(ASTROPY_G0_CONSTANT)
        assert isinstance(unit_from_quantity, Unit)
        assert unit_from_quantity.is_equivalent(u.m / (u.s**2))  # type: ignore


class TestArithmeticAndDelegation:
    """Tests operator overloads (*, /) and attribute delegation to Astropy."""

    def test_multiplication(self):
        u1 = Unit("m")
        u2 = Unit("s")
        res = u1 * u2
        assert isinstance(res, Unit)
        assert res == Unit("m * s")

    def test_division(self):
        u1 = Unit("m")
        u2 = Unit("s")
        res = u1 / u2
        assert isinstance(res, Unit)
        assert res == Unit("m / s")

    def test_equality(self):
        assert Unit("N*m") == Unit("Nm")
        assert Unit("m/s") == "m/s"  # Compare against string
        assert Unit("m") != Unit("s")

    def test_astropy_attribute_delegation(self):
        unit_obj = Unit("m/s")
        # .physical_type is delegated via __getattr__ to the underlying astropy unit
        assert unit_obj.physical_type == "speed"
        assert unit_obj.is_equivalent("km/h")


class TestCopyingAndHashing:
    """A copied Unit must stay a Unit -- see __getattr__ in pyisomme/unit.py."""

    def test_deepcopy_keeps_wrapper(self):
        unit_obj = Unit("m/s")
        copied = copy.deepcopy(unit_obj)
        assert isinstance(copied, Unit)
        assert copied == unit_obj

    def test_copy_keeps_wrapper(self):
        unit_obj = Unit("m/s")
        copied = copy.copy(unit_obj)
        assert isinstance(copied, Unit)
        assert copied == unit_obj

    def test_pickle_round_trip(self):
        unit_obj = Unit("m/s")
        restored = pickle.loads(pickle.dumps(unit_obj))
        assert isinstance(restored, Unit)
        assert restored == unit_obj

    def test_private_attributes_are_not_delegated(self):
        # Delegating dunder/private lookups is what handed out the bare astropy unit.
        private_name = "_not_an_attribute"
        with pytest.raises(AttributeError):
            getattr(Unit("m"), private_name)

    def test_hashable(self):
        assert len({Unit("m/s"), Unit("m/s"), Unit("m")}) == 2
        assert {Unit("m/s"): 1}[Unit("m/s")] == 1

    def test_deepcopied_channel_can_still_convert(self):
        # Regression: calculate_olc() deep-copies its velocity channel, and the copy's
        # unit used to come back as a raw astropy unit -- convert_unit() then failed
        # with "'m / s' and 'm / s' are not convertible" while exporting the PPTX.
        channel = Channel(
            code="10VEHC000000VEXA",
            data=pd.DataFrame({0: [1.0, 2.0]}, index=[0.0, 0.01]),
            unit="m/s",
        )
        copied = copy.deepcopy(channel)
        assert isinstance(copied.unit, Unit)
        copied.convert_unit(Unit("m/s"))
        assert copied.unit == Unit("m/s")
        copied.convert_unit("km/h")
        assert float(copied.get_data()[0]) == pytest.approx(3.6)


class TestReflectedArithmetic:
    """`2 * Unit(...)` must not fall out of the wrapper either."""

    def test_reflected_multiplication(self):
        res = 2 * Unit("m")
        assert isinstance(res, Unit)
        assert res == Unit("2 m")

    def test_reflected_division(self):
        res = 1 / Unit("s")
        assert isinstance(res, Unit)
        assert res == Unit("1/s")


class TestNumericAndInvalidInputs:
    """Verifies numeric handling and proper failure modes for bad unit definitions."""

    def test_numeric_inputs_allowed(self):
        # Numbers like 1 or 12345 produce dimensionless scale units in Astropy
        unit_int = Unit(12345)
        assert isinstance(unit_int, Unit)
        assert unit_int._astropy_unit == u.Unit(12345)  # type: ignore

    def test_invalid_unit_string(self):
        with pytest.raises(ValueError):
            Unit("not_a_real_unit_xyz")

    def test_invalid_complex_type(self):
        # Unparseable object types (e.g. list or dict) should raise TypeError or ValueError
        with pytest.raises((TypeError, ValueError)):
            Unit([1, 2, 3])
