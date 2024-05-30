from __future__ import annotations

import copy
import fnmatch
import re
from collections.abc import Iterable
import logging
import numpy as np

from pyisomme import Channel, Code
from pyisomme.unit import Unit


logger = logging.getLogger(__name__)


class Limit:
    name: str
    value: float
    color: str

    def __init__(self, code_patterns: list, func, color: str = None, linestyle: str = "-", name: str = None, value: float = None, lower: bool = None, upper: bool = None, x_unit="s", y_unit=None):
        self.code_patterns: list = code_patterns
        self.func = lambda x: float(func(x)) if not isinstance(x, Iterable) else np.array([func(x_i) for x_i in x], dtype=float)  # if x is scalar --> return scalar, if is array --> return array

        if color is not None:
            self.color = color
        self.linestyle = linestyle
        if name is not None:
            self.name = name
        if value is not None:
            self.value = value
        self.lower = lower
        self.upper = upper
        self.x_unit = x_unit
        self.y_unit = y_unit

    def get_data(self, x, x_unit, y_unit):
        # Convert x
        if x_unit is not None:
            if self.x_unit is not None:
                x = x * Unit(x_unit).to(Unit(self.x_unit))
            else:
                logger.warning(f"Could not convert unit of {self}. Attribute x_unit missing.")

        # Calculate data
        y = self.func(x)

        # Convert y
        if y_unit is not None:
            if self.y_unit is not None:
                y *= Unit(self.y_unit).to(Unit(y_unit))
            else:
                logger.warning(f"Could not convert unit of {self}. Attribute y_unit missing.")
        return y

    def __repr__(self):
        return f"Limit({self.name})"

    def __eq__(self, other):
        return id(self) == id(other)

    def __hash__(self):
        return id(self)


class Limits:
    name: str
    limit_list: list

    def __init__(self, name: str = None, limit_list: list = None):
        self.name = name
        self.limit_list = [] if limit_list is None else limit_list

    def get_limits(self, *codes: Code | str) -> list:
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

    def get_limit_colors(self, channel: Channel) -> list:
        limits = limit_list_sort(self.get_limits(channel.code))
        assert None not in [limit.value for limit in limits], "All limits must have a value defined."
        assert None not in [limit.color for limit in limits], "All limits must have a color defined."

        channel_time = channel.data.index
        channel_values = channel.data.values

        limit_colors = []
        for channel_time, channel_value in zip(channel_time, channel_values):
            for limit in limits:
                if limit.upper and channel_value < limit.get_data(channel_time, x_unit="s", y_unit=channel.unit):
                    limit_colors.append(limit.color)
                    break
                if limit.lower and channel_value >= limit.get_data(channel_time, x_unit="s", y_unit=channel.unit):
                    limit_colors.append(limit.color)
                    break
        return limit_colors

    def get_limit_values(self, channel: Channel, interpolate=True) -> list:
        limits = limit_list_sort(self.get_limits(channel.code))
        assert None not in [limit.value for limit in limits], "All limits must have a value defined."

        channel_times = channel.data.index
        channel_values = channel.data.values

        if interpolate:
            limit_values = []
            limit_data = {limit: limit.get_data(channel_times, x_unit="s", y_unit=channel.unit) for limit in limits}
            for idx, (channel_time, channel_value) in enumerate(zip(channel_times, channel_values)):
                limit_values.append(np.interp(channel_value, [limit_data[limit][idx] for limit in limits], [limit.value for limit in limits]))
        else:
            limit_values = []
            limit_data = {limit: limit.get_data(channel_times, x_unit="s", y_unit=channel.unit) for limit in limits}
            for idx, (channel_time, channel_value) in enumerate(zip(channel_times, channel_values)):
                for limit, data in limit_data.items():
                    if limit.upper and channel_value < data[idx]:
                        limit_values.append(limit.value)
                        break
                    if limit.lower and channel_value >= data[idx]:
                        limit_values.append(limit.value)
                        break
        return limit_values

    def get_limit_max_value(self, channel: Channel, interpolate=True) -> float:
        return np.max(self.get_limit_values(channel, interpolate))

    def get_limit_min_value(self, channel: Channel, interpolate=True) -> float:
        return np.min(self.get_limit_values(channel, interpolate))

    def get_limit_min_color(self, channel: Channel):
        limit_values = self.get_limit_values(channel, interpolate=False)
        limit_colors = self.get_limit_colors(channel)
        return limit_colors[np.argmin(limit_values)]

    def get_limit_max_color(self, channel: Channel):
        limit_values = self.get_limit_values(channel, interpolate=False)
        limit_colors = self.get_limit_colors(channel)
        return limit_colors[np.argmax(limit_values)]

    def add_sym_limits(self):
        for limit in self.limit_list:
            new_limit = copy.deepcopy(limit)
            new_limit.upper = True if limit.lower else None
            new_limit.lower = True if limit.upper else None
            new_limit.func = lambda x: -1 * new_limit.func(x)

            self.limit_list.append(new_limit)

    def __repr__(self):
        return f"Limits({self.name})"


def limit_list_sort(limit_list: list[Limit], sym=False) -> list:
    return sorted(limit_list, key=lambda limit: (limit.func(0) if not sym else np.abs(limit.func(0)), 0 if limit.upper and limit.lower else -1 if limit.upper else 1 if limit.lower else 0))


def limit_list_unique(limit_list: list[Limit], x, x_unit, y_unit) -> list:
    filtered_limit_list = []
    for limit in limit_list:
        add = True
        for filtered_limit in filtered_limit_list:
            # Same data?
            if not np.all(limit.get_data(x, x_unit=x_unit, y_unit=y_unit) == filtered_limit.get_data(x, x_unit=x_unit, y_unit=y_unit)):
                continue

            # Both upper or both lower?
            if limit.upper != filtered_limit.upper or limit.lower != filtered_limit.lower:
                continue

            if limit.name != filtered_limit.name:
                raise ValueError("Multiple limits with same data but different names")

            add = False
        if add:
            filtered_limit_list.append(limit)

    return filtered_limit_list



