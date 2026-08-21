import pytest

from pyisomme.isomme import Isomme
from pyisomme.limit import Limit
from pyisomme.report.criterion import Criterion
from pyisomme.report.manual import Manual, manual
from pyisomme.report.report import Report
from pyisomme.report.validate.validate import validate_tree


class Overall(Criterion):
    pass


class EmptyReport(Report[Overall]):
    Criterion_Overall = Overall
    pass


@pytest.fixture
def empty_report_isomme() -> tuple[Report, Isomme]:
    isomme = Isomme()
    return EmptyReport(isomme_list=[isomme]), isomme


def test_check_name(empty_report_isomme) -> None:
    class UnnamedCriterion(Criterion):
        pass

    criterion = UnnamedCriterion(*empty_report_isomme)

    assert "name" in {issue.check for issue in validate_tree(criterion)}


def test_code_pattern_with_an_impossible_character(empty_report_isomme) -> None:
    class ImpossibleCodeCriterion(Criterion):
        pass

    criterion = ImpossibleCodeCriterion(*empty_report_isomme)
    criterion.extend_limit_list([Limit(("?1CHST0000 ?DSX?",), func=lambda x: 1.0)])

    assert "code_pattern" in {issue.check for issue in validate_tree(criterion)}


def test_code_pattern_length(empty_report_isomme) -> None:
    class WrongLengthCriterion(Criterion):
        pass

    criterion = WrongLengthCriterion(*empty_report_isomme)
    criterion.extend_limit_list([Limit(("?1HICR0015??00R",), func=lambda x: 1.0)])

    assert "code_pattern" in {issue.check for issue in validate_tree(criterion)}


def test_code_pattern_character_class_counts_as_one(empty_report_isomme) -> None:
    class CharacterClassCriterion(Criterion):
        pass

    criterion = CharacterClassCriterion(*empty_report_isomme)
    criterion.extend_limit_list(
        [Limit(("?1CHST000[03]??DSX?",), func=lambda x: 1.0, lower=True)]
    )

    assert not {issue.check for issue in validate_tree(criterion)} - {"name"}


def test_perturbed_intermediate(empty_report_isomme) -> None:
    class PerturbedCriterion(Criterion):
        pass

    criterion = PerturbedCriterion(*empty_report_isomme)
    criterion.extend_limit_list(
        [
            Limit(
                ("?1HICR0015??00RX",),
                func=lambda x: 500,
                rating=4,
                upper=True,
            ),
            Limit(
                ("?1HICR0015??00RX",),
                func=lambda x: 556.667,
                rating=2.669,
                lower=True,
            ),
            Limit(
                ("?1HICR0015??00RX",),
                func=lambda x: 633.333,
                rating=1.329,
                lower=True,
            ),
            Limit(
                ("?1HICR0015??00RX",),
                func=lambda x: 700,
                rating=0,
                lower=True,
            ),
        ]
    )

    issues = validate_tree(criterion)
    checks = {issue.check for issue in issues}
    interpolation_issue = next(
        issue for issue in issues if issue.check == "limit_interpolation"
    )

    assert checks == {"name", "limit_interpolation"}
    assert "556.667" in interpolation_issue.message
    assert "566.667" in interpolation_issue.message


def test_poor_row_flagged_at_the_capping_value(empty_report_isomme) -> None:
    class CappedCriterion(Criterion):
        pass

    criterion = CappedCriterion(*empty_report_isomme)
    criterion.extend_limit_list(
        [
            Limit(("?1HICR0015??00RX",), func=lambda x: 500, rating=4, upper=True),
            Limit(("?1HICR0015??00RX",), func=lambda x: 700, rating=0, lower=True),
            Limit(("?1HICR0015??00RX",), func=lambda x: 700, rating=-1, lower=True),
        ]
    )

    assert "limit_capping" in {issue.check for issue in validate_tree(criterion)}


def test_unsuperseded_row_without_a_flag(empty_report_isomme) -> None:
    class UnflaggedCriterion(Criterion):
        pass

    criterion = UnflaggedCriterion(*empty_report_isomme)
    criterion.extend_limit_list(
        [
            Limit(("?1HICR0015??00RX",), func=lambda x: 500, rating=4, upper=True),
            Limit(("?1HICR0015??00RX",), func=lambda x: 700, rating=0),
        ]
    )

    assert "limit_capping" in {issue.check for issue in validate_tree(criterion)}


def test_worse_row_flagged_the_wrong_way(empty_report_isomme) -> None:
    class WrongFlagCriterion(Criterion):
        pass

    criterion = WrongFlagCriterion(*empty_report_isomme)
    criterion.extend_limit_list(
        [
            Limit(("?1HICR0015??00RX",), func=lambda x: 500, rating=4, upper=True),
            Limit(("?1HICR0015??00RX",), func=lambda x: 633.333, rating=2, upper=True),
            Limit(("?1HICR0015??00RX",), func=lambda x: 700, rating=0, lower=True),
        ]
    )

    assert "limit_flags" in {issue.check for issue in validate_tree(criterion)}


def test_best_row_is_not_the_extreme(empty_report_isomme) -> None:
    class NonExtremeCriterion(Criterion):
        pass

    criterion = NonExtremeCriterion(*empty_report_isomme)
    criterion.extend_limit_list(
        [
            Limit(("?1HICR0015??00RX",), func=lambda x: 500, rating=4, lower=True),
            Limit(("?1HICR0015??00RX",), func=lambda x: 633.333, rating=2),
            Limit(("?1HICR0015??00RX",), func=lambda x: 700, rating=0, upper=True),
        ]
    )

    assert "limit_flags" in {issue.check for issue in validate_tree(criterion)}


def test_mixed_units_in_one_block(empty_report_isomme) -> None:
    class MixedUnitCriterion(Criterion):
        pass

    criterion = MixedUnitCriterion(*empty_report_isomme)
    criterion.extend_limit_list(
        [
            Limit(("?1HICR0015??00RX",), func=lambda x: 500, y_unit="1"),
            Limit(("?1HICR0015??00RX",), func=lambda x: 633.333, y_unit="mm"),
        ]
    )

    assert "limit_unit" in {issue.check for issue in validate_tree(criterion)}


def test_asymmetric_symmetric_block(empty_report_isomme) -> None:
    class AsymmetricCriterion(Criterion):
        pass

    criterion = AsymmetricCriterion(*empty_report_isomme)
    criterion.extend_limit_list(
        [
            Limit(("?1HICR0015??00RX",), func=lambda x: 1.20, rating=4),
            Limit(("?1HICR0015??00RX",), func=lambda x: 1.45, rating=2.669),
            Limit(("?1HICR0015??00RX",), func=lambda x: 1.70, rating=1.329),
            Limit(("?1HICR0015??00RX",), func=lambda x: 1.95, rating=0),
            Limit(("?1HICR0015??00RX",), func=lambda x: -1.20, rating=4),
            Limit(("?1HICR0015??00RX",), func=lambda x: -1.45, rating=2.669),
            Limit(("?1HICR0015??00RX",), func=lambda x: -1.70, rating=1.329),
            Limit(("?1HICR0015??00RX",), func=lambda x: -1.90, rating=0),
        ]
    )

    assert "limit_symmetry" in {issue.check for issue in validate_tree(criterion)}


def test_unused_manual_input(empty_report_isomme) -> None:
    class UnusedCriterion(Criterion):
        never_read: Manual[bool, manual(False, doc="declared and forgotten")]

    criterion = UnusedCriterion(*empty_report_isomme)

    assert "unused_input" in {issue.check for issue in validate_tree(criterion)}
