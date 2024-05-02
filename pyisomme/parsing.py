from pyisomme.channel import Channel

import logging
from datetime import datetime
import numpy as np
import pandas as pd


def parse_mme(mme_file) -> dict:
    """
    # TODO: nicht von leerem ausgehen sondern ergänzen -> self -> methode in class reinziehen
    # TODO: Comment können mehrfach vorkommen -> list default empty
    :param mme_file:
    :return:
    """
    lines = mme_file.readlines()
    test_info = {}
    for line in lines:
        try:
            try:
                line = line.strip().decode("iso-8859-1")
            except UnicodeDecodeError:
                line = line.strip().decode('utf-8')
        except AttributeError:
            line = line.strip()

        if line == "":
            continue

        # Extract variable name and value
        if len(line.split()) == 2:
            name = line.split()[0].strip()
            value = get_value(line.split()[1].strip())
        elif len(line.split(":", 1)) >= 2:
            name = line.split(":", 1)[0].strip()
            value = get_value(line.split(":", 1)[1].strip())
        else:
            logging.error(f"Could not parse malformed line: '{line}'")
            continue

        # Add to dict
        if name not in test_info:
            test_info[name] = value
        else:
            logging.error(f"NotImplementedError: Multiple Variables with the same name found: '{name}'")
    return test_info


def parse_chn(chn_file) -> dict:
    return parse_mme(chn_file)


def parse_xxx(xxx_file, test_number="data"):
    lines = xxx_file.readlines()
    info = {}
    start_data_idx = 0
    for idx, line in enumerate(lines):
        try:
            try:
                line = line.strip().decode("iso-8859-1")
            except UnicodeDecodeError:
                line = line.strip().decode('utf-8')
        except AttributeError:
            line = line.strip()

        if line == "":
            continue
        if len(line.split(":", 1)) >= 2:
            name = line.split(":", 1)[0].strip()
            value = get_value(line.split(":", 1)[1].strip())
        else:
            start_data_idx = idx
            break

        # Add to dict
        if name not in info:
            info[name] = value
        else:
            logging.error(f"NotImplementedError: Multiple Variables with the same name found: '{name}'")

    code = info.get("Channel code")
    unit = info.get("Unit")

    # data
    array = np.array(lines[start_data_idx:])
    # TODO: Explicit
    # Implicit
    if "Time of first sample" in info and "Sampling interval" in info:
        n = len(array)
        time_array = np.linspace(info["Time of first sample"], n * info["Sampling interval"], n)
        data = pd.DataFrame({test_number: array, "Time": time_array}).set_index("Time")
    else:
        logging.error(f"'Time of first sample' and 'Sampling interval' missing in channel information of {code}")
        data = pd.DataFrame({test_number: array})
    data[test_number] = data[test_number].astype(float)
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
    text = text[1:] if text[0] == ":" else text
    # None
    if text.upper() in ("NOVALUE", "NONE") or text.strip() == "":
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