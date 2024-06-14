from pyisomme.channel import Channel
from pyisomme.info import Info

import logging
from datetime import datetime
import numpy as np
import pandas as pd
import re


logger = logging.getLogger(__name__)


def parse_mme(text: str) -> list:
    lines = text.splitlines()
    info = Info([])
    for line in lines:
        line = line.strip()

        if line == "":
            continue
        match = re.fullmatch(r"(.*[^\s]+)\s*:(.*)", line)
        if match is None:
            logger.error(f"Could not parse malformed line: '{line}'")
            continue
        else:
            name, value = match.groups()
            info[name] = get_value(value)
    return info


def parse_chn(text: str) -> list:
    return parse_mme(text)


def parse_xxx(text: str, isomme):
    lines = text.splitlines()
    info = Info([])
    start_data_idx = 0
    for idx, line in enumerate(lines):
        line = line.strip()

        if line == "":
            continue
        match = re.fullmatch(r"(.*[^\s]+)\s*:(.*)", line)
        if match is None:
            start_data_idx = idx
            break
        else:
            name, value = match.groups()
            info[name] = get_value(value)

    code = info.get("Channel code")
    unit = info.get("Unit")

    # data
    array = np.array(lines[start_data_idx:], dtype=float)

    if info.get("Reference channel") == "explicit":
        reference_channel_code = info.get("Reference channel name")
        if reference_channel_code is None:
            raise ValueError(f"Reference channel name not found.")
        reference_channel = isomme.get_channel(reference_channel_code)
        if reference_channel is None:
            raise ValueError(f"Reference channel not found.")

        data = pd.DataFrame(array, index=reference_channel.get_data())

    elif info.get("Reference channel") == "implicit":
        time_of_first_sample = info.get("Time of first sample")
        if time_of_first_sample is None:
            raise ValueError(f"Time of first sample not found.")
        sampling_interval = info.get("Sampling interval")
        if sampling_interval is None:
            raise ValueError(f"Sampling interval not found.")

        n = len(array)
        time_array = np.linspace(time_of_first_sample, n * sampling_interval, n)

        data = pd.DataFrame(array, index=time_array)

    else:
        logger.warning("Reference channel type [implicit/explicit] unknown.")
        data = pd.DataFrame(array)

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
