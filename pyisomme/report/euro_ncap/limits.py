from dataclasses import dataclass
import numpy as np

from pyisomme.limit import Limit


@dataclass(frozen=True, eq=False)
class Limit_G(Limit):
    name = "Good"
    color = "green"
    rating = 4  # Points


@dataclass(frozen=True, eq=False)
class Limit_A(Limit):
    name = "Adequate"
    color = "yellow"
    rating = 4  # Points


@dataclass(frozen=True, eq=False)
class Limit_M(Limit):
    name = "Marginal"
    color = "orange"
    rating = 2.669  # Points


@dataclass(frozen=True, eq=False)
class Limit_W(Limit):
    name = "Weak"
    color = "brown"
    rating = 1.329  # Points


@dataclass(frozen=True, eq=False)
class Limit_P(Limit):
    name = "Poor"
    color = "red"
    rating = 0  # Points


@dataclass(frozen=True, eq=False)
class Limit_C(Limit):
    name = "Capping"
    color = "gray"
    rating = -np.inf  # Points
