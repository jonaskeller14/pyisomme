import fnmatch
import re
from collections.abc import Iterable


class Limits:
    def __init__(self, name: str = None, limits: list = None):
        self.name = name
        self.limits = [] if limits is None else limits

    def get_limits(self, *codes) -> list:
        """
        Returns list of limits matching given code.
        :param code: Channel code (pattern not allowed)
        :return:
        """
        output = []
        for limit in self.limits:
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

    def read(self, *paths):
        pass

    def write(self, path):
        pass


class Limit:
    def __init__(self, code_patterns: list, func, color="black", linestyle="-", name: str = None, lower: bool = None, upper: bool = None, x_unit=None, y_unit=None):
        self.code_patterns = code_patterns
        self.color = color
        self.linestyle = linestyle
        self.name = name
        self.lower = lower
        self.upper = upper
        self.func = lambda x: func(x) if not isinstance(x, Iterable) else [func(x_i) for x_i in x]  # if x is scalar --> return scalar, if is array --> return array
        self.x_unit = x_unit
        self.y_unit = y_unit

    def __repr__(self):
        return f"Limit({self.name})"
