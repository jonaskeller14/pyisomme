from __future__ import annotations

from typing import TYPE_CHECKING, Callable
from collections.abc import Iterator

from pyisomme.report.validate.check_code_pattern import check_code_pattern
from pyisomme.report.validate.check_limit_capping import check_limit_capping
from pyisomme.report.validate.check_limit_flags import check_limit_flags
from pyisomme.report.validate.check_limit_interpolation import check_limit_interpolation
from pyisomme.report.validate.check_limit_symmetry import check_limit_symmetry
from pyisomme.report.validate.check_limit_unit import check_limit_unit
from pyisomme.report.validate.check_max_rating import check_max_rating
from pyisomme.report.validate.check_name import check_name
from pyisomme.report.validate.check_unused_input import check_unused_input
from pyisomme.report.validate.issue import Issue, IssueSeverity

if TYPE_CHECKING:
    from pyisomme.report.criterion import Criterion
    from pyisomme.report.report import Report


CHECKS: tuple[Callable[[str, Criterion], Iterator[Issue]], ...] = (
    check_name,
    check_code_pattern,
    check_max_rating,
    check_limit_unit,
    check_limit_flags,
    check_limit_capping,
    check_limit_interpolation,
    check_limit_symmetry,
    check_unused_input,
)


# --------------------------------------------------------------------------- #
# entry points
# --------------------------------------------------------------------------- #

def validate_criterion(path: str, criterion: Criterion) -> Iterator[Issue]:
    """Run every check against one criterion, honouring its ``validate_ignore``."""
    ignored = criterion.validate_ignore
    for check in CHECKS:
        if check.__name__.removeprefix("check_") in ignored:
            continue
        yield from check(path, criterion)


def validate_tree(overall: Criterion) -> list[Issue]:
    """Every issue in one criterion tree, parent before children."""
    issues: list[Issue] = []
    seen: dict[int, str] = {}
    for path, criterion in overall.walk():
        first = seen.setdefault(id(criterion), path)
        if first != path:
            issues.append(Issue("orphan", IssueSeverity.ERROR, path,
                                f"the same criterion object is also reachable as {first!r}; "
                                f"one of the two references is stale."))
            continue
        issues += validate_criterion(path, criterion)
    return issues


def validate_report(report: Report) -> list[Issue]:
    """
    Every issue in ``report``, over all of its tests.

    Criterion-level checks run against the first test only — the tree is the same
    for each — while the report-level limit list is checked per test, because that
    is where a rebuilt subtree can leave a stale row behind.
    """
    issues: list[Issue] = []
    if not report.isomme_list:
        return issues

    issues += validate_tree(report.overall(report.isomme_list[0]))

    for isomme in report.isomme_list:
        overall = report.overall(isomme)
        owned = {id(limit) for _, criterion in overall.walk()
                 for limit in criterion.limits.limit_list}
        for limit in report.limits[isomme].limit_list:
            if id(limit) not in owned:
                issues.append(Issue("orphan", IssueSeverity.ERROR, "",
                                    f"{isomme}: limit {limit.name or type(limit).__name__} "
                                    f"{limit.code_patterns} is in the report's limit list but "
                                    f"belongs to no criterion — a rebuilt subtree left it "
                                    f"behind, and it still draws in the plots."))
    return issues
