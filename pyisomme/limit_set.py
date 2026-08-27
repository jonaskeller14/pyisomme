from __future__ import annotations

import fnmatch
import logging
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

import numpy as np

from pyisomme.limit_evaluation import LimitEvaluation

if TYPE_CHECKING:
    from pyisomme.channel import Channel
    from pyisomme.code import Code
    from pyisomme.limit import Limit
    from pyisomme.unit import Unit


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LimitSet:
    name: str = "Unnamed Limits"
    limits: tuple[Limit, ...] = ()

    def __add__(self, other: LimitSet) -> LimitSet:
        if not isinstance(other, LimitSet):
            return NotImplemented
        return LimitSet(
            name=f"{self.name} + {other.name}",
            limits=self.limits + other.limits,
        )

    def extend(self, limits: tuple[Limit, ...]) -> LimitSet:
        """Return a new set with ``limits`` appended in declaration order."""
        return replace(self, limits=self.limits + limits)

    def evaluate(self, channel: Channel) -> LimitEvaluation:
        """Create a lazy, channel-specific snapshot of this limit set."""
        return LimitEvaluation(self, channel)

    def find_limits(self, *codes: Code | str) -> list:
        """
        Return each limit that matches at least one channel code.

        Limit code patterns use case-sensitive ``fnmatch`` syntax.  The returned
        limits preserve declaration order and never contain the same limit more
        than once.
        """
        output: list[Limit] = []
        for limit in self.limits:
            for code in codes:
                if code is None:
                    continue
                for code_pattern in limit.code_patterns:
                    if fnmatch.fnmatchcase(code, code_pattern):
                        output.append(limit)
                        break
                else:
                    continue
                break
        return output

    def get_limits(self, channel: Channel) -> list[Limit]:
        return list(self.evaluate(channel).selected_limits)

    def get_limit_max(self, channel: Channel) -> Limit:
        return self.evaluate(channel).get_limit_max()

    def get_limit_min(self, channel: Channel) -> Limit:
        return self.evaluate(channel).get_limit_min()

    def get_limit_ratings(
        self, channel: Channel, interpolate: bool = True
    ) -> list[float]:
        return list(self.evaluate(channel).ratings(interpolate=interpolate))

    def get_limit_max_rating(self, channel: Channel, interpolate: bool = True) -> float:
        return self.evaluate(channel).get_limit_max_rating(interpolate)

    def get_limit_min_rating(self, channel: Channel, interpolate: bool = True) -> float:
        return self.evaluate(channel).get_limit_min_rating(interpolate)

    def get_limit_colors(self, channel: Channel) -> list[str]:
        return [limit.color for limit in self.evaluate(channel).selected_limits]

    def get_limit_min_color(self, channel: Channel) -> str:
        return self.evaluate(channel).get_limit_min_color()

    def get_limit_max_color(self, channel: Channel) -> str:
        return self.evaluate(channel).get_limit_max_color()

    def get_limit_min_idx(self, channel: Channel) -> int:
        return self.evaluate(channel).get_limit_min_idx()

    def get_limit_max_idx(self, channel: Channel) -> int:
        return self.evaluate(channel).get_limit_max_idx()

    def get_limit_min_y(
        self, channel: Channel, unit: str | Unit | int | None = None
    ) -> float:
        return self.evaluate(channel).get_limit_min_y(unit)

    def get_limit_max_y(
        self, channel: Channel, unit: str | Unit | int | None = None
    ) -> float:
        return self.evaluate(channel).get_limit_max_y(unit)

    def get_limit_min_x(self, channel: Channel) -> float:
        idx = self.get_limit_min_idx(channel)
        return channel.data.index[idx]

    def get_limit_max_x(self, channel: Channel) -> float:
        idx = self.get_limit_max_idx(channel)
        return channel.data.index[idx]

    def __repr__(self) -> str:
        return f"LimitSet({self.name})"


def limit_list_sort(
    limit_list: list[Limit],
    x: float | list[float] | np.ndarray = 0.0,
    x_unit: str | Unit | int | None = None,
    y_unit: str | Unit | int | None = None,
    sym: bool = False,
) -> list[Limit]:
    """Order limits from their converted values at one or more x positions.

    Positions where two limits have the same value cast no ordering vote. When
    curves disagree across positions, the order supported by the most positions
    wins; the position nearest zero and the boundary direction break ties.
    """
    if not limit_list:
        return []

    x_values = np.atleast_1d(np.asarray(x, dtype=float))
    if len(x_values) == 0:
        raise ValueError("At least one x position is required to sort limits.")
    x_unit = limit_list[0].x_unit if x_unit is None else x_unit
    y_unit = limit_list[0].y_unit if y_unit is None else y_unit
    if x_unit is None or y_unit is None:
        raise ValueError("Limits require x and y units before they can be sorted.")

    values = np.asarray(
        [
            limit.get_data(x_values, x_unit=x_unit, y_unit=y_unit)
            for limit in limit_list
        ],
        dtype=float,
    )
    if not np.all(np.isfinite(values)):
        raise ValueError("Limits produced non-finite values while being sorted.")

    compared_values = np.abs(values) if sym else values
    scores = np.zeros(len(limit_list), dtype=int)
    for first in range(len(limit_list)):
        for second in range(first + 1, len(limit_list)):
            different = ~np.isclose(compared_values[first], compared_values[second])
            lower_votes = np.count_nonzero(
                different & (compared_values[first] < compared_values[second])
            )
            higher_votes = np.count_nonzero(
                different & (compared_values[first] > compared_values[second])
            )
            if lower_votes > higher_votes:
                scores[first] -= 1
                scores[second] += 1
            elif higher_votes > lower_votes:
                scores[first] += 1
                scores[second] -= 1

    reference_idx = int(np.argmin(np.abs(x_values)))

    def direction_key(idx: int) -> int:
        limit = limit_list[idx]
        value = values[idx, reference_idx]
        if not sym:
            return -1 if limit.upper else 1 if limit.lower else 0
        if (limit.upper and value >= 0) or (limit.lower and value < 0):
            return -1
        if (limit.lower and value >= 0) or (limit.upper and value < 0):
            return 1
        return 0

    order = sorted(
        range(len(limit_list)),
        key=lambda idx: (
            scores[idx],
            compared_values[idx, reference_idx],
            direction_key(idx),
        ),
    )
    return [limit_list[idx] for idx in order]


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
            tmp_limit = replace(
                previous_limit,
                func=limit_list[idx].func,
                upper=False,
                lower=True,
            )

            full_limit_list.append(tmp_limit)
            full_limit_list.append(limit)
        if previous_limit.lower and limit.lower:
            pass
    return full_limit_list


def limit_list_unique(
    limit_list: list[Limit],
    x: float | np.ndarray,
    x_unit: str | Unit | int | None,
    y_unit: str | Unit | int | None,
    compare_code_patterns: bool = False,
    compare_func: bool = True,
    compare_x_unit: bool = False,
    compare_y_unit: bool = False,
    compare_name: bool = True,
    compare_rating: bool = False,
    compare_upper: bool = True,
    compare_lower: bool = True,
) -> list[Limit]:
    filtered_limit_list: list[Limit] = []
    for limit in limit_list:
        add = True
        for filtered_limit in filtered_limit_list:
            if (
                compare_code_patterns
                and limit.code_patterns != filtered_limit.code_patterns
            ):
                continue

            if compare_func and not np.all(
                limit.get_data(x, x_unit=x_unit, y_unit=y_unit)
                == filtered_limit.get_data(x, x_unit=x_unit, y_unit=y_unit)
            ):
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


def get_limit_upper_data(
    x: float | np.ndarray,
    limit: Limit,
    limit_list: list[Limit],
    x_unit: str | Unit | int | None,
    y_unit: str | Unit | int | None,
) -> np.ndarray | float:
    if limit.lower and not limit.upper:
        limit_list = limit_list_sort(limit_list, x=x, x_unit=x_unit, y_unit=y_unit)
        limit_list = limit_list_unique(limit_list, x=x, x_unit=x_unit, y_unit=y_unit)
        idx = limit_list.index(limit) + 1
        if idx >= len(limit_list):
            return np.full(len(x), np.inf) if isinstance(x, np.ndarray) else np.inf
        else:
            return limit_list[idx].get_data(x=x, x_unit=x_unit, y_unit=y_unit)
    else:
        return limit.get_data(x=x, x_unit=x_unit, y_unit=y_unit)


def get_limit_lower_data(
    x: float | np.ndarray,
    limit: Limit,
    limit_list: list[Limit],
    x_unit: str | Unit | int | None,
    y_unit: str | Unit | int | None,
) -> np.ndarray | float:
    if limit.upper and not limit.lower:
        limit_list = limit_list_sort(limit_list, x=x, x_unit=x_unit, y_unit=y_unit)
        limit_list = limit_list_unique(limit_list, x=x, x_unit=x_unit, y_unit=y_unit)
        idx = limit_list.index(limit) - 1
        if idx < 0:
            return np.full(len(x), -np.inf) if isinstance(x, np.ndarray) else -np.inf
        else:
            return limit_list[idx].get_data(x=x, x_unit=x_unit, y_unit=y_unit)
    else:
        return limit.get_data(x=x, x_unit=x_unit, y_unit=y_unit)


def get_limit_min_color_from_rating(
    rating: float, limit_list: list[Limit]
) -> str | None:
    def require_rating(limit: Limit) -> float:
        if limit.rating is None:
            raise ValueError(f"Limit {limit} declares no rating.")
        return limit.rating

    limits = sorted(
        (limit for limit in limit_list if limit.rating is not None),
        key=require_rating,
    )
    for idx, limit in enumerate(limits):
        limit_rating = require_rating(limit)
        if rating == limit_rating:
            return limit.color
        if idx >= 1 and require_rating(limits[idx - 1]) < rating < limit_rating:
            return limits[idx - 1].color
    return None
