from pyisomme.limits import Limit


class Limit_G(Limit):
    name = "Good"
    color = "green"
    rating: float  # demerits

class Limit_A(Limit):
    name = "Acceptable"
    color = "yellow"
    rating: float  # demerits

class Limit_M(Limit):
    name = "Marginal"
    color = "orange"
    rating: float  # demerits

class Limit_P(Limit):
    name = "Poor"
    color = "red"
    rating: float  # demerits
