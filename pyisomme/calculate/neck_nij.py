from __future__ import annotations

from pyisomme.channel import Channel, time_intersect
from pyisomme.utils import debug_logging

import logging
import numpy as np
import pandas as pd


logger = logging.getLogger("pyisomme.calculate")


@debug_logging(logger)
def calculate_neck_nij(c_fz: Channel,
                       c_mocy: Channel,
                       oop: bool = True,
                       fz_c_crit: float | None = None,
                       fz_t_crit: float | None = None,
                       mocy_f_crit: float | None = None,
                       mocy_e_crit: float | None = None) -> tuple[Channel, ...]:
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

    mask_cf = is_compression & is_flexion
    mask_ce = is_compression & is_extension
    mask_tf = is_tension & is_flexion
    mask_te = is_tension & is_extension

    data_ncf = pd.DataFrame(np.full(len(t), np.nan), index=t)
    data_ncf.loc[mask_cf, 0] = fz[mask_cf] / fz_c_crit + mocy[mask_cf] / mocy_f_crit

    data_nce = pd.DataFrame(np.full(len(t), np.nan), index=t)
    data_nce.loc[mask_ce, 0] = fz[mask_ce] / fz_c_crit + mocy[mask_ce] / mocy_e_crit

    data_ntf = pd.DataFrame(np.full(len(t), np.nan), index=t)
    data_ntf.loc[mask_tf, 0] = fz[mask_tf] / fz_t_crit + mocy[mask_tf] / mocy_f_crit

    data_nte = pd.DataFrame(np.full(len(t), np.nan), index=t)
    data_nte.loc[mask_te, 0] = fz[mask_te] / fz_t_crit + mocy[mask_te] / mocy_e_crit

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
                      data=pd.DataFrame([np.max(c_nij.get_data())], index=[c_nij.data.index[int(np.argmax(c_nij.get_data()))]]),
                      unit=c_nij.unit,
                      info=c_nij.info.update({".Time": c_nij.data.index[int(np.argmax(c_nij.get_data()))],
                                              ".Analysis start time": t[0],
                                              ".Analysis end time": t[-1],}))

    c_ncf_x = Channel(code=c_ncf.code.set(filter_class="X"),
                      data=pd.DataFrame([np.max(c_ncf.get_data())], index=[c_ncf.data.index[int(np.argmax(c_ncf.get_data()))]]),
                      unit=c_nij.unit,
                      info=c_nij_x.info.update({"Time": c_ncf.data.index[int(np.argmax(c_ncf.get_data()))]}))
    c_nce_x = Channel(code=c_nce.code.set(filter_class="X"),
                      data=pd.DataFrame([np.max(c_nce.get_data())], index=[c_nce.data.index[int(np.argmax(c_nce.get_data()))]]),
                      unit=c_nce.unit,
                      info=c_nij_x.info.update({"Time": c_nce.data.index[int(np.argmax(c_nce.get_data()))]}))
    c_ntf_x = Channel(code=c_ntf.code.set(filter_class="X"),
                      data=pd.DataFrame([np.max(c_ntf.get_data())], index=[c_ntf.data.index[int(np.argmax(c_ntf.get_data()))]]),
                      unit=c_ntf.unit,
                      info=c_nij_x.info.update({"Time": c_ntf.data.index[int(np.argmax(c_ntf.get_data()))]}))
    c_nte_x = Channel(code=c_nte.code.set(filter_class="X"),
                      data=pd.DataFrame([np.max(c_nte.get_data())], index=[c_nte.data.index[int(np.argmax(c_nte.get_data()))]]),
                      unit=c_nte.unit,
                      info=c_nij_x.info.update({"Time": c_nte.data.index[int(np.argmax(c_nte.get_data()))]}))

    return c_nij, c_ncf, c_nce, c_ntf, c_nte, c_nij_x, c_ncf_x, c_nce_x, c_ntf_x, c_nte_x
