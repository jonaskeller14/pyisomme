from pyisomme.unit import Unit

import fnmatch
import re
from collections.abc import Iterable
import logging
import numpy as np


class Limits:
    name: str
    limit_list: list

    def __init__(self, name: str = None, limit_list: list = None):
        self.name = name
        self.limit_list = [] if limit_list is None else limit_list

    def get_limits(self, *codes) -> list:
        """
        Returns list of limits matching given code.
        :param code: Channel code (pattern not allowed)
        :return:
        """
        output = []
        for limit in self.limit_list:
            for code in codes:
                if code is None:
                    continue
                for code_pattern in limit.code_patterns:
                    if fnmatch.fnmatch(code, code_pattern):
                        output.append(limit)
                    try:
                        if re.match(code_pattern, code):
                            output.append(limit)
                    except re.error:
                        continue
        return output

    def get_limit_color(self, y, y_unit, x, x_unit):
        if np.isnan(y):
            return None

        limit_list = sorted(self.limit_list, key=lambda limit: (limit.func(0), 0 if limit.upper and limit.lower else -1 if limit.upper else 1 if limit.lower else 0))
        for limit in limit_list:
            limit_y = limit.get_data(x, x_unit=x_unit, y_unit=y_unit)
            if limit.upper and limit_y > y:
                return limit.color
            if limit.lower and limit_y <= y:
                return limit.color
        return None

    def __repr__(self):
        return f"Limits({self.name})"

def limit_list_sort(limit_list: list):
    return sorted(limit_list, key=lambda limit: (limit.func(0), 0 if limit.upper and limit.lower else -1 if limit.upper else 1 if limit.lower else 0))

def limit_list_unique(limit_list: list, x, x_unit, y_unit):
    filtered_limit_list = []
    for limit in limit_list:
        add = True
        for filtered_limit in filtered_limit_list:
            # Same data?
            if not np.all(limit.get_data(x, x_unit=x_unit, y_unit=y_unit) == filtered_limit.get_data(x, x_unit=x_unit, y_unit=y_unit)):
                continue

            # Both upper or both lower?
            if limit.upper != filtered_limit.upper and limit.lower != filtered_limit.lower:
                continue

            if limit.name != filtered_limit.name:
                raise ValueError("Multiple limits with same data but different names")

            add = False
        if add:
            filtered_limit_list.append(limit)

    return filtered_limit_list


class Limit:
    def __init__(self, code_patterns: list, func, color="black", linestyle="-", name: str = None, lower: bool = None, upper: bool = None, x_unit="s", y_unit=None):
        self.code_patterns = code_patterns
        self.color = color
        self.linestyle = linestyle
        self.name = name
        self.lower = lower
        self.upper = upper
        self.func = lambda x: float(func(x)) if not isinstance(x, Iterable) else np.array([func(x_i) for x_i in x], dtype=float)  # if x is scalar --> return scalar, if is array --> return array
        self.x_unit = x_unit
        self.y_unit = y_unit

    def get_data(self, x, x_unit, y_unit):
        # Convert x
        if x_unit is not None:
            if self.x_unit is not None:
                x = x * Unit(x_unit).to(Unit(self.x_unit))
            else:
                logging.warning(f"Could not convert unit of {self}. Attribute x_unit missing.")

        # Calculate data
        y = self.func(x)

        # Convert y
        if y_unit is not None:
            if self.y_unit is not None:
                y *= Unit(self.y_unit).to(Unit(y_unit))
            else:
                logging.warning(f"Could not convert unit of {self}. Attribute y_unit missing.")
        return y

    def __repr__(self):
        return f"Limit({self.name})"

    def __eq__(self, other):
        return id(self) == id(other)
