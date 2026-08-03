from __future__ import annotations

from typing import TYPE_CHECKING
from collections.abc import Iterator

from pyisomme.report.validate.issue import Issue, IssueSeverity
from pyisomme.report.validate.util import (
    Direction, Row, close, flag, per_side, block_label, rows_text, superseded,
)

if TYPE_CHECKING:
    from pyisomme.report.criterion import Criterion


def check_limit_flags(path: str, criterion: Criterion) -> Iterator[Issue]:
    """
    ``upper``/``lower`` agree with the ordering of the rows' values.

    On a higher-is-worse scale exactly one row — the best one, at the lowest
    value — carries ``upper``, and every worse row carries ``lower``; mirrored the
    other way round. Get this wrong and ``Limits.get_limit_ratings(interpolate=False)``
    stops at the first row whose flag happens to match and awards a band the value
    is not in, without anything looking amiss.

    A row that is superseded at its own value (the ``capped_at_poor`` case) is
    exempt here and belongs to :func:`~pyisomme.report.validate.check_limit_capping.check_limit_capping`.
    """
    def at(patterns: tuple[str, ...], side: list[Row], direction: Direction, x: float) -> Iterator[Issue]:
        best_rows = [row for row in side if flag(row.limit, direction.best_flag)]
        extreme = (min if direction is Direction.HIGHER_IS_WORSE else max)(row.y for row in side)

        if len(best_rows) != 1:
            yield Issue("limit_flags", IssueSeverity.WARNING, path,
                        f"{block_label(patterns, side)} has {len(best_rows)} rows flagged "
                        f"{direction.best_flag}=True; a scale bounds its best band exactly once. "
                        f"Rows at x={x:g}: {rows_text(side)}.")
            return

        best = best_rows[0]
        if not close(best.y, extreme):
            yield Issue("limit_flags", IssueSeverity.WARNING, path,
                        f"{block_label(patterns, side)}: {best} bounds the best band but is not the "
                        f"{'lowest' if direction is Direction.HIGHER_IS_WORSE else 'highest'} row "
                        f"({extreme:g}) at x={x:g}. Rows: {rows_text(side)}.")

        for row in side:
            if row is best or superseded(row, side, direction):
                continue
            if not flag(row.limit, direction.worse_flag):
                yield Issue("limit_flags", IssueSeverity.WARNING, path,
                            f"{block_label(patterns, side)}: {row} opens a worse band and should "
                            f"carry {direction.worse_flag}=True at x={x:g}. "
                            f"Rows: {rows_text(side)}.")

    return per_side(criterion, at)
