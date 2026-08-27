from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

import numpy as np

from pyisomme.unit import Unit

if TYPE_CHECKING:
    from pyisomme.channel import Channel
    from pyisomme.limit import Limit
    from pyisomme.limit_set import LimitSet


def _interpolate_rating(
    value: float, thresholds: np.ndarray, ratings: np.ndarray
) -> float:
    """Interpolate finite ratings while treating infinities as step boundaries."""
    if np.isnan(value):
        return np.nan

    right = int(np.searchsorted(thresholds, value, side="right"))
    if right == 0:
        return float(ratings[0])

    left = right - 1
    if thresholds[left] == value or right == len(thresholds):
        return float(ratings[left])

    left_rating = ratings[left]
    right_rating = ratings[right]
    if np.isfinite(left_rating) and np.isfinite(right_rating):
        fraction = (value - thresholds[left]) / (
            thresholds[right] - thresholds[left]
        )
        return float(left_rating + fraction * (right_rating - left_rating))
    if np.isfinite(left_rating):
        return float(left_rating)
    if np.isfinite(right_rating):
        return float(right_rating)
    return float(left_rating)


class LimitEvaluation:
    """Lazy evaluation of one immutable :class:`LimitSet` for one channel snapshot."""

    def __init__(self, limit_set: LimitSet, channel: Channel) -> None:
        self.limit_set = limit_set
        self.channel = channel
        self.times = np.asarray(channel.data.index, dtype=float).copy()
        self.values = np.asarray(channel.get_data(), dtype=float).copy()
        self.matched_limits = tuple(limit_set.find_limits(channel.code))

        if not self.matched_limits:
            raise ValueError(f"No limits found for channel '{channel.code}'.")

    @cached_property
    def thresholds(self) -> np.ndarray:
        """Converted thresholds in declaration order (limits x samples)."""
        thresholds = np.asarray(
            [
                limit.get_data(self.times, x_unit="s", y_unit=self.channel.unit)
                for limit in self.matched_limits
            ],
            dtype=float,
        )
        if not np.all(np.isfinite(thresholds)):
            raise ValueError(
                f"Limits for channel '{self.channel.code}' produced non-finite values."
            )
        return thresholds

    @cached_property
    def order(self) -> np.ndarray:
        """One threshold order, established near the conventional ``x=0`` origin."""
        reference_idx = int(np.argmin(np.abs(self.times)))
        return np.asarray(
            sorted(
                range(len(self.matched_limits)),
                key=lambda idx: (
                    self.thresholds[idx, reference_idx],
                    -1
                    if self.matched_limits[idx].upper
                    else 1
                    if self.matched_limits[idx].lower
                    else 0,
                ),
            ),
            dtype=int,
        )

    @cached_property
    def ordered_limits(self) -> tuple[Limit, ...]:
        return tuple(self.matched_limits[idx] for idx in self.order)

    @cached_property
    def ordered_thresholds(self) -> np.ndarray:
        thresholds = self.thresholds[self.order]
        differences = np.diff(thresholds, axis=0)
        reversed_order = differences < 0
        if np.any(reversed_order):
            limit_idx, sample_idx = np.argwhere(reversed_order)[0]
            before = self.ordered_limits[int(limit_idx)]
            after = self.ordered_limits[int(limit_idx) + 1]
            raise ValueError(
                f"Limits {before} and {after} change order for channel "
                f"'{self.channel.code}' at x={self.times[int(sample_idx)]} s."
            )
        return thresholds

    def _require_ratings(self) -> np.ndarray:
        ratings: list[float] = []
        unrated: list[str | None] = []
        for limit in self.ordered_limits:
            if limit.rating is None:
                unrated.append(limit.name)
            else:
                ratings.append(limit.rating)
        if unrated:
            raise ValueError(
                f"Cannot rate channel '{self.channel.code}': limits {unrated} "
                "declare no rating."
            )
        return np.asarray(ratings, dtype=float)

    @cached_property
    def interpolated_ratings(self) -> np.ndarray:
        ratings = self._require_ratings()
        return np.asarray(
            [
                _interpolate_rating(
                    channel_value,
                    self.ordered_thresholds[:, sample_idx],
                    ratings,
                )
                for sample_idx, channel_value in enumerate(self.values)
            ],
            dtype=float,
        )

    @cached_property
    def discrete_ratings(self) -> np.ndarray:
        ratings = self._require_ratings()
        output = np.full(len(self.values), np.nan)
        for sample_idx, channel_value in enumerate(self.values):
            if np.isnan(channel_value):
                continue
            for limit_idx, limit in enumerate(self.ordered_limits):
                threshold = self.ordered_thresholds[limit_idx, sample_idx]
                if limit.upper and channel_value < threshold:
                    output[sample_idx] = ratings[limit_idx]
                    break
                if limit.lower and channel_value >= threshold:
                    output[sample_idx] = ratings[limit_idx]
                    break
            if np.isnan(output[sample_idx]):
                raise ValueError(
                    f"No limit covers channel '{self.channel.code}' at "
                    f"x={self.times[sample_idx]} s, y={channel_value}."
                )
        return output

    def ratings(self, interpolate: bool = True) -> np.ndarray:
        return self.interpolated_ratings if interpolate else self.discrete_ratings

    def get_limit_min_rating(self, interpolate: bool = True) -> float:
        return float(np.nanmin(self.ratings(interpolate)))

    def get_limit_max_rating(self, interpolate: bool = True) -> float:
        return float(np.nanmax(self.ratings(interpolate)))

    @cached_property
    def selected_limits(self) -> tuple[Limit, ...]:
        matching = np.zeros_like(self.ordered_thresholds, dtype=bool)
        for idx, limit in enumerate(self.ordered_limits):
            threshold = self.ordered_thresholds[idx]
            matching[idx] = (
                (self.values == threshold)
                | ((limit.upper is True) & (self.values < threshold))
                | ((limit.lower is True) & (self.values > threshold))
            )

        difference = np.abs(self.ordered_thresholds - self.values)
        difference[~matching] = np.inf
        uncovered = np.all(np.isinf(difference), axis=0)
        if np.any(uncovered):
            sample_idx = int(np.flatnonzero(uncovered)[0])
            raise ValueError(
                f"No limit covers channel '{self.channel.code}' at "
                f"x={self.times[sample_idx]} s, y={self.values[sample_idx]}."
            )
        indices = np.argmin(difference, axis=0)
        return tuple(self.ordered_limits[idx] for idx in indices)

    def get_limit_min(self) -> Limit:
        idx = int(np.nanargmin(self.interpolated_ratings))
        return self.selected_limits[idx]

    def get_limit_max(self) -> Limit:
        idx = int(np.nanargmax(self.interpolated_ratings))
        return self.selected_limits[idx]

    def get_limit_min_color(self) -> str:
        return self.get_limit_min().color

    def get_limit_max_color(self) -> str:
        return self.get_limit_max().color

    def _get_tie_break_idx(self, idx_candidates: np.ndarray, find_max: bool) -> int:
        selected = np.asarray(self.selected_limits, dtype=object)[idx_candidates]
        selected_ratings = np.asarray([limit.rating for limit in selected], dtype=float)
        ratings = self._require_ratings()
        differences = np.abs(
            self.ordered_thresholds[:, idx_candidates] - self.values[idx_candidates]
        )

        lower = ratings[:, None] < selected_ratings[None, :]
        higher = ratings[:, None] > selected_ratings[None, :]

        def nearest(mask: np.ndarray) -> np.ndarray:
            candidates = np.where(mask, differences, np.nan)
            output = np.full(len(idx_candidates), np.nan)
            present = ~np.all(np.isnan(candidates), axis=0)
            output[present] = np.nanmin(candidates[:, present], axis=0)
            return output

        lower_distance = nearest(lower)
        higher_distance = nearest(higher)

        if not find_max:
            higher_metric = (
                np.nanmax(higher_distance)
                if not np.all(np.isnan(higher_distance))
                else np.nan
            )
            lower_metric = (
                np.nanmin(lower_distance)
                if not np.all(np.isnan(lower_distance))
                else np.nan
            )
            metrics = np.asarray([higher_metric, lower_metric])
            if not np.all(np.isnan(metrics)):
                if np.nanargmin(metrics) == 0:
                    return int(idx_candidates[np.nanargmax(higher_distance)])
                return int(idx_candidates[np.nanargmin(lower_distance)])
        else:
            higher_metric = (
                np.nanmin(higher_distance)
                if not np.all(np.isnan(higher_distance))
                else np.nan
            )
            lower_metric = (
                np.nanmax(lower_distance)
                if not np.all(np.isnan(lower_distance))
                else np.nan
            )
            metrics = np.asarray([higher_metric, lower_metric])
            if not np.all(np.isnan(metrics)):
                if np.nanargmin(metrics) == 0:
                    return int(idx_candidates[np.nanargmin(higher_distance)])
                return int(idx_candidates[np.nanargmax(lower_distance)])
        return int(idx_candidates[0])

    def _get_limit_extreme_idx(self, find_max: bool) -> int:
        ratings = self.interpolated_ratings
        if np.all(np.isnan(ratings)):
            raise ValueError(
                f"Limit evaluation for channel '{self.channel.code}' produced "
                "only NaN ratings."
            )
        extreme = np.nanmax(ratings) if find_max else np.nanmin(ratings)
        candidates = np.flatnonzero(ratings == extreme)
        if len(candidates) == 1:
            return int(candidates[0])
        return self._get_tie_break_idx(candidates, find_max=find_max)

    def get_limit_min_idx(self) -> int:
        return self._get_limit_extreme_idx(find_max=False)

    def get_limit_max_idx(self) -> int:
        return self._get_limit_extreme_idx(find_max=True)

    def get_limit_min_y(self, unit: str | Unit | int | None = None) -> float:
        value = self.values[self.get_limit_min_idx()]
        if unit is not None:
            value *= Unit(self.channel.unit).to(Unit(unit))
        return float(value)

    def get_limit_max_y(self, unit: str | Unit | int | None = None) -> float:
        value = self.values[self.get_limit_max_idx()]
        if unit is not None:
            value *= Unit(self.channel.unit).to(Unit(unit))
        return float(value)
