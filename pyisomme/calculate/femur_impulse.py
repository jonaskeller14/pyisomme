from __future__ import annotations

from pyisomme.channel import Channel
from pyisomme.unit import Unit
from pyisomme.utils import debug_logging

import logging
import numpy as np
import pandas as pd
from scipy.integrate import trapezoid


logger = logging.getLogger("pyisomme.calculate")


@debug_logging(logger)
def calculate_femur_impulse(channel: Channel, y_end: float = -4050) -> Channel:
    x = channel.data.index
    y = channel.get_data(unit="N")

    idx_min = int(np.argmin(y))
    idx_start = np.nonzero((y >= 0) * (np.arange(len(x)) < idx_min))[0][-1]
    if y[idx_min] >= y_end:
        idx_end = idx_min
    else:
        idx_end = np.nonzero((y > y_end) * (np.arange(len(x)) > idx_min))[0][0]

    data = trapezoid(y[idx_start:idx_end], x[idx_start:idx_end])

    return Channel(code=channel.code.set(main_location="KTHC", physical_dimension="IM", filter_class="X"),
                   data=pd.DataFrame([data]),
                   unit=channel.unit * Unit("s"),
                   info=channel.info.update({
                       "Data source": "calculation",
                   }).add({
                       ".Channel 001": channel.code,
                       ".Filter": channel.code.filter_class,
                       ".Start time": x[idx_start],
                       ".End time": x[idx_end],
                   }))
