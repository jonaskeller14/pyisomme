from __future__ import annotations

from pyisomme.channel import Channel
from pyisomme.utils import debug_logging

import logging
import numpy as np
import pandas as pd
from scipy.stats import norm


logger = logging.getLogger("pyisomme.calculate")


@debug_logging(logger)
def calculate_p_head_hic15_ais_2plus(channel_hic15: Channel, dummy: str | None = None) -> Channel:
    """
    References:
    - references/SafetyWissen/SafetyCompanion-2023.pdf
    :param channel_hic15:
    :param dummy:
    :return:
    """
    if dummy is None:
        dummy = channel_hic15.code.fine_location_3

    hic15 = channel_hic15.get_data()

    if dummy in ("TH", "T3"):
        p = norm.cdf((np.log(hic15) - 6.96362) / 0.84687)
    else:
        raise NotImplementedError(f"Dummy {dummy} not supported.")

    return Channel(code="????????????????",
                   data=pd.DataFrame(p, index=channel_hic15.data.index),
                   unit="1")


@debug_logging(logger)
def calculate_p_head_hic15_ais_3plus(channel_hic15: Channel, dummy: str | None = None) -> Channel:
    """
    References:
    - references/SafetyWissen/SafetyCompanion-2024.pdf
    :param channel_hic15:
    :param dummy:
    :return:
    """
    if dummy is None:
        dummy = channel_hic15.code.fine_location_3

    hic15 = channel_hic15.get_data()

    if dummy in ("H3", "HF", "TH", "T3"):
        p = norm.cdf((np.log(hic15) - 7.45231) / 0.73998)
    else:
        raise NotImplementedError(f"Dummy {dummy} not supported.")

    return Channel(code="????????????????",
                   data=pd.DataFrame(p, index=channel_hic15.data.index),
                   unit="1")


@debug_logging(logger)
def calculate_p_head_hic36_ais_3plus(channel_hic36: Channel, dummy: str | None = None) -> Channel:
    """
    References:
    - references/SafetyWissen/SafetyCompanion-2024.pdf
    :param channel_hic36:
    :param dummy:
    :return:
    """
    if dummy is None:
        dummy = channel_hic36.code.fine_location_3

    hic36 = channel_hic36.get_data()

    if dummy in ("ER", "S2"):
        p = norm.cdf((np.log(hic36) - 7.45231) / 0.73998)
    else:
        raise NotImplementedError(f"Dummy {dummy} not supported.")

    return Channel(code="????????????????",
                   data=pd.DataFrame(p, index=channel_hic36.data.index),
                   unit="1")


@debug_logging(logger)
def calculate_p_head_bric_ais_3plus(channel_bric: Channel, dummy: str | None = None) -> Channel:
    """
    References:
    - references/SafetyWissen/SafetyCompanion-2023.pdf
    :param channel_bric:
    :param dummy:
    :return:
    """
    if dummy is None:
        dummy = channel_bric.code.fine_location_3

    bric = channel_bric.get_data()

    if dummy in ("TH", "T3"):
        p = 1 - np.exp(-((bric - 0.523) / 0.531)**1.8)
    else:
        raise NotImplementedError(f"Dummy {dummy} not supported.")

    return Channel(code="????????????????",
                   data=pd.DataFrame(p, index=channel_bric.data.index),
                   unit="1")


@debug_logging(logger)
def calculate_p_head_bric_ais_4plus(channel_bric: Channel, dummy: str | None = None) -> Channel:
    """
    References:
    - references/SafetyWissen/SafetyCompanion-2023.pdf
    :param channel_bric:
    :param dummy:
    :return:
    """
    if dummy is None:
        dummy = channel_bric.code.fine_location_3

    bric = channel_bric.get_data()

    if dummy in ("TH", "T3"):
        p = 1 - np.exp(-((bric - 0.523) / 0.647)**1.8)
    else:
        raise NotImplementedError(f"Dummy {dummy} not supported.")

    return Channel(code="????????????????",
                   data=pd.DataFrame(p, index=channel_bric.data.index),
                   unit="1")


@debug_logging(logger)
def calculate_p_chest_deflection_ais_3plus(channel_chest_deflection: Channel, dummy: str | None = None) -> Channel:
    """
    References:
    - references/SafetyWissen/SafetyCompanion-2024.pdf
    - references/SafetyWissen/SafetyCompanion-2023.pdf
    :param channel_chest_deflection:
    :param dummy:
    :return:
    """
    if dummy is None:
        dummy = channel_chest_deflection.code.fine_location_3

    chest_deflection = np.abs(channel_chest_deflection.get_data(unit="mm"))

    if dummy == "H3":
        p = 1 / (1 + np.exp(10.5456 - 1.568 * chest_deflection ** 0.4612))
    elif dummy == "HF":
        p = 1 / (1 + np.exp(10.5456 - 1.7212 * chest_deflection ** 0.4612))
    elif dummy in ("TH", "T3"):
        p = 1 - np.exp(-(chest_deflection / 58.183)**2.997)
    else:
        raise NotImplementedError(f"Dummy {dummy} not supported.")

    return Channel(code="????????????????",
                   data=pd.DataFrame(p, index=channel_chest_deflection.data.index),
                   unit="1")


@debug_logging(logger)
def calculate_p_femur_force_ais_2plus(channel_femur_force: Channel, dummy: str | None = None) -> Channel:
    """
    References:
    - references/SafetyWissen/SafetyCompanion-2024.pdf
    :param channel_femur_force:
    :param dummy:
    :return:
    """
    if dummy is None:
        dummy = channel_femur_force.code.fine_location_3

    femur_force = np.abs(channel_femur_force.get_data(unit="kN"))

    if dummy == "H3":
        p = 1 / (1 + np.exp(5.795 - 0.5196 * femur_force))
    elif dummy == "HF":
        p = 1 / (1 + np.exp(5.7949 - 0.7619 * femur_force))
    else:
        raise NotImplementedError(f"Dummy {dummy} not supported.")

    return Channel(code="????????????????",
                   data=pd.DataFrame(p, index=channel_femur_force.data.index),
                   unit="1")


@debug_logging(logger)
def calculate_p_neck_nij_ais_2plus(channel_neck_nij: Channel, dummy: str | None = None) -> Channel:
    """
    References:
    - references/SafetyWissen/SafetyCompanion-2023.pdf
    :param channel_neck_nij:
    :param dummy:
    :return:
    """
    if dummy is None:
        dummy = channel_neck_nij.code.fine_location_3

    neck_nij = channel_neck_nij.get_data()

    if dummy in ("TH", "T3"):
        p = 1 / (1 + np.exp(5.819 - 5.681 * neck_nij))
    else:
        raise NotImplementedError(f"Dummy {dummy} not supported.")

    return Channel(code="????????????????",
                   data=pd.DataFrame(p, index=channel_neck_nij.data.index),
                   unit="1")


@debug_logging(logger)
def calculate_p_neck_nij_ais_3plus(channel_neck_nij: Channel, dummy: str | None = None) -> Channel:
    """
    References:
    - references/SafetyWissen/SafetyCompanion-2024.pdf
    - references/SafetyWissen/SafetyCompanion-2023.pdf
    :param channel_neck_nij:
    :param dummy:
    :return:
    """
    if dummy is None:
        dummy = channel_neck_nij.code.fine_location_3

    neck_nij = channel_neck_nij.get_data()

    if dummy in ("H3", "HF"):
        p = 1 / (1 + np.exp(3.2269 - 1.9688 * neck_nij))
    elif dummy in ("TH", "T3"):
        p = 1 / (1 + np.exp(6.047 - 5.44 * neck_nij))
    else:
        raise NotImplementedError(f"Dummy {dummy} not supported.")

    return Channel(code="????????????????",
                   data=pd.DataFrame(p, index=channel_neck_nij.data.index),
                   unit="1")


@debug_logging(logger)
def calculate_p_neck_tension_ais_3plus(channel_neck_tension: Channel, dummy: str | None = None) -> Channel:
    """
    References:
    - references/SafetyWissen/SafetyCompanion-2024.pdf
    :param channel_neck_tension:
    :param dummy:
    :return:
    """
    if dummy is None:
        dummy = channel_neck_tension.code.fine_location_3

    neck_tension = np.abs(channel_neck_tension.get_data(unit="kN"))

    if dummy == "H3":
        p = 1 / (1 + np.exp(10.9745 - 2.375 * neck_tension))
    elif dummy == "HF":
        p = 1 / (1 + np.exp(10.958 - 3.770 * neck_tension))
    else:
        raise NotImplementedError(f"Dummy {dummy} not supported.")

    return Channel(code="????????????????",
                   data=pd.DataFrame(p, index=channel_neck_tension.data.index),
                   unit="1")


@debug_logging(logger)
def calculate_p_neck_compression_ais_3plus(channel_neck_compression: Channel, dummy: str | None = None) -> Channel:
    """
    References:
    - references/SafetyWissen/SafetyCompanion-2024.pdf
    :param channel_neck_compression:
    :param dummy:
    :return:
    """
    if dummy is None:
        dummy = channel_neck_compression.code.fine_location_3

    neck_compression = np.abs(channel_neck_compression.get_data(unit="kN"))

    if dummy == "H3":
        p = 1 / (1 + np.exp(10.9745 - 2.375 * neck_compression))
    elif dummy == "HF":
        p = 1 / (1 + np.exp(10.958 - 3.770 * neck_compression))
    else:
        raise NotImplementedError(f"Dummy {dummy} not supported.")

    return Channel(code="????????????????",
                   data=pd.DataFrame(p, index=channel_neck_compression.data.index),
                   unit="1")


@debug_logging(logger)
def calculate_p_chest_rib_deflection_ais_3plus(channel_chest_rib_deflection: Channel, dummy: str | None = None) -> Channel:
    """
    References:
    - references/SafetyWissen/SafetyCompanion-2024.pdf
    :param channel_chest_rib_deflection:
    :param dummy:
    :return:
    """
    if dummy is None:
        dummy = channel_chest_rib_deflection.code.fine_location_3

    rib_deflection = np.abs(channel_chest_rib_deflection.get_data(unit="mm"))

    if dummy == "ER":
        p = 1 / (1 + np.exp(5.3895 - 0.0919 * rib_deflection))
    else:
        raise NotImplementedError(f"Dummy {dummy} not supported.")

    return Channel(code="????????????????",
                   data=pd.DataFrame(p, index=channel_chest_rib_deflection.data.index),
                   unit="1")


@debug_logging(logger)
def calculate_p_abdomen_force_ais_3plus(channel_abdomen_force: Channel, dummy: str | None = None) -> Channel:
    """
    References:
    - references/SafetyWissen/SafetyCompanion-2024.pdf
    :param channel_abdomen_force:
    :param dummy:
    :return:
    """
    if dummy is None:
        dummy = channel_abdomen_force.code.fine_location_3

    abdomen_force = np.abs(channel_abdomen_force.get_data(unit="N"))

    if dummy == "ER":
        p = 1 / (1 + np.exp(6.04044 - 0.002133 * abdomen_force))
    else:
        raise NotImplementedError(f"Dummy {dummy} not supported.")

    return Channel(code="????????????????",
                   data=pd.DataFrame(p, index=channel_abdomen_force.data.index),
                   unit="1")


@debug_logging(logger)
def calculate_p_abdomen_compression_ais_3plus(channel_abdomen_compression: Channel, dummy: str | None = None) -> Channel:
    """
    References:
    - references/SafetyWissen/SafetyCompanion-2023.pdf
    :param channel_abdomen_compression:
    :param dummy:
    :return:
    """
    raise NotImplementedError  # FIXME


@debug_logging(logger)
def calculate_p_pelvis_force_ais_3plus(channel_pelvis_force: Channel, dummy: str | None = None) -> Channel:
    """
    References:
    - references/SafetyWissen/SafetyCompanion-2024.pdf
    :param channel_pelvis_force:
    :param dummy:
    :return:
    """
    if dummy is None:
        dummy = channel_pelvis_force.code.fine_location_3

    pelvis_force = np.abs(channel_pelvis_force.get_data(unit="N"))

    if dummy == "ER":
        p = 1 / (1 + np.exp(7.5969 - 0.0011 * pelvis_force))
    else:
        raise NotImplementedError(f"Dummy {dummy} not supported.")

    return Channel(code="????????????????",
                   data=pd.DataFrame(p, index=channel_pelvis_force.data.index),
                   unit="1")


@debug_logging(logger)
def calculate_p_pelvis_force_ais_2plus(channel_pelvis_force: Channel, dummy: str | None = None) -> Channel:
    """
    References:
    - references/SafetyWissen/SafetyCompanion-2024.pdf
    :param channel_pelvis_force:
    :param dummy:
    :return:
    """
    if dummy is None:
        dummy = channel_pelvis_force.code.fine_location_3

    pelvis_force = np.abs(channel_pelvis_force.get_data(unit="N"))

    if dummy == "S2":
        p = 1 / (1 + np.exp(6.3055 - 0.00094 * pelvis_force))
    else:
        raise NotImplementedError(f"Dummy {dummy} not supported.")

    return Channel(code="????????????????",
                   data=pd.DataFrame(p, index=channel_pelvis_force.data.index),
                   unit="1")
