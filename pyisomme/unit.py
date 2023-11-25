from __future__ import annotations
from astropy import units as astropy_units

astropy_units.set_enabled_aliases({"Nm": astropy_units.Unit("N*m")})


class Unit(astropy_units.Unit):
    def __init__(self, unit):
        super().__init__(unit)
