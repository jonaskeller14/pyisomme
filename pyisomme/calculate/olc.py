from __future__ import annotations

import copy
import logging

import numpy as np
import pandas as pd

from pyisomme.channel import Channel
from pyisomme.unit import Unit, g0
from pyisomme.utils import debug_logging

logger = logging.getLogger("pyisomme.calculate")


@debug_logging(logger)
def calculate_olc(
    c_v: Channel,
    free_flight_phase_displacement: float = 0.065,
    restraining_phase_displacement: float = 0.235,
) -> tuple[Channel, Channel]:
    """
    Calculate OLC
    :param c_v:
    :param free_flight_phase_displacement:
    :param restraining_phase_displacement:
    :return:
    """
    c_v = c_v.convert_unit("m/s")

    c_olc_visual = copy.deepcopy(c_v)

    v_0 = c_v.get_data(t=0)
    c_v_rel = -c_v + v_0
    c_s_rel = c_v_rel.integrate()

    # Free flight phase
    is_not_free_flight_phase = c_s_rel.data.iloc[:, 0] >= free_flight_phase_displacement
    if is_not_free_flight_phase.any():
        t_1 = float(is_not_free_flight_phase.idxmax())
    else:
        raise ArithmeticError(
            "OLC: Could not calculate t_1. Free flight phase too short."
        )

    # Restraining phase

    for i_2, t_2 in enumerate(c_s_rel.data.index):
        if t_2 <= t_1:
            continue
        v_2 = c_v.get_data(t=t_2)
        olc = float((v_0 - v_2) / (t_2 - t_1))
        if (
            c_s_rel.data.iloc[i_2, 0]
            - olc * (1 / 2 * t_2**2 + 1 / 2 * t_1**2 - t_1 * t_2)
            >= free_flight_phase_displacement + restraining_phase_displacement
        ):
            break

    after_restraining_phase = c_s_rel.data.index >= t_2
    if not after_restraining_phase.any():
        logger.warning(
            "Incorrect OLC values. Not reached restraining phase displacement."
        )

    c_olc_visual.data.iloc[
        np.logical_xor(is_not_free_flight_phase, after_restraining_phase), 0
    ] = -olc * c_olc_visual.data[  # pyright: ignore[reportOperatorIssue]
        np.logical_xor(is_not_free_flight_phase, after_restraining_phase)
    ].index + (v_0 + olc * t_1)  # pyright: ignore[reportOperatorIssue]
    c_olc_visual.data.iloc[
        np.logical_and(is_not_free_flight_phase, after_restraining_phase), 0
    ] = v_2
    c_olc_visual.data[~is_not_free_flight_phase] = v_0

    c_olc_visual.set_code(
        c_v.code.set(
            fine_location_1="0O",
            fine_location_2="LC",
            filter_class=c_v.code.filter_class,
        )
    )

    c_olc_visual.info["OLC [g]"] = olc / 9.81
    c_olc_visual.info["t_1 [s]"] = t_1
    c_olc_visual.info["t_2 [s]"] = t_2
    c_olc_visual.info["Data source"] = "calculation"

    c_olc = Channel(
        code=c_v.code.set(fine_location_1="0O", fine_location_2="LC", filter_class="X"),
        data=pd.DataFrame([olc / 9.81]),
        unit=Unit(g0),
        info=[
            (
                "Data source",
                "calculation",
            ),
            ("t_1 [s]", t_1),
            ("t_2 [s]", t_2),
        ],
    )
    return c_olc, c_olc_visual
