"""Tests for the error taxonomy and the 3-state criterion outcome."""

import types
import typing

import numpy as np
import pytest

from pyisomme.errors import (
    MissingData,
    PyisommeError,
    Status,
    UnsupportedCalculationError,
)
from pyisomme.isomme import Isomme
from pyisomme.report.criterion import Criterion


class _FakeReport:
    """Minimal stand-in for a Report (Criterion only needs `.name` at construction)."""

    name = "test-report"


class TestErrorTaxonomy:
    def test_missing_data_is_pyisomme_error(self) -> None:
        assert issubclass(MissingData, PyisommeError)

    def test_missing_data_records_what_was_missing(self) -> None:
        err = MissingData("11HEAD??00??ACRA", "fallback")
        assert err.what == ("11HEAD??00??ACRA", "fallback")
        assert "11HEAD??00??ACRA" in str(err)

    def test_unsupported_calculation_is_not_implemented_error(self) -> None:
        assert issubclass(UnsupportedCalculationError, PyisommeError)
        assert issubclass(UnsupportedCalculationError, NotImplementedError)


class TestCriterionOutcomes:
    @pytest.fixture
    def empty_isomme(self) -> Isomme:
        return Isomme("T1")

    @pytest.fixture
    def fake_report(self) -> _FakeReport:
        return _FakeReport()

    @pytest.fixture
    def make_criterion(
        self, fake_report: _FakeReport, empty_isomme: Isomme
    ) -> typing.Callable[[typing.Callable[..., None]], Criterion]:
        """Factory fixture that binds a custom calculation method to a fresh Criterion."""

        def _factory(calculation_func: typing.Callable[..., None]) -> Criterion:
            criterion = Criterion(fake_report, empty_isomme)
            criterion.calculation = types.MethodType(calculation_func, criterion)
            return criterion

        return _factory

    def test_default_status_is_pending(
        self, fake_report: _FakeReport, empty_isomme: Isomme
    ) -> None:
        assert Criterion(fake_report, empty_isomme).status is Status.PENDING

    def test_ok(self, make_criterion) -> None:
        def calculation(self: Criterion) -> None:
            self.value = 1.0
            self.rating = 2.0

        c = make_criterion(calculation)
        c.calculate()

        assert c.status is Status.OK
        assert c.value == 1.0

    def test_missing_data_via_require_channel(self, make_criterion) -> None:
        def calculation(self: Criterion) -> None:
            self.require_channel("11HEAD??00??ACRA")  # not present in an empty Isomme

        c = make_criterion(calculation)
        c.calculate()

        assert c.status is Status.NA
        assert isinstance(c.na_reason, MissingData)
        assert np.isnan(c.value)

    def test_missing_data_via_require_test_info(self, make_criterion) -> None:
        def calculation(self: Criterion) -> None:
            self.require_test_info("Driver position object 1")

        c = make_criterion(calculation)
        c.calculate()

        assert c.status is Status.NA

    def test_require_returns_value_when_present(self, make_criterion) -> None:
        def calculation(self: Criterion) -> None:
            self.value = self.require(42, "something")

        c = make_criterion(calculation)
        c.calculate()

        assert c.status is Status.OK
        assert c.value == 42

    def test_unexpected_error(self, make_criterion) -> None:
        def calculation(self: Criterion) -> None:
            raise RuntimeError("boom")

        c = make_criterion(calculation)
        c.calculate()

        assert c.status is Status.ERROR
