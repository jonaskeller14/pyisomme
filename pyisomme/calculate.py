from __future__ import annotations

from pyisomme.channel import Channel, time_intersect
from pyisomme.unit import Unit
from pyisomme.utils import debug_logging
from pyisomme.unit import g0

import copy
import logging
import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp, trapezoid


logger = logging.getLogger(__name__)


@debug_logging(logger)
def calculate_resultant(c1: Channel | None,
                        c2: Channel | None = 0,
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
    new_channel.info = c1.info.update({
        "Data source": "calculation",
    }).add({
        f".Channel 00{idx}": channel.code for idx, channel in enumerate((c1, c2, c3), 1) if isinstance(channel, Channel)
    }).add({
        f".Filter 00{idx}": channel.code.filter_class for idx, channel in enumerate((c1, c2, c3), 1) if isinstance(channel, Channel)
    })
    new_channel.code = c1.code.set(direction="R")
    return new_channel


@debug_logging(logger)
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

    if channel is None:
        return None

    channel = channel.convert_unit(g0)

    max_delta_t *= 1e-3
    time_array = np.array(channel.data.index)
    res = 0
    res_t1 = None
    res_t2 = None

    if np.all(channel.get_data() >= 0):  # this is the case for resultant channels
        # Integral can only be positive -> extrema expected for maximum timespan (more runtime efficient)
        for idx_1, t1 in enumerate(time_array[:-1]):
            upper_limit_idx = (t1 + max_delta_t <= time_array).argmax()
            idx_2 = upper_limit_idx - 1
            t2 = time_array[idx_2]
            a_int = np.trapz(channel.get_data(time_array[idx_1:idx_2+1]), time_array[idx_1:idx_2+1])
            new_res = (t2 - t1) * (1 / (t2 - t1) * a_int) ** 2.5
            if new_res > res:
                res = new_res
                res_t1 = t1
                res_t2 = t2
    else:
        # Integral can be negative -> extrema can occur for smaller timespan
        for idx_1, t1 in enumerate(time_array[:-1]):
            upper_limit_idx = (t1 + max_delta_t <= time_array).argmax()
            for idx2_offset, t2 in enumerate(time_array[idx_1+1:upper_limit_idx]):
                idx_2 = idx_1 + 1 + idx2_offset
                a_int = np.trapz(channel.get_data(time_array[idx_1:idx_2+1]), time_array[idx_1:idx_2+1])
                if a_int < 0:
                    continue
                new_res = (t2 - t1) * (1 / (t2 - t1) * a_int) ** 2.5
                if new_res > res:
                    res = new_res
                    res_t1 = t1
                    res_t2 = t2

    return Channel(
        code=channel.code.set(main_location="HICR",
                              fine_location_1="00",
                              fine_location_2=f"{(max_delta_t * 1e3):.0f}",
                              physical_dimension="00",
                              filter_class="X"),
        data=pd.DataFrame([res]),
        unit="1",
        info=[("Data source", "calculation"),
              ("Name of the channel", f"HIC VALUE {max_delta_t * 1e3:.0f}"),
              ("Number of samples", 1),
              (".Start time", res_t1),
              (".End time", res_t2),
              (".Analysis start time", channel.data.index[0]),
              (".Analysis end time", channel.data.index[-1]),])


@debug_logging(logger)
def calculate_xms(channel: Channel, min_delta_t: float = 3, method: str = "S") -> Channel | None:
    """
    Exceedance value (typical 3ms)
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
        "Data source": "calculation",
    }).add({
        ".Analysis start time": np.min(time_array),
        ".Analysis end time": np.max(time_array),
    })
    if method == "S":
        new_info.add({
            ".Start time": res_t1,
            ".End time": res_t2,
        })
    return Channel(new_code, data=pd.DataFrame([res]), unit=channel.unit, info=new_info)


@debug_logging(logger)
def calculate_bric(c_av_x: Channel | None,
                   c_av_y: Channel | None,
                   c_av_z: Channel | None,
                   critical_av_x: float = None,
                   critical_av_y: float = None,
                   critical_av_z: float = None,
                   method: str = "MPS") -> Channel | None:
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


@debug_logging(logger)
def calculate_damage(c_aa_x: Channel | None,
                     c_aa_y: Channel | None,
                     c_aa_z: Channel | None) -> tuple[Channel, ...] | None:
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
    damage_x = Channel(code=c_aa_x.code.set(fine_location_1="DA", fine_location_2="MA", direction="X"),
                       data=pd.DataFrame(beta * np.abs(sol.y[0]), index=sol.t),
                       unit=c_aa_x.unit,
                       info={"Data source": "calculation",
                             ".Channel 001": c_aa_x.code,
                             ".Channel 002": c_aa_y.code,
                             ".Channel 003": c_aa_z.code,
                             ".Filter 001": c_aa_x.code.filter_class,
                             ".Filter 002": c_aa_y.code.filter_class,
                             ".Filter 003": c_aa_z.code.filter_class,})
    damage_y = Channel(code=c_aa_y.code.set(fine_location_1="DA", fine_location_2="MA", direction="Y"),
                       data=pd.DataFrame(beta * np.abs(sol.y[1]), index=sol.t),
                       unit=c_aa_y.unit,
                       info=damage_x.info)
    damage_z = Channel(code=c_aa_z.code.set(fine_location_1="DA", fine_location_2="MA", direction="Z"),
                       data=pd.DataFrame(beta * np.abs(sol.y[2]), index=sol.t),
                       unit=c_aa_z.unit,
                       info=damage_x.info)
    damage_r = calculate_resultant(damage_x, damage_y, damage_z)

    # Create scalar channels
    damage_x_max = Channel(code=damage_x.code.set(filter_class="X"),
                           data=pd.DataFrame([damage_x.data.max()], index=[damage_x.data.idxmax()]),
                           unit=damage_x.unit,
                           info=damage_x.info.add({".Analysis start time": damage_x.data.index[0],
                                                   ".Analysis end time": damage_x.data.index[-1],
                                                   ".Time": damage_x.data.index[np.argmax(damage_x.get_data())]}))
    damage_y_max = Channel(code=damage_y.code.set(filter_class="X"),
                           data=pd.DataFrame([damage_y.data.max()], index=[damage_y.data.idxmax()]),
                           unit=damage_y.unit,
                           info=damage_y.info.add({".Analysis start time": damage_y.data.index[0],
                                                   ".Analysis end time": damage_y.data.index[-1],
                                                   ".Time": damage_y.data.index[np.argmax(damage_y.get_data())]}))
    damage_z_max = Channel(code=damage_z.code.set(filter_class="X"),
                           data=pd.DataFrame([damage_z.data.max()], index=[damage_z.data.idxmax()]),
                           unit=damage_z.unit,
                           info=damage_z.info.add({".Analysis start time": damage_z.data.index[0],
                                                   ".Analysis end time": damage_z.data.index[-1],
                                                   ".Time": damage_z.data.index[np.argmax(damage_z.get_data())]}))
    damage_r_max = Channel(code=damage_r.code.set(filter_class="X"),
                           data=pd.DataFrame([damage_r.data.max()], index=[damage_r.data.idxmax()]),
                           unit=damage_r.unit,
                           info=damage_r.info.add({".Analysis start time": damage_r.data.index[0],
                                                   ".Analysis end time": damage_r.data.index[-1],
                                                   ".Time": damage_r.data.index[np.argmax(damage_r.get_data())]}))

    return damage_x, damage_y, damage_z, damage_r, damage_x_max, damage_y_max, damage_z_max, damage_r_max


@debug_logging(logger)
def calculate_neck_nij(c_fz: Channel,
                       c_mocy: Channel,
                       oop: bool = True,
                       fz_c_crit: float = None,
                       fz_t_crit: float = None,
                       mocy_f_crit: float = None,
                       mocy_e_crit: float = None) -> tuple[Channel, ...]:
    """
    References:
    - https://www.ni.com/docs/de-DE/bundle/diadem/page/crash/neck_nij.html
    - references/SafetyWissen/SafetyCompanion-2023.pdf
    :param c_fz:
    :param c_mocy:
    :param oop: Out-of-position (else In-position)
    :param fz_c_crit:
    :param fz_t_crit:
    :param mocy_f_crit:
    :param mocy_e_crit:
    :return:
    """
    if None in (fz_c_crit, fz_t_crit, mocy_f_crit, mocy_e_crit):
        dummys = list({c_fz.code.fine_location_3, c_mocy.code.fine_location_3})
        assert len(dummys) == 1, f"Multiple dummy types found: {dummys}"
        dummy = dummys[0]

        if oop:
            assert dummy in ("HF",), f"Dummy {dummy} not supported by {calculate_neck_nij.__name__}"

            if fz_t_crit is None:
                fz_t_crit = {
                    "HF": 3880,
                }[dummy]
            if fz_c_crit is None:
                fz_c_crit = {
                    "HF": -3880,
                }[dummy]
            if mocy_f_crit is None:
                mocy_f_crit = {
                    "HF": 155,
                }[dummy]
            if mocy_e_crit is None:
                mocy_e_crit = {
                    "HF": -61,
                }[dummy]
        else:
            assert dummy in ("H3", "HF", "T3", "TH"), f"Dummy {dummy} not supported by {calculate_neck_nij.__name__}"
            if fz_t_crit is None:
                fz_t_crit = {
                    "H3": 6806,
                    "HF": 4287,
                    "TH": 4200,
                    "T3": 4200,
                }[dummy]
            if fz_c_crit is None:
                fz_c_crit = {
                    "H3": -6160,
                    "HF": -3880,
                    "TH": -6400,
                    "T3": -6400,
                }[dummy]
            if mocy_f_crit is None:
                mocy_f_crit = {
                    "H3": 310,
                    "HF": 155,
                    "TH": 88.1,
                    "T3": 88.1,
                }[dummy]
            if mocy_e_crit is None:
                mocy_e_crit = {
                    "H3": -135,
                    "HF": -67,
                    "TH": -117,
                    "T3": -117,
                }[dummy]

    t = time_intersect(c_fz, c_mocy)
    fz = c_fz.get_data(t, unit="N")
    mocy = c_mocy.get_data(t, unit="Nm")

    is_compression = fz < 0
    is_tension = fz > 0
    is_flexion = mocy > 0
    is_extension = mocy < 0

    data_ncf = pd.DataFrame(np.full(len(t), np.nan), index=t)
    data_ncf.iloc[is_compression * is_flexion, 0] = fz[is_compression * is_flexion] / fz_c_crit + mocy[is_compression * is_flexion] / mocy_f_crit

    data_nce = pd.DataFrame(np.full(len(t), np.nan), index=t)
    data_nce.iloc[is_compression * is_extension, 0] = fz[is_compression * is_extension] / fz_c_crit + mocy[is_compression * is_extension] / mocy_e_crit

    data_ntf = pd.DataFrame(np.full(len(t), np.nan), index=t)
    data_ntf.iloc[is_tension * is_flexion, 0] = fz[is_tension * is_flexion] / fz_t_crit + mocy[is_tension * is_flexion] / mocy_f_crit

    data_nte = pd.DataFrame(np.full(len(t), np.nan), index=t)
    data_nte.iloc[is_tension * is_extension, 0] = fz[is_tension * is_extension] / fz_t_crit + mocy[is_tension * is_extension] / mocy_e_crit

    c_nij = Channel(code=c_fz.code.set(main_location="NIJC", fine_location_1="OP" if oop else "IP", fine_location_2="00", physical_dimension="00", direction="Y"),
                    data=pd.DataFrame(np.nansum([data_ncf, data_nce, data_nte, data_nte], axis=0), index=t),
                    unit="1",
                    info={"Data source": "calculation",
                          ".Fzcc": fz_c_crit,
                          ".Fzct": fz_t_crit,
                          ".Mycf": mocy_f_crit,
                          ".Myce": mocy_e_crit,
                          ".Channel 001": c_fz.code,
                          ".Channel 002": c_mocy.code,
                          ".Filter 001": c_fz.code.filter_class,
                          ".Filter 002": c_mocy.code.filter_class,})

    c_ncf = Channel(code=c_nij.code.set(fine_location_2="CF"),
                    data=data_ncf,
                    unit=c_nij.unit,
                    info=c_nij.info)
    c_nce = Channel(code=c_nij.code.set(fine_location_2="CE"),
                    data=data_nce,
                    unit=c_nij.unit,
                    info=c_nij.info)
    c_ntf = Channel(code=c_nij.code.set(fine_location_2="TF"),
                    data=data_ntf,
                    unit=c_nij.unit,
                    info=c_nij.info)
    c_nte = Channel(code=c_nij.code.set(fine_location_2="TE"),
                    data=data_nte,
                    unit=c_nij.unit,
                    info=c_nij.info)

    c_nij_x = Channel(code=c_nij.code.set(filter_class="X"),
                      data=pd.DataFrame([np.max(c_nij.get_data())], index=[c_nij.data.index[np.argmax(c_nij.get_data())]]),
                      unit=c_nij.unit,
                      info=c_nij.info.update({".Time": c_nij.data.index[np.argmax(c_nij.get_data())],
                                              ".Analysis start time": t[0],
                                              ".Analysis end time": t[-1],}))

    c_ncf_x = Channel(code=c_ncf.code.set(filter_class="X"),
                      data=pd.DataFrame([np.max(c_ncf.get_data())], index=[c_ncf.data.index[np.argmax(c_ncf.get_data())]]),
                      unit=c_nij.unit,
                      info=c_nij_x.info.update({"Time": c_ncf.data.index[np.argmax(c_ncf.get_data())]}))
    c_nce_x = Channel(code=c_nce.code.set(filter_class="X"),
                      data=pd.DataFrame([np.max(c_nce.get_data())], index=[c_nce.data.index[np.argmax(c_nce.get_data())]]),
                      unit=c_nce.unit,
                      info=c_nij_x.info.update({"Time": c_nce.data.index[np.argmax(c_nce.get_data())]}))
    c_ntf_x = Channel(code=c_ntf.code.set(filter_class="X"),
                      data=pd.DataFrame([np.max(c_ntf.get_data())], index=[c_ntf.data.index[np.argmax(c_ntf.get_data())]]),
                      unit=c_ntf.unit,
                      info=c_nij_x.info.update({"Time": c_ntf.data.index[np.argmax(c_ntf.get_data())]}))
    c_nte_x = Channel(code=c_nte.code.set(filter_class="X"),
                      data=pd.DataFrame([np.max(c_nte.get_data())], index=[c_nte.data.index[np.argmax(c_nte.get_data())]]),
                      unit=c_nte.unit,
                      info=c_nij_x.info.update({"Time": c_nte.data.index[np.argmax(c_nte.get_data())]}))

    return c_nij, c_ncf, c_nce, c_ntf, c_nte, c_nij_x, c_ncf_x, c_nce_x, c_ntf_x, c_nte_x


@debug_logging(logger)
def calculate_neck_MOCx(channel_Mx: Channel, channel_Fy: Channel, d: float = None) -> tuple[Channel, Channel] | tuple[None, None]:
    """
    References:
    - references/Euro-NCAP/tb-021-data-acquisition-and-injury-calculation-v402.pdf

    :param channel_Mx:
    :param channel_Fy:
    :param d: lever
    :return:
    """
    if None in (channel_Mx, channel_Fy):
        return None, None

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
                                     index=[channel.data.index[np.argmax(np.abs(channel.get_data()))]])
    channel_calc.set_code(filter_class="X")
    channel_calc.info.add({
        ".Time": channel_calc.data.index[0],
        ".Analysis start time": channel.data.index[0],
        ".Analysis end time": channel.data.index[-1],
    })
    return channel, channel_calc


@debug_logging(logger)
def calculate_neck_MOCy(channel_My: Channel, channel_Fx: Channel, d: float = None) -> tuple[Channel, Channel] | tuple[None, None]:
    """
    References:
    - references/Euro-NCAP/tb-021-data-acquisition-and-injury-calculation-v402.pdf

    :param channel_My:
    :param channel_Fx:
    :param d: lever
    :return:
    """
    if None in (channel_My, channel_Fx):
        return None, None

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
                                     index=[channel.data.index[np.argmin(channel.get_data())]])
    channel_calc.set_code(filter_class="X")
    channel_calc.info.add({
        ".Time": channel_calc.data.index[0],
        ".Analysis start time": channel.data.index[0],
        ".Analysis end time": channel.data.index[-1],
    })
    return channel, channel_calc


@debug_logging(logger)
def calculate_neck_Mx_base(channel_Mx: Channel, channel_Fy: Channel, dz: float = None) -> tuple[Channel, Channel] | tuple[None, None]:
    """
    References:
    - references/Euro-NCAP/tb-021-data-acquisition-and-injury-calculation-v402.pdf

    :param channel_Mx:
    :param channel_Fy:
    :param dz: lever
    :return:
    """
    if None in (channel_Mx, channel_Fy):
        return None, None

    if dz is None:
        dummys = list({channel_Mx.code.fine_location_3, channel_Fy.code.fine_location_3})
        assert len(dummys) == 1, f"Multiple dummy types found: {dummys}"
        dummy = dummys[0]
        assert dummy in ("WS",), f"Dummy {dummy} not supported by {calculate_neck_Mx_base.__name__}"

        dz = {"WS": 0.0145}[dummy]  # [m]

    channel_Mx = channel_Mx.convert_unit("N*m")
    channel_Fy = channel_Fy.convert_unit("N")

    channel = channel_Mx - channel_Fy * dz
    channel.set_code(main_location="TMON")
    channel.set_unit("N*m")
    channel.info.update({
        "Data source": "calculation",
    }).add({
        ".Channel 001": channel_Mx.code,
        ".Channel 002": channel_Fy.code,
        ".Filter 001": channel_Mx.code.filter_class,
        ".Filter 002": channel_Fy.code.filter_class,
        ".Dz": dz,
    })

    channel_calc = copy.deepcopy(channel)
    channel_calc.data = pd.DataFrame(data=[channel.get_data()[np.argmax(np.abs(channel.get_data()))]],
                                     index=[channel.data.index[np.argmax(np.abs(channel.get_data()))]])
    channel_calc.set_code(filter_class="X")
    channel_calc.info.add({
        ".Time": channel_calc.data.index[0],
        ".Analysis start time": channel.data.index[0],
        ".Analysis end time": channel.data.index[-1],
    })
    return channel, channel_calc


@debug_logging(logger)
def calculate_neck_My_base(channel_My: Channel, channel_Fx: Channel, dz: float = None) -> tuple[Channel, Channel] | tuple[None, None]:
    """
    References:
    - references/Euro-NCAP/tb-021-data-acquisition-and-injury-calculation-v402.pdf

    :param channel_My:
    :param channel_Fx:
    :param dz: lever
    :return:
    """
    if None in (channel_My, channel_Fx):
        return None, None

    if dz is None:
        dummys = list({channel_My.code.fine_location_3, channel_Fx.code.fine_location_3})
        assert len(dummys) == 1, f"Multiple dummy types found: {dummys}"
        dummy = dummys[0]
        assert dummy in ("WS",), f"Dummy {dummy} not supported by {calculate_neck_My_base.__name__}"

        dz = {"WS": 0.0145}[dummy]  # [m]

    channel_My = channel_My.convert_unit("N*m")
    channel_Fx = channel_Fx.convert_unit("N")

    channel = channel_My + channel_Fx * dz
    channel.set_unit("N*m")
    channel.set_code(main_location="TMON")
    channel.info.update({
        "Data source": "calculation",
    }).add({
        ".Channel 001": channel_My.code,
        ".Channel 002": channel_Fx.code,
        ".Filter 001": channel_My.code.filter_class,
        ".Filter 002": channel_Fx.code.filter_class,
        ".Dz": dz,
    })

    channel_calc = copy.deepcopy(channel)
    channel_calc.data = pd.DataFrame(data=[np.min(channel.get_data())],
                                     index=[channel.data.index[np.argmin(channel.get_data())]])
    channel_calc.set_code(filter_class="X")
    channel_calc.info.add({
        ".Time": channel_calc.data.index[0],
        ".Analysis start time": channel.data.index[0],
        ".Analysis end time": channel.data.index[-1],
    })
    return channel, channel_calc


@debug_logging(logger)
def calculate_chest_pc_score(channel_le_up_ds: Channel,
                             channel_ri_up_ds: Channel,
                             channel_le_lo_ds: Channel,
                             channel_ri_lo_ds: Channel) -> Channel:
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

    channel_pc_score = l_1 * channel_up_tot / s_1 + l_2 * channel_lo_tot / s_2 + l_3 * channel_up_dif / s_3 + l_4 * channel_lo_dif / s_4
    channel_pc_score.set_code(fine_location_1="00", fine_location_2="PC")
    return channel_pc_score


@debug_logging(logger)
def calculate_vc(channel: Channel | None,
                 scaling_factor: float = None,
                 defo_constant: float = None,
                 dummy: str = None) -> tuple[Channel | None, Channel | None]:
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
    if channel is None:
        return None, None

    channel = copy.deepcopy(channel).convert_unit("m")

    if scaling_factor is None or defo_constant is None:
        if dummy is None:
            dummy = channel.code.fine_location_3
        assert dummy in ("BS", "E2", "ER", "H3", "HF", "HM", "S2", "WF", "WS", "Y6", "Y7", "YA"), f"Dummy {dummy} not supported by {calculate_vc.__name__}"

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
                           data=pd.DataFrame([np.max(np.abs(channel_vc.get_data()))], index=[channel.data.index[np.argmax(np.abs(channel_vc.get_data()))]]),
                           unit=channel_vc.unit,
                           info=channel_vc.info.add({
                               ".Analysis start time": channel_vc.data.index[0],
                               ".Analysis end time": channel_vc.data.index[-1],
                               ".Time": channel.data.index[np.argmax(channel_vc.get_data())],
                           }))

    return channel_vc, channel_vc_x


@debug_logging(logger)
def calculate_iliac_force_drop(channel: Channel | None, delta_t: float = 0.001) -> Channel | None:
    """
    References:
    - references/Euro-NCAP/tb-021-data-acquisition-and-injury-calculation-v402.pdf
    :param channel: Iliac Force channel
    :param delta_t:
    :return:
    """
    if channel is None:
        return None

    time_array = channel.data.index

    ifd = channel.get_data(t=time_array + delta_t) - channel.get_data(t=time_array)

    return Channel(code="????????????????",
                   data=pd.DataFrame(ifd, index=time_array),
                   unit=channel.unit,
                   info=channel.info.update({"Data source": "calculation",}))


@debug_logging(logger)
def calculate_femur_impulse(channel: Channel, y_end: float = -4050) -> Channel:
    x = channel.data.index
    y = channel.get_data(unit="N")

    idx_min = np.argmin(y)
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


@debug_logging(logger)
def calculate_tibia_index(channel_MOX: Channel | None,
                          channel_MOY: Channel | None,
                          channel_FOZ: Channel | None,
                          ) -> Channel | None:
    """
    References: references/Euro-NCAP/tb-021-data-acquisition-and-injury-calculation-v402.pdf
    :param channel_MOX:
    :param channel_MOY:
    :param channel_FOZ:
    :return:
    """
    if None in (channel_MOX, channel_MOY, channel_FOZ):
        return None

    dummy = channel_MOX.code.fine_location_3
    assert dummy in ("H3", "HF", "TH", "T3"), f"Dummy {dummy} not supported by {calculate_tibia_index.__name__}"
    assert channel_MOX.code.fine_location_3 == channel_MOY.code.fine_location_3 == channel_FOZ.code.fine_location_3, f"Channel with different dummy found."
    assert channel_MOX.code.test_object == channel_MOY.code.test_object == channel_FOZ.code.test_object, f"Channel with different test_objects found."
    assert channel_MOX.code.position == channel_MOY.code.position == channel_FOZ.code.position, f"Channel with different positions found."

    channel_m_r = calculate_resultant(channel_MOX, channel_MOY)
    m_r_c = 225 if dummy in ("H3", "TH", "T3") else 115  # [Nm]
    f_z_c = 35.9 if dummy in ("H3", "TH", "T3") else 22.9  # [kN]

    time = time_intersect(channel_m_r, channel_FOZ)

    t_i = np.abs(channel_m_r.get_data(t=time, unit="Nm") / m_r_c) + np.abs(channel_FOZ.get_data(t=time, unit="kN") / f_z_c)

    return Channel(
        code=channel_MOX.code.set(main_location="TIIN", physical_dimension="00", direction="0"),
        data=pd.DataFrame(t_i, index=time),
        unit="1",
        info=[("Data source", "calculation",),
              (".Channel 001", channel_MOX.code),
              (".Channel 002", channel_MOY.code),
              (".hannel 003", channel_FOZ.code),])


@debug_logging(logger)
def calculate_olc(c_v: Channel | None,
                  free_flight_phase_displacement: float = 0.065,
                  restraining_phase_displacement: float = 0.235) -> tuple[Channel | None, ...] | None:
    """
    Calculate OLC
    :param c_v:
    :param free_flight_phase_displacement:
    :param restraining_phase_displacement:
    :return:
    """
    if c_v is None:
        return None, None

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
    c_olc_visual.info["Data source"] = "calculation"

    c_olc = Channel(
        code=c_v.code.set(fine_location_1="0O", fine_location_2="LC", filter_class="X"),
        data=pd.DataFrame([olc / 9.81]),
        unit=g0,
        info=[("Data source", "calculation",),
              ("t_1 [s]", t_1),
              ("t_2 [s]", t_2)]
    )
    return c_olc, c_olc_visual
