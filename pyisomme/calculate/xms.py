from __future__ import annotations

import copy
import logging
from typing import Literal

import numpy as np
import pandas as pd

from pyisomme.channel import Channel
from pyisomme.utils import debug_logging

logger = logging.getLogger("pyisomme.calculate")


@debug_logging(logger)
def calculate_xms(
    channel: Channel, min_delta_t: float = 3, method: Literal["S", "C"] = "S"
) -> Channel:
    """
    Calculate the level exceeded for a specified duration (typically 3 ms).

    The input samples are interpreted as a piecewise-linear signal, so threshold
    crossings between samples contribute their fractional duration. ``S`` requires one
    continuous exceedance interval; ``C`` sums all exceedance intervals.

    :param channel: Channel to evaluate.
    :param min_delta_t: Required exceedance duration in milliseconds.
    :param method: ``S`` for a single continuous interval or ``C`` for cumulative time.
    :return: Scalar xms channel.
    """
    if not 0 < min_delta_t < 10:
        raise ValueError("min_delta_t must be between 0 and 10 ms")
    if method not in ("S", "C"):
        raise ValueError(f"Method {method} not supported. Use 'S' or 'C'.")

    min_delta_t_seconds = min_delta_t * 1e-3
    time_array = np.asarray(channel.data.index, dtype=float)
    value_array = np.asarray(channel.get_data(), dtype=float)

    if len(time_array) < 2:
        raise ValueError("xms calculation requires at least two samples")
    if not np.all(np.isfinite(time_array)):
        raise ValueError("xms calculation requires finite time values")
    if not np.all(np.diff(time_array) > 0):
        raise ValueError("xms calculation requires a strictly increasing time index")
    if not np.all(np.isfinite(value_array)):
        raise ValueError("xms calculation requires finite channel values")
    if time_array[-1] - time_array[0] < min_delta_t_seconds:
        raise ValueError(
            "channel duration is shorter than the requested xms duration "
            f"({min_delta_t:g} ms)"
        )

    # Search for the highest acceleration level whose exceedance duration is at
    # least min_delta_t. The signal between samples is treated as a straight line,
    # allowing the threshold-crossing time to be interpolated.
    lower = float(np.min(value_array))
    upper = float(np.max(value_array))
    result_intervals = [(float(time_array[0]), float(time_array[-1]))]
    merge_tolerance = max(1.0, float(time_array[-1] - time_array[0])) * 1e-14

    for _ in range(64):
        if lower == upper:
            break

        level = (lower + upper) / 2
        intervals: list[tuple[float, float]] = []

        # Build all intervals where the piecewise-linear signal is at or above
        # the candidate level.
        for t0, t1, value0, value1 in zip(
            time_array[:-1],
            time_array[1:],
            value_array[:-1],
            value_array[1:],
        ):
            if value0 >= level and value1 >= level:
                start, end = float(t0), float(t1)
            elif value0 < level <= value1:
                crossing = t0 + (level - value0) * (t1 - t0) / (value1 - value0)
                start, end = float(crossing), float(t1)
            elif value0 >= level > value1:
                crossing = t0 + (level - value0) * (t1 - t0) / (value1 - value0)
                start, end = float(t0), float(crossing)
            else:
                continue

            # Adjacent sample segments belonging to the same exceedance event
            # are combined into one interval.
            if intervals and start <= intervals[-1][1] + merge_tolerance:
                intervals[-1] = (intervals[-1][0], max(intervals[-1][1], end))
            else:
                intervals.append((start, end))

        durations = [end - start for start, end in intervals]
        if method == "S":
            exceedance_duration = max(durations, default=0.0)
        else:
            exceedance_duration = float(np.sum(durations))

        if exceedance_duration >= min_delta_t_seconds:
            lower = level
            result_intervals = intervals
        else:
            upper = level

    result = lower

    result_t1 = None
    result_t2 = None
    if method == "S":
        result_t1, interval_end = max(
            result_intervals, key=lambda interval: interval[1] - interval[0]
        )
        result_t2 = min(result_t1 + min_delta_t_seconds, interval_end)

    new_code = channel.code.set(
        fine_location_2=f"{min_delta_t:.0f}{method}", filter_class="X"
    )
    new_info = copy.deepcopy(channel.info)
    new_info.update(
        {
            "Data source": "calculation",
        }
    ).add(
        {
            ".Analysis start time": float(time_array[0]),
            ".Analysis end time": float(time_array[-1]),
        }
    )
    if method == "S":
        new_info.add(
            {
                ".Start time": result_t1,
                ".End time": result_t2,
            }
        )
    return Channel(
        new_code, data=pd.DataFrame([result]), unit=channel.unit, info=new_info
    )
