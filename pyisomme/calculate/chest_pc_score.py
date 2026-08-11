from __future__ import annotations

from pyisomme.channel import Channel
from pyisomme.utils import debug_logging

import logging

logger = logging.getLogger("pyisomme.calculate")


@debug_logging(logger)
def calculate_chest_pc_score(
    channel_le_up_ds: Channel,
    channel_ri_up_ds: Channel,
    channel_le_lo_ds: Channel,
    channel_ri_lo_ds: Channel,
) -> Channel:
    """
    References:
    - references/1-s2.0-S0001457517301707-main.pdf
    :param channel_le_up_ds:
    :param channel_ri_up_ds:
    :param channel_le_lo_ds:
    :param channel_ri_lo_ds:
    :return:
    """
    channel_up_tot = channel_le_up_ds + channel_ri_up_ds
    channel_lo_tot = channel_le_lo_ds + channel_ri_lo_ds

    channel_up_dif = abs(channel_le_up_ds - channel_ri_up_ds)
    channel_lo_dif = abs(channel_le_lo_ds - channel_ri_lo_ds)

    l_1 = 0.486
    l_2 = 0.492
    l_3 = 0.496
    l_4 = 0.526

    s_1 = 17.439
    s_2 = 14.735
    s_3 = 9.672
    s_4 = 12.384

    channel_pc_score = (
        l_1 * channel_up_tot / s_1
        + l_2 * channel_lo_tot / s_2
        + l_3 * channel_up_dif / s_3
        + l_4 * channel_lo_dif / s_4
    )
    channel_pc_score.set_code(fine_location_1="00", fine_location_2="PC")
    return channel_pc_score
