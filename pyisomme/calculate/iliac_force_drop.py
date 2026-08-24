from __future__ import annotations

import logging

import pandas as pd

from pyisomme.channel import Channel
from pyisomme.utils import debug_logging

logger = logging.getLogger("pyisomme.calculate")


@debug_logging(logger)
def calculate_iliac_force_drop(channel: Channel, delta_t: float = 0.001) -> Channel:
    """
    References:
    - references/Euro-NCAP/tb-021-data-acquisition-and-injury-calculation-v402.pdf
    :param channel: Iliac Force channel
    :param delta_t:
    :return:
    """
    time_array = channel.data.index
    future_time = time_array + delta_t
    valid = future_time <= time_array[-1]
    valid_time = time_array[valid]
    valid_future_time = future_time[valid]

    ifd = channel.get_data(t=valid_future_time) - channel.get_data(t=valid_time)

    return Channel(
        code="????????????????",
        data=pd.DataFrame(ifd, index=valid_time),
        unit=channel.unit,
        info=channel.info.update(
            {
                "Data source": "calculation",
            }
        ),
    )
