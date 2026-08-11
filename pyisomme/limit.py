from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import logging
from typing import Callable
import numpy as np

from pyisomme.unit import Unit


logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class Limit:
    code_patterns: tuple[str, ...]
    func: Callable
    color: str = "black"
    linestyle: str = "-"
    name: str | None = None
    rating: float = np.nan
    lower: bool | None = None
    upper: bool | None = None
    x_unit: str | Unit | int | None = "s"
    y_unit: str | Unit | int | None = "1"

    def get_data(self, x, x_unit, y_unit) -> float | np.ndarray:
        # Convert x
        if x_unit is not None:
            if self.x_unit is not None:
                x = x * Unit(x_unit).to(Unit(self.x_unit))
            else:
                logger.warning(
                    f"Could not convert unit of {self}. Attribute x_unit missing."
                )

        # Calculate data
        if isinstance(x, Iterable):
            y = np.array([self.func(x_i) for x_i in x], dtype=float)
        else:
            y = self.func(x)

        # Convert y
        if y_unit is not None:
            if self.y_unit is not None:
                y *= Unit(self.y_unit).to(Unit(y_unit))
            else:
                logger.warning(
                    f"Could not convert unit of {self}. Attribute y_unit missing."
                )
        return y

    def __repr__(self):
        return f"Limit({self.name})"
