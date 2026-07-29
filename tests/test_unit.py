import logging
import unittest
import astropy.units as u
from astropy.constants import g0 as ASTROPY_G0_CONSTANT # type: ignore
import pandas as pd

from pyisomme import Unit, g0
from pyisomme.channel import Channel

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(module)-12s %(levelname)-8s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S', level=logging.WARNING)


class TestUnitClassIdentity(unittest.TestCase):
    """Verifies that custom Unit instantiation retains class identity."""

    def test_isinstance_check(self):
        unit_obj = Unit("m")
        self.assertIsInstance(
            unit_obj, 
            Unit, 
            msg="Unit('m') should be an instance of the custom Unit class, not u.UnitBase"
        )

    def test_passthrough_instantiation(self):
        unit1 = Unit("m")
        unit2 = Unit(unit1)
        self.assertIsInstance(unit2, Unit)
        self.assertEqual(unit1, unit2)


class TestStringSanitizationAndEdgeCases(unittest.TestCase):
    """Tests custom string replacements, degree symbols, and shorthand symbols."""

    def test_sanitization_mappings(self):
        test_cases = [
            ("°C", "deg_C"),
            ("°", "deg"),
            ("°/s", "deg / s"),
            ("-", "1"),
            ("Nm", "N m"),
            ("dimensionless", "1"),
        ]
        for input_str, expected_astropy_str in test_cases:
            with self.subTest(input_str=input_str):
                unit_obj = Unit(input_str)
                self.assertEqual(unit_obj._astropy_unit, u.Unit(expected_astropy_str))

    def test_compound_degree_edge_case(self):
        # Checks edge case when 'deg' and '°' appear in the same string ("deg°C" -> "degdeg_C")
        with self.assertRaises(ValueError):
            Unit("deg°C")

    def test_whitespace_dash_sanitization(self):
        unit_obj = Unit(" - ")
        self.assertEqual(unit_obj._astropy_unit, u.Unit("1"))

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
            data=pd.DataFrame([1,2,3]),
            unit="g",
        )
        assert channel.unit == Unit(g0)


class TestGravityConstantHandling(unittest.TestCase):
    """Tests Earth gravity (g0) unit integration and conversions."""

    def test_g0_object_behavior(self):
        unit_g0 = Unit(g0)
        self.assertIsInstance(unit_g0, Unit)
        self.assertTrue(unit_g0.is_equivalent(u.m / (u.s ** 2))) # type: ignore

    def test_g0_scaling_equivalence(self):
        # 1 g0 must equal ~9.80665 m/s^2
        unit_g0 = Unit(g0)
        converted_val = (1 * unit_g0._astropy_unit).to(u.m / (u.s ** 2)).value # type: ignore
        self.assertAlmostEqual(converted_val, ASTROPY_G0_CONSTANT.value, places=5)

    def test_astropy_constant_quantity_passthrough(self):
        # Passing raw astropy Constant/Quantity directly
        unit_from_quantity = Unit(ASTROPY_G0_CONSTANT)
        self.assertIsInstance(unit_from_quantity, Unit)
        self.assertTrue(unit_from_quantity.is_equivalent(u.m / (u.s ** 2))) # type: ignore


class TestArithmeticAndDelegation(unittest.TestCase):
    """Tests operator overloads (*, /) and attribute delegation to Astropy."""

    def test_multiplication(self):
        u1 = Unit("m")
        u2 = Unit("s")
        res = u1 * u2
        self.assertIsInstance(res, Unit)
        self.assertEqual(res, Unit("m * s"))

    def test_division(self):
        u1 = Unit("m")
        u2 = Unit("s")
        res = u1 / u2
        self.assertIsInstance(res, Unit)
        self.assertEqual(res, Unit("m / s"))

    def test_equality(self):
        self.assertEqual(Unit("N*m"), Unit("Nm"))
        self.assertEqual(Unit("m/s"), "m/s")  # Compare against string
        self.assertNotEqual(Unit("m"), Unit("s"))

    def test_astropy_attribute_delegation(self):
        unit_obj = Unit("m/s")
        # .physical_type is delegated via __getattr__ to the underlying astropy unit
        self.assertEqual(unit_obj.physical_type, "speed")
        self.assertTrue(unit_obj.is_equivalent("km/h"))


class TestNumericAndInvalidInputs(unittest.TestCase):
    """Verifies numeric handling and proper failure modes for bad unit definitions."""

    def test_numeric_inputs_allowed(self):
        # Numbers like 1 or 12345 produce dimensionless scale units in Astropy
        unit_int = Unit(12345)
        self.assertIsInstance(unit_int, Unit)
        self.assertEqual(unit_int._astropy_unit, u.Unit(12345)) # type: ignore

    def test_invalid_unit_string(self):
        with self.assertRaises(ValueError):
            Unit("not_a_real_unit_xyz")

    def test_invalid_complex_type(self):
        # Unparseable object types (e.g. list or dict) should raise TypeError or ValueError
        with self.assertRaises((TypeError, ValueError)):
            Unit([1, 2, 3])


if __name__ == "__main__":
    unittest.main()
