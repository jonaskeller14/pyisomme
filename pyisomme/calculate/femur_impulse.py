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
    """
    References:
    - references/IIHS/small_overlap_rating_protocol.pdf

    :param channel: Compressive Force Channel
    :param y_end: The force value at which to stop the impulse calculation. Default is -4050 N.
    :return: A Channel with time and scalar data for the femur impulse.
    """
    x = channel.data.index
    y = channel.get_data(unit="N")

    idx_min = int(np.argmin(y))
    before_peak = np.nonzero((y >= 0) & (np.arange(len(x)) < idx_min))[0]
    idx_start = int(before_peak[-1]) if len(before_peak) else 0
    if y[idx_min] >= y_end:
        #FIXME: A pulse that never reaches the cutoff has no post-peak crossing. --> return zero impulse then might be more correct
        idx_end = idx_min
    else:
        after_peak = np.nonzero((y > y_end) & (np.arange(len(x)) > idx_min))[0]
        idx_end = int(after_peak[0]) if len(after_peak) else len(x) - 1

    data = trapezoid(y[idx_start:idx_end + 1], x[idx_start:idx_end + 1])

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
