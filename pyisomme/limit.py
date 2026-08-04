from __future__ import annotations

from collections.abc import Iterable
import logging
from typing import Callable
import numpy as np

from pyisomme.unit import Unit


logger = logging.getLogger(__name__)


class Limit:
    name: str | None = None
    #: Score this limit awards. ``nan`` means "no rating declared" — legitimate for
    #: limits that only draw a reference line. Rating-consuming paths reject it
    #: explicitly (see :meth:`Limits.get_limit_ratings`) instead of failing later
    #: with an ``AttributeError``.
    rating: float = np.nan
    color: str = "black"
    code_patterns: list[str]
    func: Callable
    x_unit: str | Unit | int | None = "s"
    y_unit: str | Unit | int | None = "1"
    linestyle: str = "-"
    lower: bool | None = None
    upper: bool | None = None

    def __init__(self, code_patterns: list[str],
                 func: Callable,
                 color: str | None = None,
                 linestyle: str | None = None,
                 name: str | None = None,
                 rating: float | None = None,
                 lower: bool | None = None,
                 upper: bool | None = None,
                 x_unit: str | Unit | int | None = None,
                 y_unit: str | Unit | int | None = None):
        if code_patterns is not None:
            self.code_patterns = code_patterns
        if self.code_patterns is None:
            self.code_patterns = []

        if func is not None:
            self.func = func
        if self.func.__code__.co_argcount != 1:
            raise ValueError(
                f"Limit func must take exactly one argument, "
                f"got {self.func.__code__.co_argcount}."
            )

        if color is not None:
            self.color = color
        if linestyle is not None:
            self.linestyle = linestyle
        if name is not None:
            self.name = name
        if rating is not None:
            self.rating = rating
        if lower is not None:
            self.lower = lower
        if upper is not None:
            self.upper = upper
        if x_unit is not None:
            self.x_unit = x_unit
        if y_unit is not None:
            self.y_unit = y_unit

    def get_data(self, x, x_unit, y_unit) -> float | np.ndarray:
        # Convert x
        if x_unit is not None:
            if self.x_unit is not None:
                x = x * Unit(x_unit).to(Unit(self.x_unit))  # type: ignore[attr-defined]
            else:
                logger.warning(f"Could not convert unit of {self}. Attribute x_unit missing.")

        # Calculate data
        if isinstance(x, Iterable):
            y = np.array([self.func(x_i) for x_i in x], dtype=float)
        else:
            y = self.func(x)

        # Convert y
        if y_unit is not None:
            if self.y_unit is not None:
                y *= Unit(self.y_unit).to(Unit(y_unit))  # type: ignore[attr-defined]
            else:
                logger.warning(f"Could not convert unit of {self}. Attribute y_unit missing.")
        return y

    def __repr__(self):
        return f"Limit({self.name})"

    def __eq__(self, other):
        return id(self) == id(other)

    def __hash__(self):
        return id(self)
