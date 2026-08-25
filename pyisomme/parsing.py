from __future__ import annotations

import logging
import re
from datetime import datetime

import numpy as np
import pandas as pd

from pyisomme.channel import Channel
from pyisomme.errors import MalformedFileError, ParsingChannelStatus, ParsingTimeStatus
from pyisomme.info import Info, InfoValue

logger = logging.getLogger(__name__)


NORMALIZATION_COMMENT_PREFIX = "Normalization: "
HEADER_LINE_PATTERN = re.compile(r"([^:]*[^:\s])\s*:(.*)")


def parse_mme(text: str) -> Info:
    lines = text.splitlines()
    info = Info()
    for line in lines:
        line = line.strip()

        if line == "":
            continue
        match = HEADER_LINE_PATTERN.fullmatch(line)
        if match is None:
            logger.error(f"Could not parse malformed line: '{line}'")
            continue
        else:
            name, value = match.groups()
            info[name] = get_value(value)
    return info


def parse_chn(text: str) -> Info:
    return parse_mme(text)


def parse_header_and_data(text: str) -> tuple[Info, np.ndarray]:
    """
    Split a channel file into its ``Info`` header and its numeric data column.

    Raises :class:`MalformedFileError` if the data section is not numeric — that is a
    structural defect the data cannot recover from, so it fails hard rather than
    silently producing a garbage channel.
    """
    lines = text.splitlines()
    info = Info()
    start_data_idx = 0
    for idx, line in enumerate(lines):
        line = line.strip()

        if line == "":
            continue
        match = HEADER_LINE_PATTERN.fullmatch(line)
        if match is None:
            start_data_idx = idx
            break
        else:
            name, value = match.groups()
            info[name] = get_value(value)

    array_str = np.array(lines[start_data_idx:])
    array_str[array_str == "NOVALUE"] = np.nan
    try:
        array = np.array(array_str, dtype=float)
    except ValueError as error:
        raise MalformedFileError(
            f"[{info.get('Channel code')}] non-numeric channel data: {error}"
        ) from error
    return info, array


def resolve_time_axis(
    info: Info, n: int
) -> tuple[np.ndarray | None, ParsingTimeStatus]:
    """
    Reconstruct a channel's time axis from its header, centralizing *every*
    reference-channel / timing convention in one place (the ingest normalization
    boundary). Convention drift ("implicit" vs "explicit", missing
    ``Time of first sample``, undeclared reference type) is resolved here, once, so
    downstream code may assume a known-normalized shape.

    :return: ``(index, note)`` where ``index`` is the reconstructed time axis, or
        ``None`` if it could not be resolved and a plain sample index must be used;
        and ``note`` is a human-readable description of any *assumption* made — ``None``
        when the file fully specified the convention, so no assumption was necessary.
    """

    def get_float(key: str) -> float | None:
        value = info.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return float(value)

    reference_value = info.get("Reference channel")
    reference = reference_value if isinstance(reference_value, str) else None
    reference_channel_code_value = info.get("Reference channel name")
    reference_channel_code = (
        reference_channel_code_value
        if isinstance(reference_channel_code_value, str)
        else None
    )
    time_of_first_sample = get_float("Time of first sample")
    sampling_interval = get_float("Sampling interval")

    def implicit_axis(first: float, interval: float) -> np.ndarray:
        return np.linspace(first, first + (n - 1) * interval, n)

    # 1. Convention explicitly declared in the file: honor it (no assumption). A declared
    #    convention with missing/unresolvable timing is reported so it is not silent.
    if reference == "implicit":
        if time_of_first_sample is None:
            if sampling_interval is None:
                return (
                    None,
                    ParsingTimeStatus.IMPLICIT_FIRST_SAMPLE_AND_INTERVAL_MISSING,
                )
            else:
                return implicit_axis(
                    0, sampling_interval
                ), ParsingTimeStatus.IMPLICIT_ASSUME_FIRST_SAMPLE_ZERO
        if sampling_interval is None:
            return None, ParsingTimeStatus.IMPLICIT_SAMPLING_INTERVAL_MISSING
        return implicit_axis(
            time_of_first_sample, sampling_interval
        ), ParsingTimeStatus.IMPLICIT
    if reference == "explicit":
        if reference_channel_code is None:
            return None, ParsingTimeStatus.EXPLICIT_REF_CHANNEL_NAME_MISSING
        return None, ParsingTimeStatus.EXPLICIT

    # 2. Convention undeclared: infer it from whichever fields are present, and record it.
    if time_of_first_sample is not None and sampling_interval is not None:
        return implicit_axis(
            time_of_first_sample, sampling_interval
        ), ParsingTimeStatus.ASSUMED_IMPLICIT
    if sampling_interval is not None:
        return implicit_axis(
            0, sampling_interval
        ), ParsingTimeStatus.ASSUMED_IMPLICIT_WITH_START_ZERO
    if reference_channel_code is not None:
        return None, ParsingTimeStatus.ASSUMED_EXPLICIT

    # 3. No timing information at all.
    return None, ParsingTimeStatus.NO_TIME_INFO


def parse_xxx(text: str) -> tuple[Channel, ParsingChannelStatus]:
    info, array = parse_header_and_data(text)
    code_value = info.get("Channel code")
    if not isinstance(code_value, str):
        raise MalformedFileError("Missing or invalid 'Channel code' descriptor.")
    code = code_value
    unit_value = info.get("Unit")
    unit = unit_value if isinstance(unit_value, str) else None

    index, time_status = resolve_time_axis(info, len(array))

    is_tirs = code[2:6] == "TIRS"
    if not is_tirs and time_status in (
        ParsingTimeStatus.EXPLICIT,
        ParsingTimeStatus.ASSUMED_EXPLICIT,
    ):
        status = ParsingChannelStatus.EXPLICIT_TIME_RESOLUTION_PENDING
    else:
        status = ParsingChannelStatus.OK

    if is_tirs:
        pass  # A sample index is the canonical shape for a time reference channel.
    elif time_status == ParsingTimeStatus.ASSUMED_IMPLICIT:
        logger.warning(f"[{code}] {time_status.value}")
        info["Reference channel"] = "implicit"
        info["Comments"] = NORMALIZATION_COMMENT_PREFIX + time_status.value
    elif time_status == ParsingTimeStatus.ASSUMED_EXPLICIT:
        logger.warning(f"[{code}] {time_status.value}")
        info["Reference channel"] = "explicit"
        info["Comments"] = NORMALIZATION_COMMENT_PREFIX + time_status.value
    elif time_status == ParsingTimeStatus.IMPLICIT_ASSUME_FIRST_SAMPLE_ZERO:
        logger.warning(f"[{code}] {time_status.value}")
        info["Time of first sample"] = 0.0
        info["Comments"] = NORMALIZATION_COMMENT_PREFIX + time_status.value
    elif time_status == ParsingTimeStatus.ASSUMED_IMPLICIT_WITH_START_ZERO:
        logger.warning(f"[{code}] {time_status.value}")
        info["Reference channel"] = "implicit"
        info["Time of first sample"] = 0.0
        info["Comments"] = NORMALIZATION_COMMENT_PREFIX + time_status.value
    elif time_status in (
        ParsingTimeStatus.IMPLICIT_SAMPLING_INTERVAL_MISSING,
        ParsingTimeStatus.EXPLICIT_REF_CHANNEL_NAME_MISSING,
        ParsingTimeStatus.NO_TIME_INFO,
        ParsingTimeStatus.IMPLICIT_FIRST_SAMPLE_AND_INTERVAL_MISSING,
    ):
        logger.error(f"[{code}] {time_status.value} -> using sample index")
        info["Comments"] = NORMALIZATION_COMMENT_PREFIX + time_status.value

    if index is None:
        data = pd.DataFrame(array)
    else:
        data = pd.DataFrame(array, index=index)

    return Channel(code, data, unit=unit, info=info), status


def get_value(text: str) -> InfoValue:
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
