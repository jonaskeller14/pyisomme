from pyisomme.channel import Channel
from pyisomme.info import Info

import logging
from datetime import datetime
import numpy as np
import pandas as pd
import re


logger = logging.getLogger(__name__)


def parse_mme(text: str) -> Info:
    lines = text.splitlines()
    info = Info([])
    for line in lines:
        line = line.strip()

        if line == "":
            continue
        match = re.fullmatch(r"([^:]*\S+)\s*:(.*)", line)
        if match is None:
            logger.error(f"Could not parse malformed line: '{line}'")
            continue
        else:
            name, value = match.groups()
            info[name] = get_value(value)
    return info


def parse_chn(text: str) -> Info:
    return parse_mme(text)


def parse_xxx(text: str, isomme) -> Channel:
    lines = text.splitlines()
    info = Info([])
    start_data_idx = 0
    for idx, line in enumerate(lines):
        line = line.strip()

        if line == "":
            continue
        match = re.fullmatch(r"([^:]*\S+)\s*:(.*)", line)
        if match is None:
            start_data_idx = idx
            break
        else:
            name, value = match.groups()
            info[name] = get_value(value)

    code = info.get("Channel code")
    unit = info.get("Unit")

    # data
    array_str = np.array(lines[start_data_idx:])
    array_str[array_str == "NOVALUE"] = np.nan
    array = np.array(array_str, dtype=float)

    reference_channel_code = info.get("Reference channel name")
    time_of_first_sample = info.get("Time of first sample")
    sampling_interval = info.get("Sampling interval")

    if info.get("Reference channel") == "implicit":
        if time_of_first_sample is None:
            logger.error(f"[{code}] Time of first sample not found.")
        elif sampling_interval is None:
            logger.error(f"[{code}] Sampling interval not found.")
        else:
            n = len(array)
            time_array = np.linspace(time_of_first_sample, time_of_first_sample + (n-1) * sampling_interval, n)
            return Channel(code, pd.DataFrame(array, index=time_array), unit=unit, info=info)

    elif info.get("Reference channel") == "explicit":
        if reference_channel_code is None:
            logger.error(f"[{code}] Reference channel name not found.")
        else:
            reference_channel = isomme.get_channel(reference_channel_code)
            if reference_channel is None:
                logger.error(f"[{code}] Reference channel {reference_channel_code} not found.")
            else:
                return Channel(code=code,
                               data=pd.DataFrame(array, index=reference_channel.get_data()),
                               unit=unit,
                               info=info)

    elif time_of_first_sample is not None and sampling_interval is not None:
        logger.info(f"[{code}] Assume 'Reference channel' = 'implicit'")

        n = len(array)
        time_array = np.linspace(time_of_first_sample, n * sampling_interval, n)
        return Channel(code, pd.DataFrame(array, index=time_array), unit=unit, info=info)

    elif sampling_interval is not None:
        logger.info(f"[{code}] Assume 'Time of first sample' = 0")

        n = len(array)
        time_array = np.linspace(0, n * sampling_interval, n)
        return Channel(code, pd.DataFrame(array, index=time_array), unit=unit, info=info)

    elif reference_channel_code is not None:
        logger.info(f"[{code}] Assume 'Reference channel' = 'explicit'")

        reference_channel = isomme.get_channel(reference_channel_code)
        if reference_channel is None:
            logger.error(f"[{code}] Reference channel not found.")
        else:
            return Channel(code=code,
                           data=pd.DataFrame(array, index=reference_channel.get_data()),
                           unit=unit,
                           info=info)
    if code[2:6] != "TIRS":
        logger.warning(f"[{code}] Reference channel type [implicit/explicit] unknown. Could not set index.")

    data = pd.DataFrame(array)
    data = data[~data.index.duplicated(keep='first')].sort_index()
    return Channel(code, data, unit=unit, info=info)


def get_value(text: str):
    """
    Converts a string into suitable datatype.
    - None
    - string
    - int
    - float
    - datetime
    - bool
    - coded
    - reference
    - filereference

    REFERENCES:
    - references/RED A/2020_06_17_ISO_TS13499_RED_A_1_6_2.pdf
    :param text:
    :return:
    """
    text = text.strip()
    # None
    if text.upper() in ("NOVALUE", "NONE") or text == "":
        return None
    # Boolean
    elif text.upper() == "YES":
        return True
    elif text.upper() == "NO":
        return False
    if text.isdigit():
        # Integer
        try:
            return int(text)
        except ValueError:
            pass
    else:
        # Float
        try:
            return float(text)
        except ValueError:
            pass
    # Datetime
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        pass
    # TODO: Coded
    # TODO: Reference
    # TODO: Filereference
    # String
    return text
