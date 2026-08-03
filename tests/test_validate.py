"""
``Report.validate()`` — plan step 12. ``Report.describe()`` is
[tests/test_describe.py](test_describe.py), which reuses this module's helpers.

Both layers here are **fixture-free** (every report is built from empty ``Isomme``
objects), so the whole module runs in CI:

* :class:`TestChecks` — one synthetic criterion per check: the check fires on a
  broken block and stays quiet on the same block written correctly. This is what
  keeps the checks honest; a check that never fires is worse than no check.
* :class:`TestRegisteredReports` — every registered report must be **error**-free,
  and its remaining *warnings* must match ``tests/golden/validate.json``. A
  protocol is allowed to be irregular, so a warning is not a failure — but a new
  one has to be looked at, and an old one disappearing is worth noticing too.
  Re-baseline deliberately::

      .venv/Scripts/python.exe -m tests.test_validate --regen
      git diff tests/golden/
"""
from __future__ import annotations

import importlib
import json
import logging
import os
import sys
import tempfile
import unittest
from typing import Any

import numpy as np

import pyisomme
from pyisomme.limit import Limit
from pyisomme.report.criterion import Criterion
from pyisomme.report.euro_ncap.limits import Limit_A, Limit_C, Limit_G, Limit_M, Limit_P, Limit_W
from pyisomme.report.manual import Manual, manual
from pyisomme.report.report import Report
from pyisomme.report.validate import validate_tree
from tests.test_report_structure import REPORTS


logging.basicConfig(level=logging.ERROR)

GOLDEN_DIR = os.path.join(os.path.dirname(__file__), "golden")
VALIDATE_GOLDEN = os.path.join(GOLDEN_DIR, "validate.json")

slow = unittest.skipUnless(
    os.environ.get("PYISOMME_SLOW"),
    "renders 13 PPTX files (~2 min) - set PYISOMME_SLOW=1 to run",
)

CODE = "?1HICR0015??00RX"


def build(name: str) -> Report:
    """One registered report, constructed from empty Isommes."""
    dotted, _, n_isomme = next(entry for entry in REPORTS if entry[1] == name)
    module = importlib.import_module(f"pyisomme.report.{dotted}")
    return getattr(module, name)([pyisomme.Isomme(test_number=f"T{i}") for i in range(n_isomme)])


def checks_of(criterion: Criterion) -> set[str]:
    """Which checks fire on a standalone criterion."""
    return {issue.check for issue in validate_tree(criterion)}


def leaf(limit_list: list[Limit], **attributes: Any) -> Criterion:
    """A named leaf criterion carrying ``limit_list``, detached from any report."""
    made: type[Criterion] = type("Made", (Criterion,),
                                 {"name": "Made", "calculation": lambda self: None, **attributes})
    criterion = made.__new__(made)  # bypass __init__: it wants a report to register limits with
    criterion.name = "Made"
    criterion.limits = pyisomme.Limits(name="test", limit_list=limit_list)
    return criterion


def attach(parent: Criterion, name: str, child: Criterion) -> Criterion:
    """
    Hang ``child`` off ``parent`` as a subcriterion.

    Goes through ``setattr`` rather than ``parent.name = child`` so a type checker
    leaves it alone: ``Criterion.__setattr__`` types its value ``Undeclared`` on
    purpose (step 4), to reject a mistyped input name statically. A subcriterion is
    the one thing it accepts at runtime and cannot express in that annotation.
    """
    setattr(parent, name, child)
    return child


def sliding_scale(good: float, marginal: float, weak: float, poor: float,
                  capping: float | None = None) -> list[Limit]:
    """
    A Euro-NCAP 4-point block, written the way the report modules write it.

    ``poor < good`` makes it a descending scale (femur Fz, neck My), whose flags
    are the mirror image — the Good row bounds the band from below.
    """
    best, worse = ("upper", "lower") if poor > good else ("lower", "upper")
    bounds_best: dict[str, Any] = {best: True}
    opens_worse: dict[str, Any] = {worse: True}
    rows = [
        Limit_G([CODE], func=lambda x: good, **bounds_best),
        Limit_A([CODE], func=lambda x: good, **opens_worse),
        Limit_M([CODE], func=lambda x: marginal, **opens_worse),
        Limit_W([CODE], func=lambda x: weak, **opens_worse),
    ]
    if capping is None or capping != poor:
        rows.append(Limit_P([CODE], func=lambda x: poor, **opens_worse))
    else:
        # `capped_at_poor`: the Poor row drops its flag when Capping sits on it.
        rows.append(Limit_P([CODE], func=lambda x: poor))
    if capping is not None:
        rows.append(Limit_C([CODE], func=lambda x: capping, **opens_worse))
    return rows


class TestChecks(unittest.TestCase):
    """Each check fires on a broken definition and stays quiet on a correct one."""

    def test_correct_scale_is_silent(self) -> None:
        self.assertEqual(checks_of(leaf(sliding_scale(500, 566.667, 633.333, 700))), set())

    def test_correct_capped_scale_is_silent(self) -> None:
        self.assertEqual(
            checks_of(leaf(sliding_scale(500, 566.667, 633.333, 700, capping=700))), set())

    def test_capping_above_poor_keeps_the_poor_flag(self) -> None:
        """Capping at a *different* value: both rows are flagged, and that is correct."""
        self.assertEqual(
            checks_of(leaf(sliding_scale(-36, -40.333, -44.667, -49, capping=-57))), set())

    def test_unnamed_criterion(self) -> None:
        criterion = leaf([])
        criterion.name = None
        self.assertIn("name", checks_of(criterion))

    def test_perturbed_intermediate(self) -> None:
        """The check that replaces the withdrawn step 5: 566.667 -> 556.667."""
        issues = validate_tree(leaf(sliding_scale(500, 556.667, 633.333, 700)))
        self.assertEqual([issue.check for issue in issues], ["limit_interpolation"])
        self.assertIn("556.667", issues[0].message)
        self.assertIn("566.667", issues[0].message)

    def test_perturbed_intermediate_on_a_negative_scale(self) -> None:
        self.assertIn("limit_interpolation",
                      checks_of(leaf(sliding_scale(-2.6, -3.9, -5.0, -6.2))))

    def test_poor_row_flagged_at_the_capping_value(self) -> None:
        """The `capped_at_poor` typo: Poor keeps `lower` although Capping sits on it."""
        rows = sliding_scale(500, 566.667, 633.333, 700, capping=700)
        rows[4].lower = True
        self.assertIn("limit_capping", checks_of(leaf(rows)))

    def test_unsuperseded_row_without_a_flag(self) -> None:
        rows = sliding_scale(500, 566.667, 633.333, 700)
        rows[4].lower = None
        self.assertIn("limit_capping", checks_of(leaf(rows)))

    def test_worse_row_flagged_the_wrong_way(self) -> None:
        rows = sliding_scale(500, 566.667, 633.333, 700)
        rows[2].lower, rows[2].upper = None, True
        self.assertIn("limit_flags", checks_of(leaf(rows)))

    def test_best_row_is_not_the_extreme(self) -> None:
        rows = sliding_scale(500, 566.667, 633.333, 700)
        rows[0].upper, rows[0].lower = None, True
        rows[3].lower, rows[3].upper = None, True
        self.assertIn("limit_flags", checks_of(leaf(rows)))

    def test_mixed_units_in_one_block(self) -> None:
        rows = sliding_scale(500, 566.667, 633.333, 700)
        rows[2].y_unit = "mm"
        self.assertIn("limit_unit", checks_of(leaf(rows)))

    def test_asymmetric_symmetric_block(self) -> None:
        """Poor mistyped as -1.90 on one side of a ± scale only."""
        rows = sliding_scale(1.20, 1.45, 1.70, 1.95) + sliding_scale(-1.20, -1.45, -1.70, -1.90)
        self.assertIn("limit_symmetry", checks_of(leaf(rows)))

    def test_symmetric_block_is_silent(self) -> None:
        rows = sliding_scale(1.20, 1.45, 1.70, 1.95) + sliding_scale(-1.20, -1.45, -1.70, -1.95)
        self.assertEqual(checks_of(leaf(rows)), set())

    def test_code_pattern_length(self) -> None:
        self.assertIn("code_pattern", checks_of(leaf([Limit(["?1HICR0015??00R"], func=lambda x: 1.0)])))

    def test_code_pattern_character_class_counts_as_one(self) -> None:
        """`fnmatch` reads `[03]` as one code character, so this pattern is fine."""
        self.assertEqual(
            checks_of(leaf([Limit(["?1CHST000[03]??DSX?"], func=lambda x: 1.0, lower=True)])),
            set())

    def test_code_pattern_with_an_impossible_character(self) -> None:
        self.assertIn("code_pattern",
                      checks_of(leaf([Limit(["?1CHST0000 ?DSX?"], func=lambda x: 1.0)])))

    def test_unused_manual_input(self) -> None:
        class Unused(Criterion):
            name = "Unused"
            never_read: Manual[bool, manual(False, doc="declared and forgotten")]

            def calculation(self) -> None:
                pass

        criterion = Unused.__new__(Unused)
        criterion.name = "Unused"
        criterion.limits = pyisomme.Limits(name="test", limit_list=[])
        self.assertIn("unused_input", checks_of(criterion))


class TestMaxRating(unittest.TestCase):
    """``max_rating`` is checked against the limits below it, or the children below it."""

    def tree(self, parent_max: float, aggregation: str) -> Criterion:
        parent = leaf([], max_rating=parent_max, aggregation=aggregation)
        attach(parent, "head", leaf(sliding_scale(500, 566.667, 633.333, 700), max_rating=4.0))
        attach(parent, "chest", leaf(sliding_scale(-30, -35, -40, -45), max_rating=4.0))
        return parent

    def test_matching_aggregation_is_silent(self) -> None:
        self.assertEqual(checks_of(self.tree(8.0, "sum")), set())
        self.assertEqual(checks_of(self.tree(4.0, "min")), set())

    def test_broken_aggregation(self) -> None:
        issues = [issue for issue in validate_tree(self.tree(16.0, "sum"))
                  if issue.check == "max_rating"]
        self.assertEqual(len(issues), 1, issues)
        self.assertIn("sum", issues[0].message)

    def test_unachievable_leaf_max(self) -> None:
        criterion = leaf(sliding_scale(500, 566.667, 633.333, 700), max_rating=5.0)
        self.assertIn("max_rating", checks_of(criterion))

    def test_unknown_aggregation(self) -> None:
        issues = validate_tree(leaf([], max_rating=4.0, aggregation="average"))
        self.assertEqual([issue.severity for issue in issues], ["error"])

    def test_undeclared_max_rating_says_nothing(self) -> None:
        self.assertEqual(checks_of(leaf(sliding_scale(500, 566.667, 633.333, 700))), set())


class TestOrphans(unittest.TestCase):
    def test_criterion_reachable_twice(self) -> None:
        parent = leaf([])
        child = leaf([])
        attach(parent, "first", child)
        attach(parent, "second", child)
        self.assertIn("orphan", checks_of(parent))

    def test_limit_left_behind_by_a_rebuild(self) -> None:
        report = build("EuroNCAP_Frontal_50kmh")
        isomme = report.isomme_list[0]
        report.limits[isomme].limit_list.append(Limit([CODE], func=lambda x: 1.0))
        orphans = [issue for issue in report.validate() if issue.check == "orphan"]
        self.assertEqual(len(orphans), 1, orphans)


class TestRegisteredReports(unittest.TestCase):
    def test_no_errors(self) -> None:
        for _, name, _ in REPORTS:
            with self.subTest(report=name):
                errors = build(name).validate(errors_only=True)
                self.assertEqual([str(issue) for issue in errors], [])

    def test_warnings_match_golden(self) -> None:
        if not os.path.exists(VALIDATE_GOLDEN):
            self.fail(f"missing {VALIDATE_GOLDEN} — create it with "
                      f"`python -m tests.test_validate --regen`")
        with open(VALIDATE_GOLDEN, encoding="utf-8") as handle:
            golden = json.load(handle)
        current = produce_validate()
        self.assertEqual(sorted(golden), sorted(current), "the set of reports changed")
        for name in sorted(current):
            with self.subTest(report=name):
                self.assertEqual(
                    golden[name], current[name],
                    f"{name}'s validate() warnings changed. A new warning is a finding to look "
                    f"at, not a formality; once judged, re-baseline with "
                    f"`python -m tests.test_validate --regen` and say why in the progress log.",
                )

    def test_calculate_smoke(self) -> None:
        """Every report survives construct -> calculate on a test with no channels."""
        for _, name, _ in REPORTS:
            with self.subTest(report=name):
                with np.errstate(all="ignore"):
                    build(name).calculate()

    @slow
    def test_export_smoke(self) -> None:
        """...and renders, which is where a page that resolves criteria breaks."""
        with tempfile.TemporaryDirectory() as directory:
            for _, name, _ in REPORTS:
                with self.subTest(report=name):
                    with np.errstate(all="ignore"):
                        report = build(name).calculate()
                        report.export_pptx(os.path.join(directory, f"{name}.pptx"))


# --------------------------------------------------------------------------- #
# baseline
# --------------------------------------------------------------------------- #

def produce_validate() -> dict[str, list[str]]:
    return {name: [str(issue) for issue in build(name).validate()] for _, name, _ in REPORTS}


def _regen() -> int:
    data = produce_validate()
    with open(VALIDATE_GOLDEN, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=1, sort_keys=True)
        handle.write("\n")
    warnings = sum(len(issues) for issues in data.values())
    print(f"  {VALIDATE_GOLDEN}: {warnings} warnings over {len(data)} reports")
    print("\nReview `git diff tests/golden/` before committing.")
    return 0


if __name__ == "__main__":
    if "--regen" in sys.argv:
        raise SystemExit(_regen())
    unittest.main()
