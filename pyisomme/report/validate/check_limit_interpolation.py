from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING
from collections.abc import Iterator

from pyisomme.report.validate.issue import Issue, IssueSeverity
from pyisomme.report.validate.util import Direction, Row, close, per_side, block_label

if TYPE_CHECKING:
    from pyisomme.report.criterion import Criterion

DECIMALS = 3
GOOD, MARGINAL, WEAK, POOR = 4.0, 2.669, 1.329, 0.0


def check_limit_interpolation(path: str, criterion: Criterion) -> Iterator[Issue]:
    """
    On a Euro-NCAP 4-point scale the two intermediates lie 1/3 and 2/3 of the way
    from the higher- to the lower-performance limit.

    Those are what a protocol PDF prints as **two** numbers; the intermediates are
    arithmetic the module author does by hand. This is the check that replaces the
    withdrawn step 5 — the two printed numbers stay literal and PDF-checkable, and
    the two derived ones are machine-checked against them, rather than a helper
    owning all four.
    """
    def at(patterns: tuple[str, ...], side: list[Row], direction: Direction, x: float) -> Iterator[Issue]:
        by_rating: dict[float, list[Row]] = defaultdict(list)
        for row in side:
            by_rating[round(row.rating, 6)].append(row)
        if not all(rating in by_rating for rating in (GOOD, MARGINAL, WEAK, POOR)):
            return
        # Good and Adequate share a value; take the one furthest from Poor, which
        # is the row the protocol prints as the higher-performance limit.
        good = min(by_rating[GOOD], key=lambda row: row.y * direction.sign).y
        poor = by_rating[POOR][0].y

        for label, rating, fraction in (("Marginal", MARGINAL, 1 / 3), ("Weak", WEAK, 2 / 3)):
            actual = by_rating[rating][0].y
            expected = round(good + fraction * (poor - good), DECIMALS)
            if not close(actual, expected, tolerance=10 ** -DECIMALS / 2):
                yield Issue("limit_interpolation", IssueSeverity.WARNING, path,
                            f"{block_label(patterns, side)}: {label} is {actual:g}, but "
                            f"{fraction:.3f} of the way from Good {good:g} to Poor {poor:g} "
                            f"is {expected:g} (x={x:g}).")

    return per_side(criterion, at)
