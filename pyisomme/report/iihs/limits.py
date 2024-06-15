from pyisomme.limits import Limit


class Limit_G(Limit):
    name = "Good"
    color = "green"

class Limit_A(Limit):
    name = "Acceptable"
    color = "yellow"

class Limit_M(Limit):
    name = "Marginal"
    color = "orange"

class Limit_P(Limit):
    name = "Poor"
    color = "red"
