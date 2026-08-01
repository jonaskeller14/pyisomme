from __future__ import annotations

from pyisomme.channel import Channel
from pyisomme.utils import debug_logging

import copy
import logging
import numpy as np
import pandas as pd


logger = logging.getLogger("pyisomme.calculate")


@debug_logging(logger)
def calculate_neck_MOCx(channel_Mx: Channel, channel_Fy: Channel, d: float | None = None) -> tuple[Channel, Channel]:
    """
    References:
    - references/Euro-NCAP/tb-021-data-acquisition-and-injury-calculation-v402.pdf

    :param channel_Mx:
    :param channel_Fy:
    :param d: lever
    :return:
    """
    if d is None:
        dummys = list({channel_Mx.code.fine_location_3, channel_Fy.code.fine_location_3})
        assert len(dummys) == 1, f"Multiple dummy types found: {dummys}"
        dummy = dummys[0]
        assert dummy in ("WS",), f"Dummy {dummy} not supported by {calculate_neck_MOCx.__name__}"

        d = {"WS": 0.0195}[dummy]  # [m]

    channel_Mx = channel_Mx.convert_unit("N*m")
    channel_Fy = channel_Fy.convert_unit("N")

    channel = channel_Mx + channel_Fy * d
    channel.set_code(main_location="TMON")
    channel.set_unit("N*m")
    channel.info.update({
        "Data source": "calculation",
    }).add({
        ".Channel 001": channel_Mx.code,
        ".Channel 002": channel_Fy.code,
        ".Filter 001": channel_Mx.code.filter_class,
        ".Filter 002": channel_Fy.code.filter_class,
        ".D": d,
    })
    channel_calc = copy.deepcopy(channel)
    channel_calc.data = pd.DataFrame(data=[channel.get_data()[np.argmax(np.abs(channel.get_data()))]],
                                     index=[channel.data.index[int(np.argmax(np.abs(channel.get_data())))]])
    channel_calc.set_code(filter_class="X")
    channel_calc.info.add({
        ".Time": channel_calc.data.index[0],
        ".Analysis start time": channel.data.index[0],
        ".Analysis end time": channel.data.index[-1],
    })
    return channel, channel_calc


@debug_logging(logger)
def calculate_neck_MOCy(channel_My: Channel, channel_Fx: Channel, d: float | None = None) -> tuple[Channel, Channel]:
    """
    References:
    - references/Euro-NCAP/tb-021-data-acquisition-and-injury-calculation-v402.pdf

    :param channel_My:
    :param channel_Fx:
    :param d: lever
    :return:
    """
    if d is None:
        dummys = list({channel_My.code.fine_location_3, channel_Fx.code.fine_location_3})
        assert len(dummys) == 1, f"Multiple dummy types found: {dummys}"
        dummy = dummys[0]
        assert dummy in ("WS", "H3", "HF"), f"Dummy {dummy} not supported by {calculate_neck_MOCy.__name__}"

        d = {"WS": 0.0195,
             "H3": 0.01778,
             "HF": 0.01778}[dummy]  # [m]

    channel_My = channel_My.convert_unit("N*m")
    channel_Fx = channel_Fx.convert_unit("N")

    channel = channel_My - channel_Fx * d
    channel.set_code(main_location="TMON")
    channel.set_unit("N*m")
    channel.info.update({
        "Data source": "calculation",
    }).add({
        ".Channel 001": channel_My.code,
        ".Channel 002": channel_Fx.code,
        ".Filter 001": channel_My.code.filter_class,
        ".Filter 002": channel_Fx.code.filter_class,
        ".D": d,
    })

    channel_calc = copy.deepcopy(channel)
    channel_calc.data = pd.DataFrame(data=[np.min(channel.get_data())],
                                     index=[channel.data.index[int(np.argmin(channel.get_data()))]])
    channel_calc.set_code(filter_class="X")
    channel_calc.info.add({
        ".Time": channel_calc.data.index[0],
        ".Analysis start time": channel.data.index[0],
        ".Analysis end time": channel.data.index[-1],
    })
    return channel, channel_calc
