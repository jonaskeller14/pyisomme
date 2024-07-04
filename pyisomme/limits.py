from __future__ import annotations

import fnmatch
import re
from collections.abc import Iterable
import logging
from typing import Callable
import numpy as np

from pyisomme import Channel, Code
from pyisomme.unit import Unit


logger = logging.getLogger(__name__)


class Limit:
    name: str = None
    rating: float
    color: str = "black"
    code_patterns: list[str]
    func: Callable
    x_unit: str | Unit
    y_unit: str | Unit
    lower: bool
    upper: bool
    rating: float

    def __init__(self, code_patterns: list, func, color: str = None, linestyle: str = "-", name: str = None, rating: float = None, lower: bool = None, upper: bool = None, x_unit="s", y_unit=None):
        self.code_patterns: list = code_patterns

        if isinstance(func, int) or isinstance(func, float):
            func = lambda x: func
        assert func.__code__.co_argcount == 1
        self.func = lambda x: float(func(x)) if not isinstance(x, Iterable) else np.array([func(x_i) for x_i in x], dtype=float)  # if x is scalar --> return scalar, if is array --> return array

        if color is not None:
            self.color = color
        self.linestyle = linestyle
        if name is not None:
            self.name = name
        if rating is not None:
            self.rating = rating
        self.lower = lower
        self.upper = upper
        self.x_unit = x_unit
        self.y_unit = y_unit

    def get_data(self, x, x_unit, y_unit) -> float | np.ndarray:
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

    def find_limits(self, *codes: Code | str) -> list:
        """
        Returns list of limits matching given code.
        :param codes: Channel code (pattern not allowed)
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

    def get_limits(self, channel: Channel) -> list[Limit]:
        limits = limit_list_sort(self.find_limits(channel.code))
        assert len(limits) > 0, "No limits found."

        channel_times = channel.data.index
        channel_values = channel.get_data()

        limit_data = np.array([limit.get_data(channel_times, x_unit="s", y_unit=channel.unit) for limit in limits])
        limit_matching = np.zeros_like(limit_data, dtype=bool)

        for idx, (limit, data) in enumerate(zip(limits, limit_data)):
            limit_matching[idx, :] = (channel_values == data) + ((limit.upper is True) * (channel_values < data)) + ((limit.lower is True) * (channel_values > data))

        diff = np.abs(limit_data - channel_values)
        diff[~limit_matching] = np.inf

        limit_idx = np.argmin(diff, axis=0)
        limit_list = list(np.array(limits)[limit_idx])

        return limit_list

    def get_limit_max(self, channel: Channel) -> Limit:
        limits = self.get_limits(channel)
        limit_ratings = self.get_limit_max_rating(channel, interpolate=True)
        return limits[np.nanargmax(limit_ratings)]

    def get_limit_min(self, channel: Channel) -> Limit:
        limits = self.get_limits(channel)
        limit_ratings = self.get_limit_max_rating(channel, interpolate=True)
        return limits[np.nanargmin(limit_ratings)]

    def get_limit_ratings(self, channel: Channel, interpolate=True) -> list:
        limits = limit_list_sort(self.find_limits(channel.code))
        assert len(limits) > 0, "No limits found."
        assert None not in [limit.rating for limit in limits], "All limits must have a value defined."

        channel_times = channel.data.index
        channel_values = channel.get_data()

        if interpolate:
            limit_ratings = []
            limit_data = {limit: limit.get_data(channel_times, x_unit="s", y_unit=channel.unit) for limit in limits}
            for idx, (channel_time, channel_value) in enumerate(zip(channel_times, channel_values)):
                limit_ratings.append(np.interp(channel_value, [limit_data[limit][idx] for limit in limits], [limit.rating for limit in limits]))
        else:
            limit_ratings = []
            limit_data = {limit: limit.get_data(channel_times, x_unit="s", y_unit=channel.unit) for limit in limits}
            for idx, (channel_time, channel_value) in enumerate(zip(channel_times, channel_values)):
                for limit, data in limit_data.items():
                    if limit.upper and channel_value < data[idx]:
                        limit_ratings.append(limit.rating)
                        break
                    if limit.lower and channel_value >= data[idx]:
                        limit_ratings.append(limit.rating)
                        break
        return limit_ratings

    def get_limit_max_rating(self, channel: Channel, interpolate=True) -> float:
        return np.nanmax(self.get_limit_ratings(channel, interpolate))

    def get_limit_min_rating(self, channel: Channel, interpolate=True) -> float:
        return np.nanmin(self.get_limit_ratings(channel, interpolate))

    def get_limit_colors(self, channel: Channel) -> list:
        return [limit.color for limit in self.get_limits(channel)]

    def get_limit_min_color(self, channel: Channel):
        limit_ratings = self.get_limit_ratings(channel, interpolate=True)
        limit_colors = self.get_limit_colors(channel)
        return limit_colors[np.nanargmin(limit_ratings)]

    def get_limit_max_color(self, channel: Channel):
        limit_ratings = self.get_limit_ratings(channel, interpolate=True)
        limit_colors = self.get_limit_colors(channel)
        return limit_colors[np.nanargmax(limit_ratings)]

    def get_limit_min_idx(self, channel: Channel) -> int:
        limit_ratings = np.array(self.get_limit_ratings(channel, interpolate=True))
        idx_candidates = np.nonzero(np.min(limit_ratings) == limit_ratings)[0]

        limits = self.get_limits(channel)
        limit_values = np.array([limit.get_data(x=t, x_unit="s", y_unit=channel.unit) for t, limit in zip(channel.data.index, limits)])

        diff = np.abs(channel.get_data() - limit_values)
        return idx_candidates[np.argmin(diff[idx_candidates])]

    def get_limit_max_idx(self, channel: Channel):
        limit_ratings = np.array(self.get_limit_ratings(channel, interpolate=True))
        idx_candidates = np.nonzero(np.max(limit_ratings) == limit_ratings)[0]

        limits = self.get_limits(channel)
        limit_values = np.array([limit.get_data(x=t, x_unit="s", y_unit=channel.unit) for t, limit in zip(channel.data.index, limits)])

        diff = np.abs(channel.get_data() - limit_values)
        return idx_candidates[np.argmin(diff[idx_candidates])]

        idx1 = np.nanargmin([diff_limits_higher_rating_min_max, diff_limits_lower_rating_min_min])
        if idx1 == 0:
            return idx_candidates[np.nanargmin(diff_limits_higher_rating_min[idx_candidates])]
        else:
            return idx_candidates[np.nanargmax(diff_limits_lower_rating_min[idx_candidates])]

    def get_limit_min_y(self, channel: Channel, unit=None) -> float:
        idx = self.get_limit_min_idx(channel)
        return channel.get_data(unit=unit)[idx]

    def get_limit_max_y(self, channel: Channel, unit=None) -> float:
        idx = self.get_limit_max_idx(channel)
        return channel.get_data(unit=unit)[idx]

    def get_limit_min_x(self, channel: Channel) -> float:
        idx = self.get_limit_min_idx(channel)
        return channel.data.index[idx]

    def get_limit_max_x(self, channel: Channel) -> float:
        idx = self.get_limit_max_idx(channel)
        return channel.data.index[idx]

    def __repr__(self):
        return f"Limits({self.name})"


def limit_list_sort(limit_list: list[Limit], sym=False) -> list:
    if sym:
        return sorted(limit_list, key=lambda limit: (np.abs(limit.func(0)), -1 if limit.upper and limit.func(0) >= 0 else 1 if limit.lower and limit.func(0) >= 0 else 1 if limit.upper and limit.func(0) < 0 else -1 if limit.lower and limit.func(0) < 0 else 0))
    else:
        return sorted(limit_list, key=lambda limit: (limit.func(0), -1 if limit.upper else 1 if limit.lower else 0))


def limit_list_unique(limit_list: list[Limit],
                      x,
                      x_unit,
                      y_unit,
                      compare_code_patterns: bool = False,
                      compare_func: bool = True,
                      compare_x_unit: bool = False,
                      compare_y_unit: bool = False,
                      compare_name: bool = True,
                      compare_rating: bool = False,
                      compare_upper: bool = True,
                      compare_lower: bool = True) -> list[Limit]:
    filtered_limit_list = []
    for limit in limit_list:
        add = True
        for filtered_limit in filtered_limit_list:
            if compare_code_patterns and limit.code_patterns != filtered_limit.code_patterns:
                continue

            if compare_func and not np.all(limit.get_data(x, x_unit=x_unit, y_unit=y_unit) == filtered_limit.get_data(x, x_unit=x_unit, y_unit=y_unit)):
                continue

            if compare_x_unit and limit.x_unit != filtered_limit.x_unit:
                continue

            if compare_y_unit and limit.y_unit != filtered_limit.y_unit:
                continue

            if compare_upper and limit.upper != filtered_limit.upper:
                continue

            if compare_lower and limit.lower != filtered_limit.lower:
                continue

            if compare_rating and limit.rating != filtered_limit.rating:
                continue

            if compare_name and limit.name != filtered_limit.name:
                continue

            add = False
        if add:
            filtered_limit_list.append(limit)

    return filtered_limit_list



