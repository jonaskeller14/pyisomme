from __future__ import annotations

from typing import TYPE_CHECKING
from collections.abc import Iterator

from pyisomme.report.validate.issue import Issue, IssueSeverity
from pyisomme.report.validate.util import (
    Direction,
    Row,
    by_value,
    flag,
    per_side,
    block_label,
    rows_text,
    superseded,
)

if TYPE_CHECKING:
    from pyisomme.report.criterion import Criterion


def check_limit_capping(path: str, criterion: Criterion) -> Iterator[Issue]:
    """
    Two rows at the same value never carry the same flag — the ``capped_at_poor``
    convention.

    Both flagged, and ``Limits.get_limits`` has two limits at distance zero from
    the same channel value: ``np.argmin`` breaks the tie by list order, so a value
    beyond capping renders red "Poor" instead of gray "Capping". Which row keeps
    the flag follows from where the flag points — the last band in that direction
    owns it.

    The convention holds across every capped scale in the repo and is today
    encoded only by accident, which makes it the most likely silent typo in a
    hand-written block.
    """

    def at(
        patterns: tuple[str, ...], side: list[Row], direction: Direction, x: float
    ) -> Iterator[Issue]:
        for value, group in by_value(side):
            for name in ("upper", "lower"):
                flagged = [row for row in group if flag(row.limit, name)]
                if len(flagged) < 2:
                    continue
                # The flag claims everything on one side of `value`; only the row
                # whose band actually reaches out there may carry it.
                owner = (min if name == direction.worse_flag else max)(
                    flagged, key=lambda row: row.rating
                )
                for row in flagged:
                    if row is not owner:
                        yield Issue(
                            "limit_capping",
                            IssueSeverity.WARNING,
                            path,
                            f"{block_label(patterns, side)}: {row} and {owner} sit at the "
                            f"same value {value:g} and both carry {name}=True, so which "
                            f"one wins is list order. {row.label} must carry no flag "
                            f"(x={x:g}).",
                        )

        for row in side:
            if flag(row.limit, "upper") or flag(row.limit, "lower"):
                continue
            if not superseded(row, side, direction):
                yield Issue(
                    "limit_capping",
                    IssueSeverity.WARNING,
                    path,
                    f"{block_label(patterns, side)}: {row} carries no upper/lower flag but "
                    f"nothing supersedes it at {row.y:g}, so it matches only an exactly "
                    f"equal value (x={x:g}). Rows: {rows_text(side)}.",
                )

    return per_side(criterion, at)
