from __future__ import annotations

from pyisomme.channel import Channel
from pyisomme.info import Info
from pyisomme.errors import MalformedFileError

import logging
from datetime import datetime
import numpy as np
import pandas as pd
import re


logger = logging.getLogger(__name__)


#: Prefix used when :func:`parse_xxx` records an ingest-normalization assumption. The
#: note is appended to the **standard** ISO/TS 13499 ``Comments`` field (a repeatable
#: free-text keyword already present in .mme/.chn/.001 headers) rather than a custom key,
#: so exported files stay format-conformant. The prefix keeps the note distinguishable
#: from authored comments and lets :func:`get_normalization_notes` recover it — an
#: auditable "normalization log": convention drift is resolved once, here at the ingest
#: boundary, and the decision travels with the channel instead of being re-derived
#: downstream.
NORMALIZATION_COMMENT_PREFIX = "Normalization: "


def get_normalization_notes(channel) -> list[str]:
    """Return the ingest-normalization assumptions recorded on ``channel`` (may be empty)."""
    n = len(NORMALIZATION_COMMENT_PREFIX)
    return [value[n:] for name, value in channel.info if name == "Comments" and isinstance(value, str) and value.startswith(NORMALIZATION_COMMENT_PREFIX)]


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


def parse_header_and_data(text: str) -> tuple[Info, np.ndarray]:
    """
    Split a channel file into its ``Info`` header and its numeric data column.

    Raises :class:`MalformedFileError` if the data section is not numeric — that is a
    structural defect the data cannot recover from, so it fails hard rather than
    silently producing a garbage channel.
    """
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

    array_str = np.array(lines[start_data_idx:])
    array_str[array_str == "NOVALUE"] = np.nan
    try:
        array = np.array(array_str, dtype=float)
    except ValueError as error:
        raise MalformedFileError(f"[{info.get('Channel code')}] non-numeric channel data: {error}") from error
    return info, array


def resolve_time_axis(info: Info, n: int, isomme) -> tuple[np.ndarray | None, str | None]:
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
    reference = info.get("Reference channel")
    reference_channel_code = info.get("Reference channel name")
    time_of_first_sample = info.get("Time of first sample")
    sampling_interval = info.get("Sampling interval")

    def implicit_axis(first: float, interval: float) -> np.ndarray:
        return np.linspace(first, first + (n - 1) * interval, n)

    def explicit_axis(reference_code: str) -> np.ndarray | None:
        reference_channel = isomme.get_channel(reference_code)
        return None if reference_channel is None else reference_channel.get_data()

    # 1. Convention explicitly declared in the file: honor it (no assumption). A declared
    #    convention with missing/unresolvable timing is reported so it is not silent.
    if reference == "implicit":
        if time_of_first_sample is None:
            return None, "declared 'implicit' but 'Time of first sample' missing; using sample index"
        if sampling_interval is None:
            return None, "declared 'implicit' but 'Sampling interval' missing; using sample index"
        return implicit_axis(time_of_first_sample, sampling_interval), None
    if reference == "explicit":
        if reference_channel_code is None:
            return None, "declared 'explicit' but 'Reference channel name' missing; using sample index"
        index = explicit_axis(reference_channel_code)
        if index is None:
            return None, f"declared 'explicit' but reference channel '{reference_channel_code}' not available; using sample index"
        return index, None

    # 2. Convention undeclared: infer it from whichever fields are present, and record it.
    if time_of_first_sample is not None and sampling_interval is not None:
        return (implicit_axis(time_of_first_sample, sampling_interval),
                "assumed 'Reference channel' = 'implicit' (timing present, convention undeclared)")
    if sampling_interval is not None:
        return (implicit_axis(0, sampling_interval),
                "assumed 'Reference channel' = 'implicit' with 'Time of first sample' = 0")
    if reference_channel_code is not None:
        index = explicit_axis(reference_channel_code)
        if index is not None:
            return index, f"assumed 'Reference channel' = 'explicit' -> '{reference_channel_code}'"
        return None, f"assumed 'explicit' but reference channel '{reference_channel_code}' not available; using sample index"

    # 3. No timing information at all.
    return None, "no timing information; using sample index"


def parse_xxx(text: str, isomme) -> Channel:
    info, array = parse_header_and_data(text)
    code = info.get("Channel code")
    unit = info.get("Unit")

    index, note = resolve_time_axis(info, len(array), isomme)

    if index is None:
        # No time axis could be reconstructed -> fall back to a plain sample index.
        # For TIRS (time-reference) channels this is the expected, canonical shape, so it
        # is not flagged; for anything else the assumption is logged and recorded so a
        # silently-wrong time axis can never pass unnoticed.
        is_tirs = isinstance(code, str) and code[2:6] == "TIRS"
        if not is_tirs and note is not None:
            logger.warning(f"[{code}] {note}")
            info["Comments"] = NORMALIZATION_COMMENT_PREFIX + note
        data = pd.DataFrame(array)
        data = data[~data.index.duplicated(keep='first')].sort_index()
        return Channel(code, data, unit=unit, info=info)

    if note is not None:
        logger.info(f"[{code}] {note}")
        info["Comments"] = NORMALIZATION_COMMENT_PREFIX + note
    return Channel(code, pd.DataFrame(array, index=index), unit=unit, info=info)


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
