from __future__ import annotations

from pyisomme.channel import Channel
from pyisomme.utils import debug_logging

import logging
import numpy as np
import pandas as pd
from typing import Literal


logger = logging.getLogger("pyisomme.calculate")


@debug_logging(logger)
def calculate_xms(channel: Channel, min_delta_t: float = 3, method: Literal["S", "C"] = "S") -> Channel:
    """
    Exceedance value (typical 3ms)
    :param channel:
    :param min_delta_t: in ms
    :param method: S (for single peak) or C (for cumulative)
    :return:
    """
    assert 0 < min_delta_t < 10

    min_delta_t *= 1e-3  # convert to s
    time_array = channel.data.index
    value_array = channel.get_data()

    res = 0
    res_t1 = None
    res_t2 = None

    if method == "S":
        for t1 in time_array:
            t2_pts = time_array[time_array >= t1 + min_delta_t]
            if len(t2_pts) == 0:
                break
            t2 = t2_pts[0]
            indices = np.where((t1 <= time_array)*(time_array <= t2))
            values = value_array[indices]

            new_res = np.min(values)

            if new_res > res:
                res = new_res
                res_t1 = t1
                res_t2 = t2

    elif method == "C":
        dt = np.append(np.diff(time_array), 0)

        for value in np.sort(value_array)[::-1]:
            greater_indices = np.nonzero(value_array >= value)[0]
            greater_indices_left = np.array([greater_idx for greater_idx in greater_indices if (greater_idx+1) in greater_indices], dtype=int)

            if np.sum(dt[greater_indices_left]) >= min_delta_t:
                res = value
                res_t1 = time_array[greater_indices_left[0]]
                res_t2 = time_array[greater_indices_left[-1] + 1]  #  +1 because right bound was delete
                break
    else:
        raise ValueError(f"Method {method} not supported. Use 'S' or 'C'.")

    new_code = channel.code.set(fine_location_2=f"{(min_delta_t*1e3):.0f}{method}",
                                filter_class="X")
    new_info = channel.info
    new_info.update({
        "Data source": "calculation",
    }).add({
        ".Analysis start time": np.min(time_array),
        ".Analysis end time": np.max(time_array),
    })
    if method == "S":
        new_info.add({
            ".Start time": res_t1,
            ".End time": res_t2,
        })
    return Channel(new_code, data=pd.DataFrame([res]), unit=channel.unit, info=new_info)
