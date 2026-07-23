from __future__ import annotations

import copy
import fnmatch
import re
from collections.abc import Iterable
import logging
from typing import Callable, cast
import numpy as np

from pyisomme import Channel, Code
from pyisomme.unit import Unit


logger = logging.getLogger(__name__)


class Limit:
    name: str | None = None
    rating: float
    color: str = "black"
    code_patterns: list[str] | None = None
    func: Callable
    x_unit: str | Unit | None = "s"
    y_unit: str | Unit | None = "1"
    linestyle: str = "-"
    lower: bool | None = None
    upper: bool | None = None

    def __init__(self, code_patterns: list | None = None,
                 func: Callable | None = None,
                 color: str | None = None,
                 linestyle: str | None = None,
                 name: str | None = None,
                 rating: float | None = None,
                 lower: bool | None = None,
                 upper: bool | None = None,
                 x_unit: str | Unit | None = None,
                 y_unit: str | Unit | None = None):
        if code_patterns is not None:
            self.code_patterns = code_patterns
        if self.code_patterns is None:
            self.code_patterns = []

        if func is not None:
            self.func = func
        assert self.func.__code__.co_argcount == 1

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


class Limits:
    name: str
    limit_list: list

    def __init__(self, name: str = "Unnamed Limits", limit_list: list | None = None):
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
        channel_values = cast(np.ndarray, channel.get_data())

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
        channel_values = cast(np.ndarray, channel.get_data())

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

    def _get_tie_break_idx(self, channel: Channel, idx_candidates: np.ndarray, find_max: bool) -> int:
        """
        Given several time indices tied at the same rating, pick the one that is most
        representative of that rating, using the distance to the nearest limit of a
        different rating as a finer-grained tie-breaker.

        find_max=False (get_limit_min_idx): prefer the candidate closest to a strictly
        better-rated limit (about to cross into a better rating); if none is close to a
        better-rated limit, fall back to the candidate farthest from a strictly
        worse-rated limit (most solidly within the tied rating band).

        find_max=True (get_limit_max_idx): the mirror image — prefer the candidate
        closest to a strictly worse-rated limit; otherwise fall back to the candidate
        farthest from a strictly better-rated limit.
        """
        limits = np.array(self.get_limits(channel))[idx_candidates]
        limit_list = limit_list_sort(self.find_limits(channel.code))

        channel_times = channel.data.index[idx_candidates]
        channel_values = cast(np.ndarray, channel.get_data())[idx_candidates]

        limit_data = np.array([limit.get_data(channel_times, x_unit="s", y_unit=channel.unit) for limit in limit_list])

        limits_with_lower_rating = np.zeros_like(limit_data, dtype=bool)
        limits_with_higher_rating = np.zeros_like(limit_data, dtype=bool)
        for idx, (limit, data) in enumerate(zip(limit_list, limit_data)):
            limits_with_lower_rating[idx, :] = limit.rating < np.array([other_limit.rating for other_limit in limits])
            limits_with_higher_rating[idx, :] = limit.rating > np.array([other_limit.rating for other_limit in limits])

        diff_limits_lower_rating = np.abs(limit_data - channel_values)
        diff_limits_lower_rating[~limits_with_lower_rating] = np.nan

        diff_limits_higher_rating = np.abs(limit_data - channel_values)
        diff_limits_higher_rating[~limits_with_higher_rating] = np.nan

        diff_limits_higher_rating_min = np.full(len(idx_candidates), np.nan)
        idx_isnotnan = ~np.all(np.isnan(diff_limits_higher_rating), axis=0)
        diff_limits_higher_rating_min[idx_isnotnan] = np.nanmin(diff_limits_higher_rating[:, idx_isnotnan], axis=0)

        diff_limits_lower_rating_min = np.full(len(idx_candidates), np.nan)
        idx_isnotnan = ~np.all(np.isnan(diff_limits_lower_rating), axis=0)
        diff_limits_lower_rating_min[idx_isnotnan] = np.nanmin(diff_limits_lower_rating[:, idx_isnotnan], axis=0)

        if not find_max:
            diff_limits_higher_rating_min_max = np.nanmax(diff_limits_higher_rating_min) if not np.all(np.isnan(diff_limits_higher_rating_min)) else np.nan
            diff_limits_lower_rating_min_min = np.nanmin(diff_limits_lower_rating_min) if not np.all(np.isnan(diff_limits_lower_rating_min)) else np.nan

            idx_higher_lower = np.nanargmin([diff_limits_higher_rating_min_max, diff_limits_lower_rating_min_min])
            if idx_higher_lower == 0:
                return idx_candidates[np.nanargmax(diff_limits_higher_rating_min)]
            else:
                return idx_candidates[np.nanargmin(diff_limits_lower_rating_min)]
        else:
            diff_limits_higher_rating_min_min = np.nanmin(diff_limits_higher_rating_min) if not np.all(np.isnan(diff_limits_higher_rating_min)) else np.nan
            diff_limits_lower_rating_min_max = np.nanmax(diff_limits_lower_rating_min) if not np.all(np.isnan(diff_limits_lower_rating_min)) else np.nan

            idx_higher_lower = np.nanargmin([diff_limits_higher_rating_min_min, diff_limits_lower_rating_min_max])
            if idx_higher_lower == 0:
                return idx_candidates[np.nanargmin(diff_limits_higher_rating_min)]
            else:
                return idx_candidates[np.nanargmax(diff_limits_lower_rating_min)]

    def get_limit_min_idx(self, channel: Channel) -> int:
        limit_ratings = np.array(self.get_limit_ratings(channel, interpolate=True))
        idx_candidates = np.nonzero(np.min(limit_ratings) == limit_ratings)[0]
        if len(idx_candidates) == 1:
            return idx_candidates[0]
        return self._get_tie_break_idx(channel, idx_candidates, find_max=False)

    def get_limit_max_idx(self, channel: Channel) -> int:
        limit_ratings = np.array(self.get_limit_ratings(channel, interpolate=True))
        idx_candidates = np.nonzero(np.max(limit_ratings) == limit_ratings)[0]
        if len(idx_candidates) == 1:
            return idx_candidates[0]
        return self._get_tie_break_idx(channel, idx_candidates, find_max=True)

    def get_limit_min_y(self, channel: Channel, unit=None) -> float:
        idx = self.get_limit_min_idx(channel)
        return cast(np.ndarray, channel.get_data(unit=unit))[idx]

    def get_limit_max_y(self, channel: Channel, unit=None) -> float:
        idx = self.get_limit_max_idx(channel)
        return cast(np.ndarray, channel.get_data(unit=unit))[idx]

    def get_limit_min_x(self, channel: Channel) -> float:
        idx = self.get_limit_min_idx(channel)
        return channel.data.index[idx]

    def get_limit_max_x(self, channel: Channel) -> float:
        idx = self.get_limit_max_idx(channel)
        return channel.data.index[idx]

    def __repr__(self):
        return f"Limits({self.name})"


def limit_list_sort(limit_list: list[Limit], x: list = [0], sym=False) -> list:
    # TODO: convert unit to unit of first limit
    # TODO: add argument x to evaluate at different position than 0 (default=0)
    # TODO: evaluate at multiple positions an only consider positions where values are not the same and take order with most counts
    if sym:
        return sorted(limit_list, key=lambda limit: (np.abs(limit.func(0)), -1 if limit.upper and limit.func(0) >= 0 else 1 if limit.lower and limit.func(0) >= 0 else 1 if limit.upper and limit.func(0) < 0 else -1 if limit.lower and limit.func(0) < 0 else 0))
    else:
        return sorted(limit_list, key=lambda limit: (limit.func(0), -1 if limit.upper else 1 if limit.lower else 0))


def get_full_limits(limit_list: list[Limit]) -> list[Limit]:
    limit_list = limit_list_sort(limit_list)
    full_limit_list: list[Limit] = []
    for idx, limit in enumerate(limit_list):
        if idx == 0:
            assert limit.upper
            full_limit_list.append(limit)
            continue
        elif idx == len(limit_list) - 1:
            assert limit.lower
            full_limit_list.append(limit)
            continue

        previous_limit = limit_list[idx - 1]
        if previous_limit.upper and limit.upper:
            tmp_limit = copy.deepcopy(previous_limit)
            tmp_limit.func = limit_list[idx].func
            tmp_limit.upper = False
            tmp_limit.lower = True

            full_limit_list.append(tmp_limit)
            full_limit_list.append(limit)
        if previous_limit.lower and limit.lower:
            pass
    return full_limit_list


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
    filtered_limit_list: list[Limit] = []
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


def get_limit_upper_data(x, limit: Limit, limit_list, x_unit, y_unit) -> np.ndarray | float:
    if limit.lower and not limit.upper:
        limit_list = limit_list_sort(limit_list)
        limit_list = limit_list_unique(limit_list, x=x, x_unit=x_unit, y_unit=y_unit)
        idx = limit_list.index(limit) + 1
        if idx >= len(limit_list):
            return np.full(len(x), np.inf) if isinstance(x, np.ndarray) else np.inf
        else:
            return limit_list[idx].get_data(x=x, x_unit=x_unit, y_unit=y_unit)
    else:
        return limit.get_data(x=x, x_unit=x_unit, y_unit=y_unit)


def get_limit_lower_data(x: float | np.ndarray, limit: Limit, limit_list, x_unit, y_unit) -> np.ndarray | float:
    if limit.upper and not limit.lower:
        limit_list = limit_list_sort(limit_list)
        limit_list = limit_list_unique(limit_list, x=x, x_unit=x_unit, y_unit=y_unit)
        idx = limit_list.index(limit) - 1
        if idx < 0:
            return np.full(len(x), -np.inf) if isinstance(x, np.ndarray) else -np.inf
        else:
            return limit_list[idx].get_data(x=x, x_unit=x_unit, y_unit=y_unit)
    else:
        return limit.get_data(x=x, x_unit=x_unit, y_unit=y_unit)


def get_limit_min_color_from_rating(rating, limit_list):
    limits = sorted(limit_list, key=lambda limit: limit.rating)
    for idx, limit in enumerate(limits):
        if rating == limit.rating:
            return limit.color
        if idx >= 1 and limits[idx-1].rating < rating < limit.rating:
            return limits[idx-1].color
