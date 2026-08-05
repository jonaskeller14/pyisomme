"""
Golden-file regression net for the report refactor (plan Step 1).

Each covered report is constructed, calculated and compared against a committed
JSON snapshot. See ``tests/golden_utils.py`` for the two comparison layers and
``tests/golden_regen.py`` for how to re-baseline a deliberate change.
"""
from __future__ import annotations

import logging
import os
import unittest

from tests import golden_utils


logging.basicConfig(level=logging.ERROR)

class TestGolden(unittest.TestCase):
    """One test per covered report; each builds the report from scratch."""

    def _check(self, stem: str) -> None:
        if not os.path.exists(golden_utils.golden_path(stem)):
            self.fail(
                f"missing golden file {golden_utils.golden_path(stem)} — "
                f"create it with `python -m tests.golden_regen {stem}`"
            )

        current = golden_utils.produce_isolated(stem)
        golden = golden_utils.load(stem)
        regressions, improvements = golden_utils.compare(golden, current)

        for improvement in improvements:
            print(f"[golden:{stem}] improvement (tolerated): {improvement}")

        if regressions:
            listing = "\n  - ".join(regressions)
            self.fail(
                f"{len(regressions)} regression(s) against tests/golden/{stem}.json:\n  - {listing}\n\n"
                f"If the change is intended, re-baseline with "
                f"`python -m tests.golden_regen {stem}` and explain the diff in the progress log."
            )

    def test_all_reports(self):
        for stem in golden_utils.BUILDERS:
            with self.subTest(report=stem):
                self._check(stem)


class TestGoldenCoverage(unittest.TestCase):
    """The golden files must actually contain something worth comparing."""

    def test_every_builder_has_a_committed_golden(self):
        for stem in golden_utils.BUILDERS:
            self.assertTrue(
                os.path.exists(golden_utils.golden_path(stem)),
                f"{stem} has a builder but no committed golden file",
            )

    def test_goldens_are_not_empty(self):
        for stem in golden_utils.BUILDERS:
            golden = golden_utils.load(stem)
            self.assertGreater(len(golden["results"]), 0, f"{stem}: no test results captured")
            self.assertGreater(len(golden["print_results"]), 0, f"{stem}: no printed results captured")

    def test_synthetic_data_has_no_missing_channels(self):
        """NA means the shared synthetic fixture failed to supply a report input."""
        for stem in golden_utils.BUILDERS:
            golden = golden_utils.load(stem)
            missing = [f"{test}:{path}" for test, tree in golden["results"].items()
                       for path, node in tree.items() if node["status"] == "NA"]
            self.assertEqual([], missing, f"{stem}: incomplete synthetic data")

    def test_calculations_have_no_errors(self):
        """A re-baseline must not normalize a swallowed calculation exception."""
        for stem in golden_utils.BUILDERS:
            golden = golden_utils.load(stem)
            errors = {path for tree in golden["results"].values()
                      for path, node in tree.items() if node["status"] == "ERROR"}
            self.assertEqual(set(), errors, stem)


class TestComparisonSemantics(unittest.TestCase):
    """
    Unit tests for `compare` itself — the net is worthless if it cannot fail.

    These use hand-built dicts, so they need no fixture data and run instantly.
    """

    def _golden(self, **result_overrides) -> dict:
        node = {"value": 1.0, "rating": 4.0, "color": "green", "status": "OK"}
        node.update(result_overrides)
        return {
            "report": "Fake",
            "results": {"t1": {"a": node}},
            "print_results": ["A: Value=1 Rating=4"],
        }

    def test_identical_is_clean(self):
        golden = self._golden()
        regressions, improvements = golden_utils.compare(golden, self._golden())
        self.assertEqual([], regressions)
        self.assertEqual([], improvements)

    def test_changed_value_is_a_regression(self):
        regressions, _ = golden_utils.compare(self._golden(), self._golden(value=2.0))
        self.assertEqual(1, len(regressions))
        self.assertIn("a.value", regressions[0])

    def test_tiny_float_drift_within_rtol_is_accepted(self):
        regressions, _ = golden_utils.compare(self._golden(), self._golden(value=1.0 + 1e-13))
        self.assertEqual([], regressions)

    def test_known_value_becoming_nan_is_a_regression(self):
        regressions, _ = golden_utils.compare(self._golden(), self._golden(value="nan"))
        self.assertEqual(1, len(regressions))

    def test_nan_becoming_a_number_is_an_improvement(self):
        regressions, improvements = golden_utils.compare(self._golden(value="nan"), self._golden(value=3.0))
        self.assertEqual([], regressions)
        self.assertEqual(1, len(improvements))

    def test_nan_staying_nan_is_clean(self):
        regressions, improvements = golden_utils.compare(self._golden(value="nan"), self._golden(value="nan"))
        self.assertEqual([], regressions)
        self.assertEqual([], improvements)

    def test_status_downgrade_is_a_regression(self):
        regressions, _ = golden_utils.compare(self._golden(), self._golden(status="ERROR"))
        self.assertEqual(1, len(regressions))

    def test_print_results_change_is_a_regression(self):
        current = self._golden()
        current["print_results"] = ["changed"]
        regressions, _ = golden_utils.compare(self._golden(), current)
        self.assertEqual(["print_results output changed"], regressions)

    def test_error_becoming_na_is_an_improvement(self):
        # This is exactly what Step 3's `require_channel` is expected to do.
        regressions, improvements = golden_utils.compare(
            self._golden(status="ERROR"), self._golden(status="NA")
        )
        self.assertEqual([], regressions)
        self.assertEqual(1, len(improvements))

    def test_disappearing_criterion_is_a_regression(self):
        current = self._golden()
        current["results"]["t1"] = {}
        regressions, _ = golden_utils.compare(self._golden(), current)
        self.assertTrue(any("disappeared" in r for r in regressions))

    def test_bool_and_float_are_not_conflated(self):
        # `submarining` and friends store bools; False must not equal 0.0.
        self.assertFalse(golden_utils.equal(False, 0.0))
        self.assertTrue(golden_utils.equal(False, False))


if __name__ == "__main__":
    unittest.main()
