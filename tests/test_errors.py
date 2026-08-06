"""Fixture-free tests for the error taxonomy and the 3-state criterion outcome."""

import unittest
import logging

import numpy as np

from pyisomme.isomme import Isomme
from pyisomme.errors import MissingData, PyisommeError, Status, UnsupportedCalculationError
from pyisomme.report.criterion import Criterion


logging.basicConfig(level=logging.CRITICAL)  # silence the expected ERROR traceback


class _FakeReport:
    """Minimal stand-in for a Report (Criterion only needs `.name` at construction)."""
    name = "test-report"


class TestErrorTaxonomy(unittest.TestCase):
    def test_missing_data_is_pyisomme_error(self):
        self.assertTrue(issubclass(MissingData, PyisommeError))

    def test_missing_data_records_what_was_missing(self):
        err = MissingData("11HEAD??00??ACRA", "fallback")
        self.assertEqual(err.what, ("11HEAD??00??ACRA", "fallback"))
        self.assertIn("11HEAD??00??ACRA", str(err))

    def test_unsupported_calculation_is_not_implemented_error(self):
        self.assertTrue(issubclass(UnsupportedCalculationError, PyisommeError))
        self.assertTrue(issubclass(UnsupportedCalculationError, NotImplementedError))


class TestCriterionOutcomes(unittest.TestCase):
    def setUp(self):
        self.report = _FakeReport()
        self.isomme = Isomme("T1")  # empty: no channels, no test info

    def _make(self, calculation):
        criterion = Criterion(self.report, self.isomme)
        criterion.calculation = calculation.__get__(criterion, Criterion)
        return criterion

    def test_default_status_is_pending(self):
        self.assertIs(Criterion(self.report, self.isomme).status, Status.PENDING)

    def test_ok(self):
        def calculation(self):
            self.value = 1.0
            self.rating = 2.0
        c = self._make(calculation)
        c.calculate()
        self.assertIs(c.status, Status.OK)
        self.assertEqual(c.value, 1.0)

    def test_missing_data_via_require_channel(self):
        def calculation(self):
            self.require_channel("11HEAD??00??ACRA")  # not present in an empty Isomme
        c = self._make(calculation)
        c.calculate()
        self.assertIs(c.status, Status.NA)
        self.assertIsInstance(c.na_reason, MissingData)
        self.assertTrue(np.isnan(c.value))  # unchanged -> pages still render as before

    def test_missing_data_via_require_test_info(self):
        def calculation(self):
            self.require_test_info("Driver position object 1")
        c = self._make(calculation)
        c.calculate()
        self.assertIs(c.status, Status.NA)

    def test_require_returns_value_when_present(self):
        def calculation(self):
            self.value = self.require(42, "something")
        c = self._make(calculation)
        c.calculate()
        self.assertIs(c.status, Status.OK)
        self.assertEqual(c.value, 42)

    def test_unexpected_error(self):
        def calculation(self):
            raise RuntimeError("boom")
        c = self._make(calculation)
        c.calculate()
        self.assertIs(c.status, Status.ERROR)


if __name__ == "__main__":
    unittest.main()
