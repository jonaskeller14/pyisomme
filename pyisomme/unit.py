import astropy.units as u
from astropy.constants import g0 as ASTROPY_G0  # type: ignore

u.set_enabled_aliases({
    "Nm": u.Unit("N*m"),
    "dimensionless": u.Unit("1")
})

# Register standard earth gravity as an official custom Astropy unit
g0_unit = u.def_unit("g0", represents=ASTROPY_G0.value * u.m / (u.s**2), doc="Standard gravity acceleration") # type: ignore
u.add_enabled_units([g0_unit])

# Export g0 to keep compatibility with existing imports
g0 = g0_unit  


class Unit:
    """
    Custom Unit class wrapping Astropy unit functionality.
    
    Handles custom string sanitization, degree symbols, unit unitless/dash representations,
    and supports standard earth gravity (g0) as a valid unit representation.
    """
    
    def __init__(self, unit_input):
        # 1. Handle pass-through if already an instance of our custom Unit class
        if isinstance(unit_input, Unit):
            self._astropy_unit = unit_input._astropy_unit
            return

        # 2. Sanitize string inputs
        if isinstance(unit_input, str):
            unit_input = unit_input.replace("°C", "deg_C").replace("°", "deg")
            if unit_input.strip() == "-":
                unit_input = "1"

        # 3. Check for Quantity FIRST (before UnitBase, because Constants inherit from both!)
        if isinstance(unit_input, u.Quantity):
            self._astropy_unit = u.Unit(unit_input.value) * unit_input.unit
        elif isinstance(unit_input, (u.UnitBase, u.FunctionUnitBase)):
            self._astropy_unit = unit_input
        else:
            # Handles strings, ints, floats natively via Astropy
            self._astropy_unit = u.Unit(unit_input)

    def to(self, other, value=1.0, equivalencies=None):
        """
        Return the value(s) converted from this unit to `other` unit.
        
        Matches Astropy's native Unit.to() signature while gracefully handling
        custom Unit wrappers, raw strings, and Astropy unit objects.
        
        :param other: Target unit (Unit wrapper, str, or Astropy Unit)
        :param value: Scalar float or NumPy array to convert (default 1.0)
        :param equivalencies: Optional Astropy unit equivalencies
        :return: Converted float or NumPy array
        """
        # Unwrap or convert target unit to a native Astropy unit object
        if isinstance(other, Unit):
            target = other._astropy_unit
        elif isinstance(other, (u.UnitBase, u.FunctionUnitBase)):
            target = other
        else:
            target = Unit(other)._astropy_unit

        return self._astropy_unit.to(target, value=value, equivalencies=equivalencies) # type: ignore
            

    # Automatically delegate all standard Astropy Unit attributes & methods
    def __getattr__(self, name):
        return getattr(self._astropy_unit, name)

    # Operator overload delegation for unit arithmetic (e.g., unit_a * unit_b)
    def __mul__(self, other):
        if not isinstance(other, Unit):
            other = Unit(other)
        other_raw = other._astropy_unit if isinstance(other, Unit) else other
        return Unit(self._astropy_unit * other_raw)

    def __truediv__(self, other):
        if not isinstance(other, Unit):
            other = Unit(other)
        other_raw = other._astropy_unit if isinstance(other, Unit) else other
        return Unit(self._astropy_unit / other_raw)

    def __rmul__(self, other):
        return other * self._astropy_unit

    def __rtruediv__(self, other):
        return other / self._astropy_unit

    def __eq__(self, other):
        if isinstance(other, Unit):
            return self._astropy_unit == other._astropy_unit
        try:
            return self._astropy_unit == u.Unit(other)
        except Exception:
            return False

    def __repr__(self):
        return f"Unit('{self._astropy_unit}')"

    def __str__(self):
        return str(self._astropy_unit)
