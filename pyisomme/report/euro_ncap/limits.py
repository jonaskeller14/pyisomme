import numpy as np

from pyisomme.limits import Limit


class Limit_4Points(Limit):
    name = "4 Points"
    color = "green"
    value = 4


class Limit_3Points(Limit):
    name = "3 Points"
    color = "yellow"
    value = 3


class Limit_2Points(Limit):
    name = "2 Points"
    color = "orange"
    value = 2


class Limit_1Points(Limit):
    name = "1 Points"
    color = "brown"
    value = 1


class Limit_0Points(Limit):
    name = "0 Points"
    color = "red"
    value = 1


class Limit_Capping(Limit):
    name = "Capping"
    color = "gray"
    value = -np.inf