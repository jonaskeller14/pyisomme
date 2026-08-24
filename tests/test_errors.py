"""Tests for the error taxonomy and the 3-state criterion outcome."""

import types
import typing

import pytest

from pyisomme.errors import (
    MissingData,
    PyisommeError,
    Status,
    UnsupportedCalculationError,
)
from pyisomme.isomme import Isomme
from pyisomme.report.criterion import Criterion
from pyisomme.report.criterion_result import CriterionResult


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
    ) -> typing.Callable[[typing.Callable[..., CriterionResult]], Criterion]:
        """Factory fixture that binds a custom calculation method to a fresh Criterion."""

        def _factory(
            calculation_func: typing.Callable[..., CriterionResult],
        ) -> Criterion:
            criterion = Criterion(fake_report, empty_isomme)
            criterion.calculation = types.MethodType(calculation_func, criterion)
            return criterion

        return _factory

    def test_default_status_is_pending(
        self, fake_report: _FakeReport, empty_isomme: Isomme
    ) -> None:
        assert Criterion(fake_report, empty_isomme).status is Status.PENDING

    def test_ok(self, make_criterion) -> None:
        def calculation(self: Criterion) -> CriterionResult:
            return CriterionResult(channel=None, value=1.0, rating=2.0, color=None)

        c = make_criterion(calculation)
        c.calculate()

        assert c.status is Status.OK
        assert c.result is not None
        assert c.result.value == 1.0

    def test_missing_data_via_require_channel(self, make_criterion) -> None:
        def calculation(self: Criterion) -> CriterionResult:
            self.require_channel("11HEAD??00??ACRA")  # not present in an empty Isomme

        c = make_criterion(calculation)
        c.calculate()

        assert c.status is Status.NA
        assert isinstance(c.na_reason, MissingData)
        assert c.result is None

    def test_missing_data_via_require_test_info(self, make_criterion) -> None:
        def calculation(self: Criterion) -> CriterionResult:
            self.require_test_info("Driver position object 1")

        c = make_criterion(calculation)
        c.calculate()

        assert c.status is Status.NA

    def test_require_returns_value_when_present(self, make_criterion) -> None:
        def calculation(self: Criterion) -> CriterionResult:
            value = self.require(42, "something")
            return CriterionResult(channel=None, value=value, rating=value, color=None)

        c = make_criterion(calculation)
        c.calculate()

        assert c.status is Status.OK
        assert c.result is not None
        assert c.result.value == 42

    def test_unexpected_error(self, make_criterion) -> None:
        def calculation(self: Criterion) -> CriterionResult:
            raise RuntimeError("boom")

        c = make_criterion(calculation)
        c.calculate()

        assert c.status is Status.ERROR
