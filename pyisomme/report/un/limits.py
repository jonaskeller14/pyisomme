from dataclasses import dataclass

from pyisomme.limit import Limit


@dataclass(frozen=True, eq=False)
class Limit_Pass(Limit):
    name: str = "Pass"
    color: str = "green"
    rating: float = True


@dataclass(frozen=True, eq=False)
class Limit_Fail(Limit):
    name: str = "Fail"
    color: str = "red"
    rating: float = False
