from __future__ import annotations

from pyisomme.channel import Channel
from pyisomme.errors import UnsupportedCalculationError
from pyisomme.unit import Unit
from pyisomme.utils import debug_logging

import copy
import logging
import numpy as np
import pandas as pd


logger = logging.getLogger("pyisomme.calculate")


@debug_logging(logger)
def calculate_vc(channel: Channel,
                 scaling_factor: float | None = None,
                 defo_constant: float | None = None,
                 dummy: str | None = None) -> tuple[Channel, Channel]:
    """
    References:
    - references/Euro-NCAP/tb-021-data-acquisition-and-injury-calculation-v402.pdf
    - references/DIAdem/VC.pdf

    :param channel:
    :param scaling_factor:
    :param defo_constant: in unit m
    :param dummy: Dummy type
    :return:
    """
    channel = copy.deepcopy(channel).convert_unit("m")

    if scaling_factor is None or defo_constant is None:
        if dummy is None:
            dummy = channel.code.fine_location_3
        if dummy not in ("BS", "E2", "ER", "H3", "HF", "HM", "S2", "WF", "WS", "Y6", "Y7", "YA"):
            raise UnsupportedCalculationError(
                f"Dummy {dummy} not supported by {calculate_vc.__name__}"
            )

        if scaling_factor is None:
            scaling_factor = {
                "BS": 1.0,
                "E2": 1.0,
                "ER": 1.0,
                "H3": 1.3,
                "HF": 1.3,
                "HM": 1.3,
                "S2": 1.0,
                "WF": 1.0,
                "WS": 1.0,
                "Y6": 1.3,
                "Y7": 1.3,
                "YA": 1.3,
            }[dummy]

        if defo_constant is None:
            defo_constant = {
                "BS": 0.175,
                "E2": 0.140,
                "ER": 0.140,
                "H3": 0.229,
                "HF": 0.187,
                "HM": 0.254,
                "S2": 0.138,
                "WF": 0.138,
                "WS": 0.170,
                "Y6": 0.122,
                "Y7": 0.143,
                "YA": 0.166,
            }[dummy]  # unit: m

    c_t = channel.get_data() / defo_constant

    v = channel.get_data()
    t = channel.data.index
    n = len(v)
    v_t = np.zeros(n)
    for i in range(n):
        if 2 <= i < (n - 2):
            v_t[i] = (8 * (v[i+1] - v[i-1]) - (v[i+2] - v[i-2])) / (12 * (t[i] - t[i-1]))

    vc = scaling_factor * v_t * c_t

    channel_vc = Channel(code=channel.code.set(main_location="VCCR" if channel.code.main_location in ("CHST", "TRRI", "RIBS") else "VCAR" if channel.code.main_location in ("ABDO", "ABRI") else "VC??", physical_dimension="VE"),
                         data=pd.DataFrame(vc, index=t),
                         unit=channel.unit / Unit("s"),
                         info=channel.info.update({
                             "Data source": "calculation",
                         }).add({
                             ".Channel 001": channel.code,
                             ".Filter": channel.code.filter_class,
                             ".Scaling factor": scaling_factor,
                             ".Deformation constant": defo_constant}))

    channel_vc_x = Channel(code=channel_vc.code.set(filter_class="X"),
                           data=pd.DataFrame([np.max(np.abs(channel_vc.get_data()))], index=[channel.data.index[int(np.argmax(np.abs(channel_vc.get_data())))]]),
                           unit=channel_vc.unit,
                           info=channel_vc.info.add({
                               ".Analysis start time": channel_vc.data.index[0],
                               ".Analysis end time": channel_vc.data.index[-1],
                               ".Time": channel.data.index[int(np.argmax(channel_vc.get_data()))],
                           }))

    return channel_vc, channel_vc_x
