from __future__ import annotations

import datetime
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReportProtocol:
    version: str
    sources: tuple[str, ...] = field(repr=False)
    name: str | None = field(default=None, repr=False)
    date: datetime.date | None = field(default=None, repr=False)
