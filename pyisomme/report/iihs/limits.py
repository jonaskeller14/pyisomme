from dataclasses import dataclass

from pyisomme.limit import Limit


@dataclass(frozen=True, eq=False)
class Limit_G(Limit):
    name = "Good"
    color = "green"
    # rating: float  # demerits


@dataclass(frozen=True, eq=False)
class Limit_A(Limit):
    name = "Acceptable"
    color = "yellow"
    # rating: float  # demerits


@dataclass(frozen=True, eq=False)
class Limit_M(Limit):
    name = "Marginal"
    color = "orange"
    # rating: float  # demerits


@dataclass(frozen=True, eq=False)
class Limit_P(Limit):
    name = "Poor"
    color = "red"
    # rating: float  # demerits
