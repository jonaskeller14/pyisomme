from dataclasses import dataclass

from pyisomme.limit import Limit


@dataclass(frozen=True, eq=False)
class Limit_Pass(Limit):
    name = "Pass"
    color = "green"
    rating = True


@dataclass(frozen=True, eq=False)
class Limit_Fail(Limit):
    name = "Fail"
    color = "red"
    rating = False
