from dataclasses import dataclass

from pyisomme.limit import Limit


@dataclass(frozen=True, eq=False)
class Limit_5(Limit):
    name: str = "5 stars"
    color: str = "green"
    rating: float = 5


@dataclass(frozen=True, eq=False)
class Limit_4(Limit):
    name: str = "4 stars"
    color: str = "yellow"
    rating: float = 4


@dataclass(frozen=True, eq=False)
class Limit_3(Limit):
    name: str = "3 stars"
    color: str = "orange"
    rating: float = 3


@dataclass(frozen=True, eq=False)
class Limit_2(Limit):
    name: str = "2 stars"
    color: str = "brown"
    rating: float = 2


@dataclass(frozen=True, eq=False)
class Limit_1(Limit):
    name: str = "1 star"
    color: str = "red"
    rating: float = 1
