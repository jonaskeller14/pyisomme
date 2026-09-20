from __future__ import annotations

import re
from collections.abc import Iterator
from typing import TYPE_CHECKING

from pyisomme.code import CODE_LENGTH, pattern_length
from pyisomme.report.validate.issue import Issue, IssueSeverity

if TYPE_CHECKING:
    from pyisomme.report.criterion import Criterion

_INVALID_PATTERN_CHARS = re.compile(r"[^A-Za-z0-9?*]")


def _without_classes(pattern: str) -> str:
    """``pattern`` with every fnmatch character class removed."""
    return re.sub(r"\[!?\]?[^]]*\]", "", pattern)


def check_code_pattern(path: str, criterion: Criterion) -> Iterator[Issue]:
    """
    Every declared code pattern matches channel codes of the right length.

    ``Limits.find_limits`` runs the patterns through ``fnmatch``, so a character
    class (``?1CHST000[03]??DSX?``) is one code character, not four. A pattern of
    the wrong length silently matches nothing at all — the criterion then rates
    against an empty limit set and blames the channel.
    """
    for limit in criterion.limits.limits:
        label = limit.name or type(limit).__name__
        if not limit.code_patterns:
            yield Issue(
                "code_pattern",
                IssueSeverity.WARNING,
                path,
                f"{label} declares no code_patterns, so `Limits.find_limits` can never "
                f"reach it — it only works if the criterion reads it out of "
                f"`self.limits.limits` directly.",
            )
            continue
        for pattern in limit.code_patterns:
            invalid = _INVALID_PATTERN_CHARS.findall(_without_classes(pattern))
            if invalid:
                yield Issue(
                    "code_pattern",
                    IssueSeverity.ERROR,
                    path,
                    f"{label}: {pattern!r} contains {sorted(set(invalid))}, which no "
                    f"channel code can hold (letters, digits and '?' only).",
                )
                continue
            length = pattern_length(pattern)
            if length is not None and length != CODE_LENGTH:
                yield Issue(
                    "code_pattern",
                    IssueSeverity.ERROR,
                    path,
                    f"{label}: {pattern!r} matches codes of {length} characters, "
                    f"but a channel code is {CODE_LENGTH}.",
                )
