import numpy as np

from pyisomme.limits import Limit


class Limit_G(Limit):
    name = "Good"
    color = "green"
    value = 4


class Limit_A(Limit):
    name = "Adequate"
    color = "yellow"
    value = 4


class Limit_M(Limit):
    name = "Marginal"
    color = "orange"
    value = 2.669


class Limit_W(Limit):
    name = "Weak"
    color = "brown"
    value = 1.329


class Limit_P(Limit):
    name = "Poor"
    color = "red"
    value = 0


class Limit_C(Limit):
    name = "Capping"
    color = "gray"
    value = -np.inf