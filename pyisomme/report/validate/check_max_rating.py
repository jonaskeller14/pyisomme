from __future__ import annotations

import math
from typing import TYPE_CHECKING, Callable
from collections.abc import Iterator, Sequence

import numpy as np

from pyisomme.report.validate.issue import Issue, IssueSeverity
from pyisomme.report.validate.util import close

if TYPE_CHECKING:
    from pyisomme.report.criterion import Criterion


#: Names ``Criterion.aggregation`` may take, and what they mean for
#: ``Criterion.max_rating`` propagation.
AGGREGATIONS: dict[str, Callable[[Sequence[float]], float]] = {
    "min": lambda values: float(np.min(values)),
    "max": lambda values: float(np.max(values)),
    "sum": lambda values: float(np.sum(values)),
    "mean": lambda values: float(np.mean(values)),
    "first": lambda values: float(values[0]),
}


def derived_max_rating(criterion: Criterion) -> float | None:
    """
    The best score ``criterion``'s own limit rows award, or ``None`` if it has none.

    A leaf that rates off a limit block already states its maximum — in the block.
    Nothing is gained by typing it out again as ``max_rating = 4``, and a second
    copy can only disagree with the first, so leaves are left undeclared and this
    is what :func:`~pyisomme.report.describe.describe_report` renders for them.
    """
    ratings = [
        float(limit.rating)
        for limit in criterion.limits.limit_list
        if limit.rating is not None and not math.isnan(float(limit.rating))
    ]
    return max(ratings) if ratings else None


def check_max_rating(path: str, criterion: Criterion) -> Iterator[Issue]:
    """
    A declared ``max_rating`` is achievable.

    For a leaf that rates off its own limits, the best-rated row must award
    exactly it. For a parent that declares an ``aggregation``, the same
    aggregation of its children's declared maxima must reproduce it — so a child
    dropped out of the sum, or a box whose scale was widened without widening its
    parent's, is caught before anyone reads the score.
    """
    if criterion.aggregation is not None and criterion.aggregation not in AGGREGATIONS:
        yield Issue(
            "max_rating",
            IssueSeverity.ERROR,
            path,
            f"unknown aggregation {criterion.aggregation!r}; "
            f"expected one of {sorted(AGGREGATIONS)}.",
        )
        return
    if criterion.max_rating is None:
        return

    children = [child for _, child in criterion.get_children()]
    declared = [child.max_rating for child in children if child.max_rating is not None]

    if criterion.aggregation is not None:
        if len(declared) != len(children):
            yield Issue(
                "max_rating",
                IssueSeverity.WARNING,
                path,
                f"aggregates {criterion.aggregation!r} over {len(children)} children "
                f"but only {len(declared)} of them declare a max_rating, so the "
                f"propagation cannot be checked.",
            )
            return
        expected = AGGREGATIONS[criterion.aggregation](declared)
        if not close(expected, criterion.max_rating):
            yield Issue(
                "max_rating",
                IssueSeverity.WARNING,
                path,
                f"declares max_rating={criterion.max_rating:g} but "
                f"{criterion.aggregation}({[f'{value:g}' for value in declared]}) "
                f"= {expected:g}.",
            )
        return

    best = derived_max_rating(criterion)
    if best is None:
        return
    if not close(best, criterion.max_rating):
        yield Issue(
            "max_rating",
            IssueSeverity.WARNING,
            path,
            f"declares max_rating={criterion.max_rating:g} but its best limit row "
            f"awards {best:g}.",
        )
