import numpy as np

from pyisomme.limits import Limit


class Limit_G(Limit):
    name = "Good"
    color = "green"
    rating = 4  # Points


class Limit_A(Limit):
    name = "Adequate"
    color = "yellow"
    rating = 4  # Points


class Limit_M(Limit):
    name = "Marginal"
    color = "orange"
    rating = 2.669  # Points


class Limit_W(Limit):
    name = "Weak"
    color = "brown"
    rating = 1.329  # Points


class Limit_P(Limit):
    name = "Poor"
    color = "red"
    rating = 0  # Points


class Limit_C(Limit):
    name = "Capping"
    color = "gray"
    rating = -np.inf  # Points