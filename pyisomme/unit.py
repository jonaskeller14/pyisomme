import astropy.units as u
from astropy.constants import g0


u.set_enabled_aliases({"Nm": u.Unit("N*m")})

g0 = g0


class Unit:
    def __new__(cls, unit):
        if isinstance(unit, str):
            unit = unit.replace("°", "deg")
        return u.Unit(unit)
