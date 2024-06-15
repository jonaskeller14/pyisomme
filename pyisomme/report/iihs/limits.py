import numpy as np

from pyisomme.limits import Limit


class Limit_G(Limit):
    name = "Good"
    color = "green"
    value = np.nan

class Limit_A(Limit):
    name = "Acceptable"
    color = "yellow"
    value = np.nan

class Limit_M(Limit):
    name = "Marginal"
    color = "orange"
    value = np.nan

class Limit_P(Limit):
    name = "Poor"
    color = "red"
    value = np.nan