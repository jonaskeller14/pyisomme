from __future__ import annotations

import enum
from dataclasses import dataclass
from collections.abc import Sequence


class IssueSeverity(str, enum.Enum):
    WARNING = "warning"
    ERROR = "error"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Issue:
    """One finding. ``path`` locates the criterion inside the report's tree."""

    check: str
    severity: IssueSeverity
    path: str
    message: str

    @property
    def is_error(self) -> bool:
        return self.severity is IssueSeverity.ERROR

    def __str__(self) -> str:
        return f"[{self.severity}] {self.check} @ {self.path or 'Overall'}: {self.message}"


def format_issues(issues: Sequence[Issue]) -> str:
    """The issue list as text, errors first."""
    ordered = sorted(issues, key=lambda issue: (not issue.is_error, issue.path, issue.check))
    return "\n".join(str(issue) for issue in ordered)
