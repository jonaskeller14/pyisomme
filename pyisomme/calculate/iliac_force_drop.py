from __future__ import annotations

from pyisomme.channel import Channel
from pyisomme.utils import debug_logging

import logging
import pandas as pd


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

    ifd = channel.get_data(t=time_array + delta_t) - channel.get_data(t=time_array)

    return Channel(code="????????????????",
                   data=pd.DataFrame(ifd, index=time_array),
                   unit=channel.unit,
                   info=channel.info.update({"Data source": "calculation",}))
