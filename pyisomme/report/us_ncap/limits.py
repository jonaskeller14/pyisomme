from dataclasses import dataclass

from pyisomme.limit import Limit


@dataclass(frozen=True, eq=False)
class Limit_5(Limit):
    name = "5 stars"
    color = "green"
    rating = 5


@dataclass(frozen=True, eq=False)
class Limit_4(Limit):
    name = "4 stars"
    color = "yellow"
    rating = 4


@dataclass(frozen=True, eq=False)
class Limit_3(Limit):
    name = "3 stars"
    color = "orange"
    rating = 3


@dataclass(frozen=True, eq=False)
class Limit_2(Limit):
    name = "2 stars"
    color = "brown"
    rating = 2


@dataclass(frozen=True, eq=False)
class Limit_1(Limit):
    name = "1 star"
    color = "red"
    rating = 1
