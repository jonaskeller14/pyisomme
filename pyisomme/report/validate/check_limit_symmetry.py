from __future__ import annotations

from typing import TYPE_CHECKING
from collections.abc import Iterator

from pyisomme.report.validate.issue import Issue, IssueSeverity
from pyisomme.report.validate.util import blocks, rows_text, sample, sides

if TYPE_CHECKING:
    from pyisomme.report.criterion import Criterion


def check_limit_symmetry(path: str, criterion: Criterion) -> Iterator[Issue]:
    """A ±block's two sides are exact mirrors — same ratings at negated values."""
    for patterns, limits in blocks(criterion).items():
        reference = sample(limits, 0.0)
        if reference is None:
            continue
        halves = sides(reference)
        if len(halves) != 2:
            continue
        positive, negative = halves
        left = sorted((row.rating, round(row.y, 9)) for row in positive)
        right = sorted((row.rating, round(-row.y, 9)) for row in negative)
        if left != right:
            yield Issue("limit_symmetry", IssueSeverity.WARNING, path,
                        f"limit block {list(patterns)} has rows on both sides of zero but they "
                        f"are not mirrors: +{rows_text(positive)} vs -{rows_text(negative)}.")
