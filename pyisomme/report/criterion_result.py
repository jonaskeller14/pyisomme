from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pyisomme.channel import Channel


@dataclass(frozen=True)
class CriterionResult:
    """Complete, successful output produced by a criterion calculation.

    The value is expressed in channel.unit whenever a channel is present. The
    channel must therefore be converted before the value is read
    """

    channel: Channel | None
    value: float
    rating: float
    color: str | tuple[Any, ...] | None
