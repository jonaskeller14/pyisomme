from __future__ import annotations

from pyisomme.calculate.resultant import calculate_resultant
from pyisomme.channel import Channel, time_intersect
from pyisomme.errors import UnsupportedCalculationError
from pyisomme.utils import debug_logging

import logging
import numpy as np
import pandas as pd


logger = logging.getLogger("pyisomme.calculate")


@debug_logging(logger)
def calculate_tibia_index(
    channel_MOX: Channel,
    channel_MOY: Channel,
    channel_FOZ: Channel,
) -> Channel:
    """
    References: references/Euro-NCAP/tb-021-data-acquisition-and-injury-calculation-v402.pdf
    :param channel_MOX:
    :param channel_MOY:
    :param channel_FOZ:
    :return:
    """
    dummy = channel_MOX.code.fine_location_3
    if dummy not in ("H3", "HF", "TH", "T3"):
        raise UnsupportedCalculationError(
            f"Dummy {dummy} not supported by {calculate_tibia_index.__name__}"
        )
    if (
        not channel_MOX.code.fine_location_3
        == channel_MOY.code.fine_location_3
        == channel_FOZ.code.fine_location_3
    ):
        raise ValueError("Channel with different dummy found.")
    if (
        not channel_MOX.code.test_object
        == channel_MOY.code.test_object
        == channel_FOZ.code.test_object
    ):
        raise ValueError("Channel with different test_objects found.")
    if (
        not channel_MOX.code.position
        == channel_MOY.code.position
        == channel_FOZ.code.position
    ):
        raise ValueError("Channel with different positions found.")

    channel_m_r = calculate_resultant(channel_MOX, channel_MOY)
    m_r_c = 225 if dummy in ("H3", "TH", "T3") else 115  # [Nm]
    f_z_c = 35.9 if dummy in ("H3", "TH", "T3") else 22.9  # [kN]

    time = time_intersect(channel_m_r, channel_FOZ)

    t_i = np.abs(channel_m_r.get_data(t=time, unit="Nm") / m_r_c) + np.abs(
        channel_FOZ.get_data(t=time, unit="kN") / f_z_c
    )

    initial_fine_location_1 = channel_MOX.code.fine_location_1
    initial_fine_location_2 = channel_MOX.code.fine_location_2
    fine_location_1 = initial_fine_location_1[0] + initial_fine_location_2[0]
    return Channel(
        code=channel_MOX.code.set(
            main_location="TIIN",
            fine_location_1=fine_location_1,
            fine_location_2="00",
            physical_dimension="00",
            direction="0",
        ),
        data=pd.DataFrame(t_i, index=time),
        unit="1",
        info=[
            (
                "Data source",
                "calculation",
            ),
            (".Channel 001", channel_MOX.code),
            (".Channel 002", channel_MOY.code),
            (".hannel 003", channel_FOZ.code),
        ],
    )


@debug_logging(logger)
def calculate_adjusted_upper_tibia_moment_My(
    channel_MOY: Channel, channel_FOZ: Channel
) -> Channel:
    """
    References:
    - Effect of Hybrid III Leg Geometry on Upper Tibia Bending Moments (David S. Zuby, Joseph M. Nolan, Christopher P. Sherwood)
    - references/IIHS/small_overlap_rating_protocol.pdf
    :param channel_MOY: Measured upper bending moment
    :param channel_FOZ: Tibia axial force
    :return: Adjusted Tibia bending moment
    """
    dummy = channel_MOY.code.fine_location_3
    if dummy not in ("H3", "T3"):
        raise UnsupportedCalculationError(
            f"Dummy {dummy} not supported by {calculate_adjusted_upper_tibia_moment_My.__name__}"
        )

    return (
        channel_MOY.convert_unit("Nm") - channel_FOZ.convert_unit("N") * 0.02832
    )  # FIXME: Incompatible Units


@debug_logging(logger)
def calculate_adjusted_lower_tibia_moment_My(
    channel_MOY: Channel, channel_FOZ: Channel
) -> Channel:
    """
    References:
    - Effect of Hybrid III Leg Geometry on Upper Tibia Bending Moments (David S. Zuby, Joseph M. Nolan, Christopher P. Sherwood)
    - references/IIHS/small_overlap_rating_protocol.pdf
    :param channel_MOY: Measured lower bending moment
    :param channel_FOZ: Tibia axial force
    :return: Adjusted Tibia bending moment
    """
    dummy = channel_MOY.code.fine_location_3
    if dummy not in ("H3", "T3"):
        raise UnsupportedCalculationError(
            f"Dummy {dummy} not supported by {calculate_adjusted_lower_tibia_moment_My.__name__}"
        )

    return (
        channel_MOY.convert_unit("Nm") + channel_FOZ.convert_unit("N") * 0.006398
    )  # FIXME: Incompatible Units


@debug_logging(logger)
def calculate_tibia_index_using_total_moment(
    channel_MOX: Channel, channel_MOY_total: Channel, channel_FOZ: Channel
) -> Channel:
    tibia_index = calculate_tibia_index(
        channel_MOX=channel_MOX, channel_MOY=channel_MOY_total, channel_FOZ=channel_FOZ
    )
    tibia_index.code = tibia_index.code.set(fine_location_2="TO")
    return tibia_index
