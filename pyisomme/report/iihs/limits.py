from dataclasses import dataclass

from pyisomme.limit import Limit


@dataclass(frozen=True, eq=False)
class Limit_G(Limit):
    name: str = "Good"
    color: str = "green"
    # rating: float  # demerits


@dataclass(frozen=True, eq=False)
class Limit_A(Limit):
    name: str = "Acceptable"
    color: str = "yellow"
    # rating: float  # demerits


@dataclass(frozen=True, eq=False)
class Limit_M(Limit):
    name: str = "Marginal"
    color: str = "orange"
    # rating: float  # demerits


@dataclass(frozen=True, eq=False)
class Limit_P(Limit):
    name: str = "Poor"
    color: str = "red"
    # rating: float  # demerits
