from __future__ import annotations

from pyisomme.channel import Channel, time_intersect
from pyisomme.utils import debug_logging
from pyisomme.calculate.resultant import calculate_resultant

import logging
import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp


logger = logging.getLogger("pyisomme.calculate")


@debug_logging(logger)
def calculate_damage(
    c_aa_x: Channel, c_aa_y: Channel, c_aa_z: Channel
) -> tuple[Channel, ...]:
    """
    :param c_aa_x: Angular Acceleration Channel
    :param c_aa_y: Angular Acceleration Channel
    :param c_aa_z: Angular Acceleration Channel
    :return: 8 Channels with time and scalar data for each direction (x,y,z,resultant)
    References:
    - Euro-NCAP Technical Bulletin: https://cdn.euroncap.com/media/77157/tb-035-brain-injury-calculation-v101.pdf

    [m_x  0    0  ][dd_delta_x]   [c_xx+c_xy+c_xz  -c_xy           -c_xz         ][d_delta_x] + [k_xx+c_xy+c_xz  -k_xy           -k_xz         ][delta_x]   [m_x  0    0  ][aa_x]
    [0    m_y  0  ][dd_delta_y] = [-c_xy           c_xy+c_yy+c_yz  -c_yz         ][d_delta_y] + [-k_xy           k_xy+k_yy+k_yz  -k_yz         ][delta_y] = [0    m_y  0  ][aa_y]
    [0    0    m_z][dd_delta_z]   [-c_xz           -c_yz           c_xz+c_yz+c_zz][d_delta_z] + [-k_xz           -k_yz           k_xz+k_yz+k_zz][delta_z]   [0    0    m_z][aa_z]

    => Order reduction

    y = [delta_x, delta_y, delta_z, d_delta_x, d_delta_y, d_delta_z]

    dy/dt = [y_4]
            [y_5]
            [y_6]
            [...]
            [...]
            [...]

    """
    # Convert Units to SI
    c_aa_x = c_aa_x.convert_unit("rad/s^2")
    c_aa_y = c_aa_y.convert_unit("rad/s^2")
    c_aa_z = c_aa_z.convert_unit("rad/s^2")

    # Constants
    m_x = 1  # Mass [kg]
    m_y = 1
    m_z = 1
    k_xx = 32142  # Stiffness [N/m]
    k_xy = 0
    k_xz = 1636.3
    k_yy = 23493
    k_yz = 0
    k_zz = 16935
    a_1 = 5.9148e-3  # [s]
    c_xx = a_1 * k_xx  # Damping [s * N/m]
    c_xy = a_1 * k_xy
    c_xz = a_1 * k_xz
    c_yy = a_1 * k_yy
    c_yz = a_1 * k_yz
    c_zz = a_1 * k_zz
    beta = 2.9903  # [1/m]

    # Define the system of differential equations (reduction of order)
    # fmt: off
    def dydt(t, y):
        return [y[3],
                y[4],
                y[5],
                1/m_x*(-(c_xx+c_xy+c_xz)*y[3] + c_xy*y[4]             + c_xz*y[5]             - (k_xx+k_xy+k_xz)*y[0] + k_xy*y[1]             + k_xz*y[2])             + c_aa_x.get_data(t),
                1/m_y*(c_xy*y[3]              - (c_xy+c_yy+c_yz)*y[4] + c_yz*y[5]             + k_xy*y[0]             - (k_xy+k_yy+k_yz)*y[1] + k_yz*y[2])             + c_aa_y.get_data(t),
                1/m_z*(c_xz*y[3]              + c_yz*y[4]             - (c_xz+c_yz+c_zz)*y[5] + k_xz*y[0]             + k_yz*y[1]             - (k_xz+k_yz+k_zz)*y[2]) + c_aa_z.get_data(t)]
    # fmt: on

    # Define the initial conditions
    initial_conditions = [0, 0, 0, 0, 0, 0]

    # Define the time span over which to solve the system
    t_array = time_intersect(c_aa_x, c_aa_y, c_aa_z)
    t_span = (t_array[0], t_array[-1])

    # Solve the system of differential equations
    sol = solve_ivp(dydt, t_span, initial_conditions, t_eval=t_array)

    # Create time channels
    # TODO(unit): DAMAGE is dimensionless, but these channels inherit the angular
    #   acceleration unit of their inputs (rad/s^2). The Euro NCAP MPDB limit rows in
    #   report/euro_ncap/frontal_mpdb.py declare the same wrong unit, so the report is
    #   self-consistent today — fix both together or the 0.42/0.47 thresholds stop
    #   matching.
    damage_x = Channel(
        code=c_aa_x.code.set(fine_location_1="DA", fine_location_2="MA", direction="X"),
        data=pd.DataFrame(beta * np.abs(sol.y[0]), index=sol.t),
        unit=c_aa_x.unit,
        info={
            "Data source": "calculation",
            ".Channel 001": c_aa_x.code,
            ".Channel 002": c_aa_y.code,
            ".Channel 003": c_aa_z.code,
            ".Filter 001": c_aa_x.code.filter_class,
            ".Filter 002": c_aa_y.code.filter_class,
            ".Filter 003": c_aa_z.code.filter_class,
        },
    )
    damage_y = Channel(
        code=c_aa_y.code.set(fine_location_1="DA", fine_location_2="MA", direction="Y"),
        data=pd.DataFrame(beta * np.abs(sol.y[1]), index=sol.t),
        unit=c_aa_y.unit,
        info=damage_x.info,
    )
    damage_z = Channel(
        code=c_aa_z.code.set(fine_location_1="DA", fine_location_2="MA", direction="Z"),
        data=pd.DataFrame(beta * np.abs(sol.y[2]), index=sol.t),
        unit=c_aa_z.unit,
        info=damage_x.info,
    )
    damage_r = calculate_resultant(damage_x, damage_y, damage_z)

    # Create scalar channels
    damage_x_max = Channel(
        code=damage_x.code.set(filter_class="X"),
        data=pd.DataFrame([damage_x.data.max()], index=[damage_x.data.idxmax()]),
        unit=damage_x.unit,
        info=damage_x.info.add(
            {
                ".Analysis start time": damage_x.data.index[0],
                ".Analysis end time": damage_x.data.index[-1],
                ".Time": damage_x.data.index[int(np.argmax(damage_x.get_data()))],
            }
        ),
    )
    damage_y_max = Channel(
        code=damage_y.code.set(filter_class="X"),
        data=pd.DataFrame([damage_y.data.max()], index=[damage_y.data.idxmax()]),
        unit=damage_y.unit,
        info=damage_y.info.add(
            {
                ".Analysis start time": damage_y.data.index[0],
                ".Analysis end time": damage_y.data.index[-1],
                ".Time": damage_y.data.index[int(np.argmax(damage_y.get_data()))],
            }
        ),
    )
    damage_z_max = Channel(
        code=damage_z.code.set(filter_class="X"),
        data=pd.DataFrame([damage_z.data.max()], index=[damage_z.data.idxmax()]),
        unit=damage_z.unit,
        info=damage_z.info.add(
            {
                ".Analysis start time": damage_z.data.index[0],
                ".Analysis end time": damage_z.data.index[-1],
                ".Time": damage_z.data.index[int(np.argmax(damage_z.get_data()))],
            }
        ),
    )
    damage_r_max = Channel(
        code=damage_r.code.set(filter_class="X"),
        data=pd.DataFrame([damage_r.data.max()], index=[damage_r.data.idxmax()]),
        unit=damage_r.unit,
        info=damage_r.info.add(
            {
                ".Analysis start time": damage_r.data.index[0],
                ".Analysis end time": damage_r.data.index[-1],
                ".Time": damage_r.data.index[int(np.argmax(damage_r.get_data()))],
            }
        ),
    )

    return (
        damage_x,
        damage_y,
        damage_z,
        damage_r,
        damage_x_max,
        damage_y_max,
        damage_z_max,
        damage_r_max,
    )
