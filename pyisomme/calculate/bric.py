from __future__ import annotations

from pyisomme.channel import Channel
from pyisomme.utils import debug_logging

import logging
import numpy as np
import pandas as pd
from typing import Literal


logger = logging.getLogger("pyisomme.calculate")


@debug_logging(logger)
def calculate_bric(c_av_x: Channel,
                   c_av_y: Channel,
                   c_av_z: Channel,
                   critical_av_x: float | None = None,
                   critical_av_y: float | None = None,
                   critical_av_z: float | None = None,
                   method: Literal["MPS", "CSDM", "Average of CSDM and MPS"] = "MPS") -> Channel:
    """
    References:
    - references/NHTSA/Stapp2013Takhounts.pdf
    - references/DIAdem/BrIC.pdf
    :param c_av_x:
    :param c_av_y:
    :param c_av_z:
    :param critical_av_x: unit rad/s
    :param critical_av_y: unit rad/s
    :param critical_av_z: unit rad/s
    :return:
    """
    if method not in ("MPS", "CSDM", "Average of CSDM and MPS"):
        raise ValueError(f"Unknown BrIC method: {method}")

    if critical_av_x is None:
        critical_av_x = {
            "MPS": 66.30,
            "CSDM": 66.20,
            "Average of CSDM and MPS": 66.25,
        }[method]  # rad/s
    if critical_av_y is None:
        critical_av_y = {
            "MPS": 53.80,
            "CSDM": 59.10,
            "Average of CSDM and MPS": 56.45,
        }[method]  # rad/s
    if critical_av_z is None:
        critical_av_z = {
            "MPS": 41.50,
            "CSDM": 44.25,
            "Average of CSDM and MPS": 42.87,
        }[method]  # rad/s

    c_av_x = c_av_x.convert_unit("rad/s")
    c_av_y = c_av_y.convert_unit("rad/s")
    c_av_z = c_av_z.convert_unit("rad/s")

    av_x = c_av_x.get_data()
    av_y = c_av_y.get_data()
    av_z = c_av_z.get_data()

    bric = np.sqrt((np.max(np.abs(av_x))/critical_av_x)**2 + (np.max(np.abs(av_y))/critical_av_y)**2 + (np.max(np.abs(av_z))/critical_av_z)**2)

    return Channel(
        code=c_av_x.code.set(main_location="BRIC", physical_dimension="00", direction="0", filter_class="X"),
        data=pd.DataFrame([bric]),
        info=[("Data source", "calculation"),
              (".Analysis start time", np.min([c_av_x.data.index, c_av_y.data.index, c_av_z.data.index])),
              (".Analysis end time", np.max([c_av_x.data.index, c_av_y.data.index, c_av_z.data.index])),
              (".Channel 001", c_av_x.code),
              (".Channel 002", c_av_y.code),
              (".Channel 003", c_av_z.code),
              (".Filter 001", c_av_x.code.filter_class),
              (".Filter 002", c_av_y.code.filter_class),
              (".Filter 003", c_av_z.code.filter_class),],
        unit="1"
    )
