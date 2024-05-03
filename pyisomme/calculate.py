from __future__ import annotations

from pyisomme.channel import Channel, time_intersect
from pyisomme.unit import Unit
from pyisomme.utils import debug_logging

import copy
import logging
import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp
from astropy.constants import g0


logger = logging.getLogger(__name__)

#TODO Check ISO REd E --> check if all required info exists in result channels (subsets ...)


@debug_logging(__name__)
def calculate_resultant(c1: Channel | None,
                        c2: Channel | None,
                        c3: Channel | None = 0) -> Channel | None:
    """
    Takes 2 or 3 Channels and calculates the 2nd norm or resultant component.
    :param c1: X-Channel
    :param c2: Y-Channel
    :param c3: (optional) Z-Channel
    :return: Resultant Channel
    """
    if c1 is None or c2 is None or c3 is None:
        return None

    new_channel = (c1 ** 2 + c2 ** 2 + c3 ** 2) ** (1 / 2)
    new_channel.info = c1.info
    new_channel.code = c1.code.set(direction="R")
    return new_channel


@debug_logging(__name__)
def calculate_hic(channel: Channel, max_delta_t) -> Channel | None:
    """
    Computes head injury criterion (HIC)
    HIC15 --> max_delta_t = 15
    HIC36 --> max_delta_t = 36

    REFERENCES
    - https://en.wikipedia.org/wiki/Head_injury_criterion

    :param channel: Head resultant acceleration Channel-object
    :param max_delta_t: in ms
    :return:
    """
    assert 0 < max_delta_t < 100

    # TODO: effizienter machen. einmal integrieren und dann nur differenzen berechnen? channel.integrate()
    if channel is None:
        return None

    channel = channel.convert_unit(g0)

    max_delta_t *= 1e-3
    time_array = channel.data.index
    res = 0
    res_t1 = None
    res_t2 = None
    for idx_1, t1 in enumerate(time_array):
        for idx_2, t2 in enumerate(reversed(time_array)):
            if t1 < t2 < t1 + max_delta_t:
                idx_2 = len(time_array) - 1 - idx_2  # undo revered
                new_res = np.trapz(channel.get_data(time_array[idx_1:idx_2+1]), time_array[idx_1:idx_2+1])
                new_res = (t2 - t1) * (1 / (t2 - t1) * new_res) ** 2.5
                if new_res > res:
                    res = new_res
                    res_t1 = t1
                    res_t2 = t2
                break

    return Channel(
        code=channel.code.set(main_location="HICR",
                              fine_location_1="00",
                              fine_location_2=f"{(max_delta_t * 1e3):.0f}",
                              physical_dimension="00",
                              filter_class="X"),
        data=pd.DataFrame([res]),
        unit=None,
        info={
            "Name of the channel": f"HIC VALUE {max_delta_t:.0f}",
            "Data source": "Calculation",
            "Number of samples": 1,
            ".Start time": res_t1,
            ".End time": res_t2
        })


@debug_logging(__name__)
def calculate_xms(channel: Channel, min_delta_t: float = 3, method: str = "S") -> Channel | None:
    """
    # TODO
    :param channel:
    :param min_delta_t: in ms
    :param method: S (for single peak) or C (for cumulative)
    :return:
    """
    assert method in ("S", "C")
    assert 0 < min_delta_t < 10

    if channel is None:
        return None

    min_delta_t *= 1e-3  # convert to s
    time_array = channel.data.index
    value_array = channel.get_data()

    res = 0
    res_t1 = None
    res_t2 = None

    if method == "S":
        for t1 in time_array:
            t2_pts = time_array[time_array >= t1 + min_delta_t]
            if len(t2_pts) == 0:
                break
            t2 = t2_pts[0]
            indices = np.where((t1 <= time_array)*(time_array <= t2))
            values = value_array[indices]

            new_res = np.min(values)

            if new_res > res:
                res = new_res
                res_t1 = t1
                res_t2 = t2

    elif method == "C":
        dt = np.append(np.diff(time_array), 0)

        for value in np.sort(value_array)[::-1]:
            greater_indices = np.nonzero(value_array >= value)[0]
            greater_indices_left = np.array([greater_idx for greater_idx in greater_indices if (greater_idx+1) in greater_indices], dtype=int)

            if np.sum(dt[greater_indices_left]) >= min_delta_t:
                res = value
                res_t1 = time_array[greater_indices_left[0]]
                res_t2 = time_array[greater_indices_left[-1] + 1]  #  +1 because right bound was delete
                break

    new_code = channel.code.set(fine_location_2=f"{(min_delta_t*1e3):.0f}{method}",
                                filter_class="X")
    new_info = channel.info
    new_info.update({
        ".Analysis start time": np.min(time_array),
        ".Analysis end time": np.max(time_array),
        "Name of the channel": None,
        "Data source": "Calculation",
        "Number of samples": 1,
    })
    if method == "S":
        new_info.update({
            ".Start time": res_t1,
            ".End time": res_t2,
        })
    return Channel(new_code, data=pd.DataFrame([res]), unit=channel.unit, info=new_info)


@debug_logging(__name__)
def calculate_bric(c_av_x: Channel | None,
                   c_av_y: Channel | None,
                   c_av_z: Channel | None,
                   critical_av_x: float = None,
                   critical_av_y: float = None,
                   critical_av_z: float = None,
                   method="MPS") -> Channel | None:
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
    if c_av_x is None or c_av_y is None or c_av_z is None:
        return None

    assert method in ("MPS", "CSDM", "Average of CSDM and MPS")

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
    av_y = c_av_x.get_data()
    av_z = c_av_x.get_data()

    bric = np.sqrt((np.max(np.abs(av_x))/critical_av_x)**2 + (np.max(np.abs(av_y))/critical_av_y)**2 + (np.max(np.abs(av_z))/critical_av_z)**2)

    return Channel(
        code=c_av_x.code.set(main_location="BRIC", physical_dimension="00", direction="0", filter_class="X"),
        data=pd.DataFrame([bric]),
        info={".Analysis start time": np.min([c_av_x.data.index, c_av_y.data.index, c_av_z.data.index]),
              ".Analysis end time": np.max([c_av_x.data.index, c_av_y.data.index, c_av_z.data.index]),
              ".Channel 001": c_av_x.code,
              ".Channel 002": c_av_y.code,
              ".Channel 003": c_av_z.code,
              ".Filter": " / ".join({c_av_x.code.filter_class, c_av_y.code.filter_class, c_av_z.code.filter_class})},
        unit="1"
    )


@debug_logging(__name__)
def calculate_damage(c_aa_x: Channel | None,
                     c_aa_y: Channel | None,
                     c_aa_z: Channel | None) -> tuple | None:
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
    if c_aa_x is None or c_aa_y is None or c_aa_z is None:
        return None

    # Convert Units to SI
    c_aa_x = c_aa_x.convert_unit("rad/s^2")
    c_aa_y = c_aa_y.convert_unit("rad/s^2")
    c_aa_z = c_aa_z.convert_unit("rad/s^2")

    # Constants
    m_x = 1  # Mass
    m_y = 1
    m_z = 1
    k_xx = 32142  # Stiffness
    k_xy = 0
    k_xz = 1636.3
    k_yy = 23493
    k_yz = 0
    k_zz = 16935
    a_1 = 5.9148
    c_xx = a_1 * k_xx  # Damping
    c_xy = a_1 * k_xy
    c_xz = a_1 * k_xz
    c_yy = a_1 * k_yy
    c_yz = a_1 * k_yz
    c_zz = a_1 * k_zz
    beta = 2.9903

    # Define the system of differential equations (reduction of order)
    def dydt(t, y):
        return [y[3],
                y[4],
                y[5],
                1/m_x*(-(c_xx+c_xy+c_xz)*y[3] + c_xy*y[4]             + c_xz*y[5]             - (k_xx+k_xy+k_xz)*y[0] + k_xy*y[1]             + k_xz*y[2])             + c_aa_x.get_data(t),
                1/m_y*(c_xy*y[3]              - (c_xy+c_yy+c_yz)*y[4] + c_yz*y[5]             + k_xy*y[0]             - (k_xy+k_yy+k_yz)*y[1] + k_yz*y[2])             + c_aa_y.get_data(t),
                1/m_z*(c_xz*y[3]              + c_yz*y[4]             - (c_xz+c_yz+c_zz)*y[5] + k_xz*y[0]             + k_yz*y[1]             - (k_xz+k_yz+k_zz)*y[2]) + c_aa_z.get_data(t)]

    # Define the initial conditions
    initial_conditions = [0, 0, 0, 0, 0, 0]

    # Define the time span over which to solve the system
    t_array = time_intersect(c_aa_x, c_aa_y, c_aa_z)
    t_span = (t_array[0], t_array[-1])

    # Solve the system of differential equations
    sol = solve_ivp(dydt, t_span, initial_conditions, t_eval=t_array)

    # Create time channels
    damage_x = Channel(code=c_aa_x.code.set(fine_location_1="DA", fine_location_2="MA", direction="X"), data=pd.DataFrame(beta * np.abs(sol.y[0]), index=sol.t), unit=c_aa_x.unit, info=None)
    damage_y = Channel(code=c_aa_y.code.set(fine_location_1="DA", fine_location_2="MA", direction="Y"), data=pd.DataFrame(beta * np.abs(sol.y[1]), index=sol.t), unit=c_aa_y.unit, info=None)
    damage_z = Channel(code=c_aa_z.code.set(fine_location_1="DA", fine_location_2="MA", direction="Z"), data=pd.DataFrame(beta * np.abs(sol.y[2]), index=sol.t), unit=c_aa_z.unit, info=None)
    damage_r = calculate_resultant(damage_x, damage_y, damage_z)

    # Create scalar channels
    damage_x_max = Channel(code=damage_x.code.set(filter_class="X"), data=pd.DataFrame([damage_x.data.max()], index=[damage_x.data.idxmax()]), unit=damage_x.unit, info=None)
    damage_y_max = Channel(code=damage_y.code.set(filter_class="X"), data=pd.DataFrame([damage_y.data.max()], index=[damage_y.data.idxmax()]), unit=damage_y.unit, info=None)
    damage_z_max = Channel(code=damage_z.code.set(filter_class="X"), data=pd.DataFrame([damage_z.data.max()], index=[damage_z.data.idxmax()]), unit=damage_z.unit, info=None)
    damage_r_max = Channel(code=damage_r.code.set(filter_class="X"), data=pd.DataFrame([damage_r.data.max()], index=[damage_r.data.idxmax()]), unit=damage_r.unit, info=None)

    return damage_x, damage_y, damage_z, damage_r, damage_x_max, damage_y_max, damage_z_max, damage_r_max


@debug_logging(__name__)
def calculate_neck_nij() -> tuple:
    pass


@debug_logging(__name__)
def calculate_chest_vc(channel: Channel | None, scaling_factor: float = None, defo_constant: float = None, dummy: str = None):
    """
    References:
    - references/Euro-NCAP/tb-021-data-acquisition-and-injury-calculation-v402.pdf
    - references/DIAdem/VC.pdf

    :param channel:
    :param scaling_factor:
    :param defo_constant: in unit m
    :return:
    """
    if channel is None:
        return None

    channel = copy.deepcopy(channel).convert_unit("m")

    if scaling_factor is None or defo_constant is None:
        if dummy is None:
            dummy = channel.code.fine_location_3
        assert dummy in ("BS", "E2", "ER", "H3", "HF", "HM", "S2", "WF", "WS", "Y6", "Y7", "YA"), f"Dummy not supported by {calculate_chest_vc.__name__}"

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
            }[dummy] # unit: m

    c_t = channel.get_data() / defo_constant

    v = channel.get_data()
    t = channel.data.index
    n = len(v)
    v_t = np.zeros(n)
    for i in range(n):
        if 2 <= i < (n - 2):
            v_t[i] = (8 * (v[i+1] - v[i-1]) - (v[i+2] - v[i-2])) / (12 * (t[i] - t[i-1]))

    vc = scaling_factor * v_t * c_t

    new_code = channel.code.set(main_location="VCCR", physical_dimension="VE", direction="X")
    new_unit = channel.unit / Unit("s")
    new_data = pd.DataFrame(vc, index=t)
    new_info = channel.info
    new_info.update({
        ".Channel 001": channel.code,
        ".Filter": channel.code.get_info().get("Filter Class"),
        ".Scaling factor": scaling_factor,
        ".Deformation constant": defo_constant})

    return Channel(code=new_code, unit=new_unit, data=new_data, info=new_info)


@debug_logging(__name__)
def calculate_olc(c_v: Channel | None,
                  free_flight_phase_displacement: float = 0.065,
                  restraining_phase_displacement: float = 0.235) -> tuple | None:
    """
    Calculate OLC
    :param c_v:
    :param free_flight_phase_displacement:
    :param restraining_phase_displacement:
    :return:
    """
    if c_v is None:
        return None

    c_v = c_v.convert_unit("m/s")

    c_olc_visual = copy.deepcopy(c_v)

    v_0 = c_v.get_data(t=0)
    c_v_rel = -c_v + v_0
    c_s_rel = c_v_rel.integrate()

    # Free flight phase
    is_not_free_flight_phase = c_s_rel.data.iloc[:, 0] >= free_flight_phase_displacement
    if is_not_free_flight_phase.any():
        t_1 = is_not_free_flight_phase.idxmax()
    else:
        raise ArithmeticError("OLC: Could not calculate t_1. Free flight phase too short.")

    # Restraining phase

    for i_2, t_2 in enumerate(c_s_rel.data.index):
        if t_2 <= t_1:
            continue
        v_2 = c_v.get_data(t=t_2)
        olc = float((v_0 - v_2)/(t_2 - t_1))
        if c_s_rel.data.iloc[i_2, 0] - olc * (1/2*t_2**2 + 1/2*t_1**2 - t_1*t_2) >= free_flight_phase_displacement + restraining_phase_displacement:
            break

    is_restraining_phase = (t_1 < c_s_rel.data.index) * (c_s_rel.data.index < t_2)
    after_restraining_phase = c_s_rel.data.index >= t_2
    if not after_restraining_phase.any():
        logger.warning("Incorrect OLC values. Not reached restraining phase displacement.")

    c_olc_visual.data.iloc[np.logical_xor(is_not_free_flight_phase, after_restraining_phase), 0] = -olc * c_olc_visual.data[np.logical_xor(is_not_free_flight_phase, after_restraining_phase)].index + (v_0 + olc*t_1)
    c_olc_visual.data.iloc[np.logical_and(is_not_free_flight_phase, after_restraining_phase), 0] = v_2
    c_olc_visual.data[~is_not_free_flight_phase] = v_0

    c_olc_visual.set_code(c_v.code.set(fine_location_1="0O", fine_location_2="LC", filter_class=c_v.code.filter_class))

    c_olc_visual.info["OLC [g]"] = olc / 9.81
    c_olc_visual.info["t_1 [s]"] = t_1
    c_olc_visual.info["t_2 [s]"] = t_2

    c_olc = Channel(
        code=c_v.code.set(fine_location_1="0O", fine_location_2="LC", filter_class="X"),
        data=olc / 9.81,
        unit=Unit("g"),
        info={
            "t_1 [s]": t_1,
            "t_2 [s]": t_2,
        }
    )
    return c_olc, c_olc_visual
