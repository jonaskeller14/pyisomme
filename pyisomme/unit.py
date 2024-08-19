import astropy.units as u
from astropy.constants import g0


u.set_enabled_aliases({"Nm": u.Unit("N*m"),
                       "dimensionless": u.Unit("1")})

g0 = g0


class Unit:
    def __new__(cls, unit):
        if isinstance(unit, str):
            unit = unit.replace("°C", "deg_C").replace("°", "deg")
        if unit == "-":
            unit = "1"
        return u.Unit(unit)
