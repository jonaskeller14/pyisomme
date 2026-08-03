from __future__ import annotations

from typing import TYPE_CHECKING
from collections.abc import Iterator

from pyisomme.report.validate.issue import Issue, IssueSeverity
from pyisomme.report.validate.util import blocks

if TYPE_CHECKING:
    from pyisomme.report.criterion import Criterion


def check_limit_unit(path: str, criterion: Criterion) -> Iterator[Issue]:
    """One block, one ``y_unit`` — mixed units inside a scale rate against garbage."""
    for patterns, limits in blocks(criterion).items():
        units = {str(limit.y_unit) for limit in limits}
        if len(units) > 1:
            yield Issue("limit_unit", IssueSeverity.WARNING, path,
                        f"limit block {list(patterns)} mixes y_units {sorted(units)}.")
