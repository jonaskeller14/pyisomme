from __future__ import annotations

from typing import TYPE_CHECKING
from collections.abc import Iterator

from pyisomme.report.validate.issue import Issue, IssueSeverity

if TYPE_CHECKING:
    from pyisomme.report.criterion import Criterion


def check_name(path: str, criterion: Criterion) -> Iterator[Issue]:
    """Every criterion is named — the name is what the PPTX and the log print."""
    if criterion.name is None:
        yield Issue(
            "name",
            IssueSeverity.ERROR,
            path,
            f"{type(criterion).__name__} declares no name; it renders as its class name.",
        )
