from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from pyisomme.channel import Channel
from pyisomme.unit import Unit, g0
from pyisomme.utils import debug_logging

logger = logging.getLogger("pyisomme.calculate")


@debug_logging(logger)
def calculate_hic(channel: Channel, max_delta_t: float) -> Channel:
    """
    Computes head injury criterion (HIC)
    HIC15 --> max_delta_t = 15
    HIC36 --> max_delta_t = 36

    REFERENCES
    - https://en.wikipedia.org/wiki/Head_injury_criterion

    :param channel: Head resultant acceleration Channel-object
    :param max_delta_t: in ms
    :return:
    """
    if not 0 < max_delta_t < 100:
        raise ValueError("max_delta_t must be between 0 and 100 ms")

    channel = channel.convert_unit(Unit(g0))

    max_delta_t *= 1e-3
    time_array = np.array(channel.data.index)
    res = 0
    res_t1 = None
    res_t2 = None

    if np.all(channel.get_data() >= 0):  # this is the case for resultant channels
        # Integral can only be positive -> extrema expected for maximum timespan (more runtime efficient)
        for idx_1, t1 in enumerate(time_array[:-1]):
            upper_limit_idx = (t1 + max_delta_t <= time_array).argmax()
            idx_2 = upper_limit_idx - 1
            t2 = time_array[idx_2]
            a_int = np.trapz(
                channel.get_data(time_array[idx_1 : idx_2 + 1]),
                time_array[idx_1 : idx_2 + 1],
            )
            new_res = (t2 - t1) * (1 / (t2 - t1) * a_int) ** 2.5
            if new_res > res:
                res = new_res
                res_t1 = t1
                res_t2 = t2
    else:
        # Integral can be negative -> extrema can occur for smaller timespan
        for idx_1, t1 in enumerate(time_array[:-1]):
            upper_limit_idx = (t1 + max_delta_t <= time_array).argmax()
            for idx2_offset, t2 in enumerate(time_array[idx_1 + 1 : upper_limit_idx]):
                idx_2 = idx_1 + 1 + idx2_offset
                a_int = np.trapz(
                    channel.get_data(time_array[idx_1 : idx_2 + 1]),
                    time_array[idx_1 : idx_2 + 1],
                )
                if a_int < 0:
                    continue
                new_res = (t2 - t1) * (1 / (t2 - t1) * a_int) ** 2.5
                if new_res > res:
                    res = new_res
                    res_t1 = t1
                    res_t2 = t2

    return Channel(
        code=channel.code.set(
            main_location="HICR",
            fine_location_1="00",
            fine_location_2=f"{(max_delta_t * 1e3):.0f}",
            physical_dimension="00",
            filter_class="X",
        ),
        data=pd.DataFrame([res]),
        unit="1",
        info=[
            ("Data source", "calculation"),
            ("Name of the channel", f"HIC VALUE {max_delta_t * 1e3:.0f}"),
            ("Number of samples", 1),
            (".Start time", res_t1),
            (".End time", res_t2),
            (".Analysis start time", channel.data.index[0]),
            (".Analysis end time", channel.data.index[-1]),
        ],
    )
