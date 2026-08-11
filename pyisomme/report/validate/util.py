from __future__ import annotations

import enum
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable
from collections.abc import Iterator, Sequence

import numpy as np

from pyisomme.limit import Limit
from pyisomme.report.validate.issue import Issue

if TYPE_CHECKING:
    from pyisomme.report.criterion import Criterion


#: x positions every ``Limit.func`` is sampled at. Constant limits ignore them;
#: corridors (IIHS neck, MPDB) are checked at each of them independently, because
#: a time-varying block may only violate a convention part of the way along.
SAMPLE_X: tuple[float, ...] = (0.0, 0.01, 0.05, 0.1)


class Direction(enum.Enum):
    """Which way "worse" runs along a limit block's y axis."""

    HIGHER_IS_WORSE = "higher_is_worse"
    LOWER_IS_WORSE = "lower_is_worse"

    @property
    def best_flag(self) -> str:
        """The flag the row bounding the *best* band carries (Good, Pass, 5 stars)."""
        return "upper" if self is Direction.HIGHER_IS_WORSE else "lower"

    @property
    def worse_flag(self) -> str:
        """The flag every row that opens a *worse* band carries."""
        return "lower" if self is Direction.HIGHER_IS_WORSE else "upper"

    @property
    def sign(self) -> float:
        """``+1`` when a higher value is worse, ``-1`` when a lower one is."""
        return 1.0 if self is Direction.HIGHER_IS_WORSE else -1.0


# --------------------------------------------------------------------------- #
# limit blocks
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Row:
    """One ``Limit`` of a block, sampled at one x."""

    limit: Limit
    y: float

    @property
    def rating(self) -> float:
        rating = getattr(self.limit, "rating", np.nan)
        return float(rating) if rating is not None else float("nan")

    @property
    def label(self) -> str:
        return self.limit.name or type(self.limit).__name__

    def __str__(self) -> str:
        flag = (
            "upper"
            if self.limit.upper
            else "lower"
            if self.limit.lower
            else "unflagged"
        )
        return f"{self.label}({self.y:g}, {flag})"


def blocks(criterion: Criterion) -> dict[tuple[str, ...], list[Limit]]:
    """
    The criterion's limits grouped into the blocks they were written as.

    One ``extend_limit_list`` call states one scale for one set of code patterns,
    so the patterns are the block key. A ± scale is written as one block with
    rows on both sides of zero; :func:`sides` splits it.
    """
    grouped: dict[tuple[str, ...], list[Limit]] = defaultdict(list)
    for limit in criterion.limits.limit_list:
        grouped[tuple(limit.code_patterns or ())].append(limit)
    return dict(grouped)


def sample(limits: Sequence[Limit], x: float) -> list[Row] | None:
    """Evaluate every limit of a block at ``x``; ``None`` if any of them cannot be."""
    rows = []
    for limit in limits:
        try:
            y = float(limit.func(x))
        except Exception:  # a limit whose func needs more than a bare float
            return None
        if not math.isfinite(y):
            return None
        rows.append(Row(limit=limit, y=y))
    return rows


def sides(reference: Sequence[Row]) -> list[list[Row]]:
    """
    Split a ± block into its two halves, by the sign each row has **at x=0**.

    The split is always read off the x=0 sample, so a corridor that crosses zero
    part-way along still keeps each row on the side it was written for.
    """
    positive = [row for row in reference if row.y >= 0]
    negative = [row for row in reference if row.y < 0]
    return [side for side in (positive, negative) if side]


def direction_of(rows: Sequence[Row]) -> Direction | None:
    """
    Which way this side runs, read off the ratings: the worst-rated row sits at
    the worst value. ``None`` when the rows carry fewer than two distinct
    ratings — a plotting-only corridor, which has no direction to check.
    """
    ratings = {row.rating for row in rows if not math.isnan(row.rating)}
    if len(ratings) < 2:
        return None
    best = max(rows, key=lambda row: row.rating)
    worst = min(rows, key=lambda row: row.rating)
    if worst.y > best.y:
        return Direction.HIGHER_IS_WORSE
    if worst.y < best.y:
        return Direction.LOWER_IS_WORSE
    return None


def flag(limit: Limit, name: str) -> bool:
    """Is ``limit``'s ``upper``/``lower`` flag set? (Both default to ``None``.)"""
    return getattr(limit, name) is True


def close(a: float, b: float, tolerance: float = 1e-9) -> bool:
    return math.isclose(a, b, rel_tol=0.0, abs_tol=tolerance)


def by_value(side: Sequence[Row]) -> list[tuple[float, list[Row]]]:
    """The side's rows grouped by the value they sit at, ascending."""
    grouped: dict[float, list[Row]] = defaultdict(list)
    for row in side:
        grouped[round(row.y, 9)].append(row)
    return sorted(grouped.items())


def superseded(row: Row, side: Sequence[Row], direction: Direction) -> bool:
    """
    Does another row at ``row``'s own value already open the worse band?

    That is the ``capped_at_poor`` case: the worse-rated row owns the flag, and
    this one is deliberately left unflagged so it cannot win the tie.
    """
    return any(
        other is not row
        and close(other.y, row.y)
        and other.rating < row.rating
        and flag(other.limit, direction.worse_flag)
        for other in side
    )


# --------------------------------------------------------------------------- #
# rendering a finding
# --------------------------------------------------------------------------- #


def block_label(patterns: tuple[str, ...], side: Sequence[Row]) -> str:
    sign = "(+)" if side and side[0].y >= 0 else "(-)"
    return f"limit block {list(patterns)} {sign}"


def rows_text(rows: Sequence[Row]) -> str:
    return (
        "[" + ", ".join(str(row) for row in sorted(rows, key=lambda row: row.y)) + "]"
    )


# --------------------------------------------------------------------------- #
# driving a check
# --------------------------------------------------------------------------- #

#: What :func:`per_side` calls: one block's patterns, one side of it sampled at
#: ``x``, and the direction that side runs in.
SideCheck = Callable[[tuple[str, ...], list[Row], Direction, float], Iterator[Issue]]


def per_side(criterion: Criterion, check: SideCheck) -> Iterator[Issue]:
    """
    Run ``check`` over every block **side**, at the first x sample that fails.

    Constant blocks would otherwise report the same finding once per sample; a
    corridor that only misbehaves late still gets caught, because every sample is
    tried until one of them has something to say.

    A side with fewer than two distinct ratings is a plotting corridor, not a
    scale, and is skipped — there is nothing to say about which way it runs.
    """
    for patterns, limits in blocks(criterion).items():
        reference = sample(limits, 0.0)
        if reference is None:
            continue
        for half in sides(reference):
            members = {id(row.limit) for row in half}
            for x in SAMPLE_X:
                rows = reference if x == 0.0 else sample(limits, x)
                if rows is None:
                    continue
                side = [row for row in rows if id(row.limit) in members]
                direction = direction_of(side)
                if direction is None:
                    continue
                found = list(check(patterns, side, direction, x))
                if found:
                    yield from found
                    break
