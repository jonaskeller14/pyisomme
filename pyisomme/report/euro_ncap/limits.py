from dataclasses import dataclass
import numpy as np

from pyisomme.limit import Limit


@dataclass(frozen=True, eq=False)
class Limit_G(Limit):
    name: str = "Good"
    color: str = "green"
    rating: float = 4  # Points


@dataclass(frozen=True, eq=False)
class Limit_A(Limit):
    name: str = "Adequate"
    color: str = "yellow"
    rating: float = 4  # Points


@dataclass(frozen=True, eq=False)
class Limit_M(Limit):
    name: str = "Marginal"
    color: str = "orange"
    rating: float = 2.669  # Points


@dataclass(frozen=True, eq=False)
class Limit_W(Limit):
    name: str = "Weak"
    color: str = "brown"
    rating: float = 1.329  # Points


@dataclass(frozen=True, eq=False)
class Limit_P(Limit):
    name: str = "Poor"
    color: str = "red"
    rating: float = 0  # Points


@dataclass(frozen=True, eq=False)
class Limit_C(Limit):
    name: str = "Capping"
    color: str = "gray"
    rating: float = -np.inf  # Points
