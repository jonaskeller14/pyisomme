from __future__ import annotations

import io
from contextlib import redirect_stdout
from dataclasses import replace
from typing import Any

import numpy as np
import pytest

from pyisomme import Channel, Isomme, create_sample
from pyisomme.errors import InvalidCodeError, MissingData, Status
from pyisomme.limit import Limit
from pyisomme.report.criterion import Criterion, Role, sub
from pyisomme.report.criterion_result import CriterionResult
from pyisomme.report.ctx import Ctx, from_input, where
from pyisomme.report.manual import Manual, manual
from pyisomme.report.report import Report
from pyisomme.report.validate import validate_tree


def report_of(overall: type[Criterion], n: int = 1) -> tuple[Report, list[Isomme]]:
    """A minimal report around ``overall``, with ``n`` empty tests."""
    sample_report = type(
        "SampleReport",
        (Report,),
        {"name": "Sample Report", "Criterion_Overall": overall},
    )
    isomme_list = [Isomme(f"T{i}") for i in range(n)]
    return sample_report(isomme_list), isomme_list


class Rated(Criterion):
    """A leaf that reports whatever ``rating`` it was given, and counts its calls."""

    name = "Rated"
    calls: int = 0

    def calculation(self) -> CriterionResult:
        self.calls += 1
        return CriterionResult(
            channel=None, value=self.rating, rating=self.rating, color=None
        )


def rated(
    value: float, role: Role = Role.RESULT, name: str = "Rated"
) -> type[Criterion]:
    return type("Rated_", (Rated,), {"name": name, "rating": value, "role": role})


class TestDeclarationOrder:
    def test_declared_children_keep_protocol_order(self) -> None:
        """Not alphabetical: `zulu` is declared first and must come out first."""

        class Overall(Criterion):
            name = "Overall"
            zulu = sub(rated(1.0))
            alpha = sub(rated(2.0))
            mike = sub(rated(3.0))

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        assert [attr for attr, _ in report.overall(v1).get_children()] == [
            "zulu",
            "alpha",
            "mike",
        ]

    def test_subclass_appends_and_overrides_without_touching_the_base(self) -> None:
        class Base(Criterion):
            first = sub(rated(1.0))
            second = sub(rated(2.0))

            def calculation(self) -> None:
                pass

        class Derived(Base):
            third = sub(rated(3.0))
            second = sub(rated(9.0, name="Replaced"))

        report, (v1,) = report_of(Derived)
        children = dict(report.overall(v1).get_children())
        assert list(children) == ["first", "second", "third"]
        assert children["second"].name == "Replaced"

        base_report, (v2,) = report_of(Base)
        assert [attr for attr, _ in base_report.overall(v2).get_children()] == [
            "first",
            "second",
        ]

    def test_declared_then_added_then_legacy(self) -> None:
        """Coexistence (D-5): all three wiring styles in one node, in that order."""

        class Overall(Criterion):
            declared = sub(rated(1.0))

            def __init__(self, report: Report[Any], isomme: Isomme) -> None:
                super().__init__(report, isomme)
                self.legacy_z = rated(2.0)(report, isomme)
                self.legacy_a = rated(3.0)(report, isomme)

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        overall = report.overall(v1)
        overall.add_child("added", rated(4.0)(report, v1))
        assert [attr for attr, _ in overall.get_children()] == [
            "declared",
            "added",
            "legacy_z",
            "legacy_a",
        ]

    def test_walk_is_depth_first_in_declaration_order(self) -> None:
        class Leaf(Criterion):
            def calculation(self) -> None:
                pass

        class Branch(Criterion):
            zulu = sub(Leaf)
            alpha = sub(Leaf)

            def calculation(self) -> None:
                pass

        class Overall(Criterion):
            second = sub(Branch)
            first = sub(Leaf)

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        assert [path for path, _ in report.overall(v1).walk()] == [
            "",
            "second",
            "second/zulu",
            "second/alpha",
            "first",
        ]

    def test_print_results_follows_the_protocol_not_the_alphabet(self) -> None:
        class Overall(Criterion):
            name = "Overall"
            zulu = sub(rated(1.0, name="Zulu"))
            alpha = sub(rated(2.0, name="Alpha"))

            def calculation(self) -> None:
                pass

        report, _ = report_of(Overall)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            report.calculate().print_results()
        printed = [
            line.strip().split(":")[0] for line in buffer.getvalue().splitlines()[1:]
        ]
        assert printed == ["Overall", "Zulu", "Alpha"]


class TestAutoCalculation:
    def test_declared_children_are_calculated_by_the_framework(self) -> None:
        class Overall(Criterion):
            child = sub(rated(3.0))

            def calculation(self) -> CriterionResult:
                # No `self.child.calculate()` — that is the point.
                return CriterionResult(
                    channel=None,
                    value=self.min_of_children(),
                    rating=self.min_of_children(),
                    color=None,
                )

        report, (v1,) = report_of(Overall)
        report.calculate()
        assert report.overall(v1).child.calls == 1
        assert report.overall(v1).child.status == Status.OK
        assert report.overall(v1).result is not None
        assert report.overall(v1).result.rating == 3.0

    def test_children_are_calculated_before_the_parent(self) -> None:
        order: list[str] = []

        class Child(Criterion):
            def calculation(self) -> None:
                order.append("child")

        class Overall(Criterion):
            child = sub(Child)

            def prepare(self) -> None:
                order.append("prepare")

            def calculation(self) -> None:
                order.append("parent")

        report, _ = report_of(Overall)
        report.calculate()
        assert order == ["prepare", "child", "parent"]

    def test_grandchildren_are_calculated_too(self) -> None:
        class Branch(Criterion):
            leaf = sub(rated(2.0))

            def calculation(self) -> CriterionResult:
                rating = self.min_of_children()
                return CriterionResult(
                    channel=None, value=rating, rating=rating, color=None
                )

        class Overall(Criterion):
            branch = sub(Branch)

            def calculation(self) -> CriterionResult:
                rating = self.min_of_children()
                return CriterionResult(
                    channel=None, value=rating, rating=rating, color=None
                )

        report, (v1,) = report_of(Overall)
        report.calculate()
        assert report.overall(v1).result is not None
        assert report.overall(v1).result.rating == 2.0
        assert report.overall(v1).branch.leaf.calls == 1

    def test_added_children_are_calculated(self) -> None:
        class Overall(Criterion):
            def calculation(self) -> CriterionResult:
                rating = self.sum_of_children()
                return CriterionResult(
                    channel=None, value=rating, rating=rating, color=None
                )

        report, (v1,) = report_of(Overall)
        overall = report.overall(v1)
        overall.add_child("one", rated(1.0)(report, v1))
        overall.add_child("two", rated(2.0)(report, v1))
        report.calculate()
        assert overall.result is not None
        assert overall.result.rating == 3.0
        assert [child.calls for _, child in overall.get_children()] == [1, 1]

    def test_legacy_children_are_not_calculated_twice(self) -> None:
        """A not-yet-migrated parent calculates its own children; the framework must not."""

        class Overall(Criterion):
            def __init__(self, report: Report[Any], isomme: Isomme) -> None:
                super().__init__(report, isomme)
                self.criterion_legacy = rated(1.0)(report, isomme)

            def calculation(self) -> None:
                self.criterion_legacy.calculate()

        report, (v1,) = report_of(Overall)
        report.calculate()
        assert report.overall(v1).criterion_legacy.calls == 1

    def test_a_failing_child_does_not_stop_its_siblings(self) -> None:
        class Broken(Criterion):
            def calculation(self) -> None:
                raise MissingData("?1HEAD??00??ACRA")

        class Overall(Criterion):
            broken = sub(Broken)
            fine = sub(rated(4.0))

            def calculation(self) -> CriterionResult:
                rating = self.min_of_children()
                return CriterionResult(
                    channel=None, value=rating, rating=rating, color=None
                )

        report, (v1,) = report_of(Overall)
        report.calculate()
        overall = report.overall(v1)
        assert overall.broken.status == Status.NA
        assert overall.fine.status == Status.OK
        assert overall.status == Status.OK

    def test_add_child_sets_the_parent_link(self) -> None:
        class Overall(Criterion):
            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        overall = report.overall(v1)
        child = rated(1.0)(report, v1)
        overall.add_child("child", child)
        assert child.parent is overall

    def test_sub_sets_the_parent_link(self) -> None:
        class Overall(Criterion):
            child = sub(rated(1.0))

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        assert report.overall(v1).child.parent is report.overall(v1)
        assert report.overall(v1).parent is None

    def test_the_tree_exists_before_calculate(self) -> None:
        """G8: eager construction — manual inputs are set between build and calculate."""

        class Leaf(Criterion):
            hard_contact: Manual[bool, manual(True, doc="…")]

            def calculation(self) -> CriterionResult:
                rating = 1.0 if self.hard_contact else 0.0
                return CriterionResult(
                    channel=None, value=rating, rating=rating, color=None
                )

        class Overall(Criterion):
            leaf = sub(Leaf)

            def calculation(self) -> CriterionResult:
                rating = self.min_of_children()
                return CriterionResult(
                    channel=None, value=rating, rating=rating, color=None
                )

        report, (v1,) = report_of(Overall)
        report.overall(v1).leaf.hard_contact = False
        report.calculate()
        assert report.overall(v1).result is not None
        assert report.overall(v1).result.rating == 0.0


class Mixed(Criterion):
    """Two results and a modifier — the "min over results plus sum over modifiers" box."""

    name = "Mixed"
    good = sub(rated(4.0, name="Good"))
    bad = sub(rated(2.0, name="Bad"))
    penalty = sub(rated(-1.0, Role.MODIFIER, name="Penalty"))

    def calculation(self) -> CriterionResult:
        rating = self.min_of_children() + self.modifiers_sum()
        return CriterionResult(channel=None, value=rating, rating=rating, color=None)


class TestAggregation:
    def test_modifiers_are_excluded_from_the_headline(self) -> None:
        report, (v1,) = report_of(Mixed)
        report.calculate()
        overall = report.overall(v1)
        assert overall.min_of_children() == 2.0
        assert overall.sum_of_children() == 6.0
        assert overall.modifiers_sum() == -1.0
        assert overall.result is not None
        assert overall.result.rating == 1.0

    def test_aggregate_children_count_towards_the_headline(self) -> None:
        class Overall(Criterion):
            leaf = sub(rated(4.0))
            branch = sub(rated(1.0, Role.AGGREGATE))
            penalty = sub(rated(-2.0, Role.MODIFIER))

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        report.calculate()
        assert sorted(report.overall(v1).ratings_of_children()) == [1.0, 4.0]
        assert report.overall(v1).ratings_of_children(Role.MODIFIER) == [-2.0]

    def test_explicit_roles_select_exactly_those(self) -> None:
        report, (v1,) = report_of(Mixed)
        overall = report.overall(v1)
        assert [c.name for c in overall.children_by_role(Role.RESULT)] == [
            "Good",
            "Bad",
        ]
        assert [c.name for c in overall.children_by_role(Role.MODIFIER)] == ["Penalty"]
        assert len(overall.children_by_role(Role.RESULT, Role.MODIFIER)) == 3

    def test_nan_propagates_through_every_helper(self) -> None:
        """G9: a missing measurement must never look like a good score."""

        class Overall(Criterion):
            fine = sub(rated(4.0))
            missing = sub(rated(np.nan))

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        overall = report.overall(v1)
        assert np.isnan(overall.min_of_children())
        assert np.isnan(overall.max_of_children())
        assert np.isnan(overall.sum_of_children())
        assert np.isnan(overall.mean_of_children())

    def test_explicit_result_helpers_handle_unavailable_results(self) -> None:
        report, (v1,) = report_of(Mixed)
        criterion = rated(4.0)(report, v1)

        assert Criterion.result_of(criterion) is None
        assert np.isnan(Criterion.rating_of(criterion))
        assert np.isnan(Criterion.value_of(criterion))
        assert Criterion.channel_of(criterion) is None
        assert Criterion.color_of(criterion) is None

    def test_a_nan_tolerant_mean_needs_a_reason_and_records_it(self) -> None:
        class Overall(Criterion):
            fine = sub(rated(4.0))
            missing = sub(rated(np.nan))

            def calculation(self) -> CriterionResult:
                rating = self.mean_of_children(
                    skip_missing="no rear occupant in this test"
                )
                return CriterionResult(
                    channel=None, value=rating, rating=rating, color=None
                )

        report, (v1,) = report_of(Overall)
        report.calculate()
        overall = report.overall(v1)
        assert overall.result is not None
        assert overall.result.rating == 4.0
        assert overall.skip_missing == "no rear occupant in this test"

    def test_skip_missing_stays_unset_when_nothing_was_skipped(self) -> None:
        class Overall(Criterion):
            one = sub(rated(4.0))
            two = sub(rated(2.0))

            def calculation(self) -> CriterionResult:
                rating = self.mean_of_children(skip_missing="would be a lie")
                return CriterionResult(
                    channel=None, value=rating, rating=rating, color=None
                )

        report, (v1,) = report_of(Overall)
        report.calculate()
        assert report.overall(v1).result is not None
        assert report.overall(v1).result.rating == 3.0
        assert report.overall(v1).skip_missing is None

    def test_all_missing_stays_nan_even_when_tolerated(self) -> None:
        class Overall(Criterion):
            one = sub(rated(np.nan))

            def calculation(self) -> CriterionResult:
                rating = self.mean_of_children(skip_missing="whatever")
                return CriterionResult(
                    channel=None, value=rating, rating=rating, color=None
                )

        report, (v1,) = report_of(Overall)
        report.calculate()
        assert report.overall(v1).result is not None
        assert np.isnan(report.overall(v1).result.rating)

    def test_modifiers_sum_is_zero_without_modifiers(self) -> None:
        class Overall(Criterion):
            leaf = sub(rated(4.0))

            def calculation(self) -> CriterionResult:
                rating = self.min_of_children() + self.modifiers_sum()
                return CriterionResult(
                    channel=None, value=rating, rating=rating, color=None
                )

        report, (v1,) = report_of(Overall)
        report.calculate()
        assert report.overall(v1).result is not None
        assert report.overall(v1).result.rating == 4.0

    def test_min_over_no_children_is_nan_not_an_exception(self) -> None:
        class Overall(Criterion):
            def calculation(self) -> CriterionResult:
                rating = self.min_of_children()
                return CriterionResult(
                    channel=None, value=rating, rating=rating, color=None
                )

        report, (v1,) = report_of(Overall)
        report.calculate()
        assert report.overall(v1).result is not None
        assert np.isnan(report.overall(v1).result.rating)
        assert report.overall(v1).status == Status.OK

    def test_legacy_children_are_aggregated_too(self) -> None:
        """The helpers read `get_children()`, so they work before a report is migrated."""

        class Overall(Criterion):
            def __init__(self, report: Report[Any], isomme: Isomme) -> None:
                super().__init__(report, isomme)
                self.criterion_a = rated(4.0)(report, isomme)
                self.criterion_b = rated(2.0)(report, isomme)

            def calculation(self) -> CriterionResult:
                self.criterion_a.calculate()
                self.criterion_b.calculate()
                rating = self.min_of_children()
                return CriterionResult(
                    channel=None, value=rating, rating=rating, color=None
                )

        report, (v1,) = report_of(Overall)
        report.calculate()
        assert report.overall(v1).result is not None
        assert report.overall(v1).result.rating == 2.0


#: Declared once and referenced twice — by the ``Manual[...]`` annotation and by the
#: ``at=`` that reads it. That is the point: the wiring names the declaration, not a
#: string that has to match it.
P_DRIVER = manual("1", doc="Channel-code position of the driver.")
P_FRONT_PASSENGER = manual("3", doc="… of the front passenger.")


class Occupant(Criterion):
    """One occupant class serving every seat — what `p` threading used to prevent."""

    name = "Occupant"

    def calculation(self) -> CriterionResult:
        value = self.ctx.field("p")
        return CriterionResult(channel=None, value=value, rating=0.0, color=None)  # type: ignore[arg-type]


class Seated(Criterion):
    name = "Seated"
    p_driver: Manual[str, P_DRIVER]
    p_front_passenger: Manual[str, P_FRONT_PASSENGER]

    driver = sub(Occupant, at=from_input(P_DRIVER), name="Driver")
    front_passenger = sub(
        Occupant, at=from_input(P_FRONT_PASSENGER), name="Front Passenger"
    )
    trolley = sub(Occupant, at=where(p="M"), name="Trolley")

    def calculation(self) -> None:
        pass


class TestContext:
    def test_a_root_has_an_empty_context(self) -> None:
        class Overall(Criterion):
            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        ctx = report.overall(v1).ctx
        assert ctx.report is report
        assert ctx.isomme is v1
        assert dict(ctx.fields) == {}

    def test_from_input_reads_the_manual_input_of_the_nearest_ancestor(self) -> None:
        report, (v1,) = report_of(Seated)
        report.calculate()
        overall = report.overall(v1)
        assert overall.driver.result is not None
        assert overall.front_passenger.result is not None
        assert overall.driver.result.value == "1"
        assert overall.front_passenger.result.value == "3"

    def test_a_position_set_after_construction_is_honoured(self) -> None:
        """F15, properly: no rebuild_child(), no sync_positions()."""
        report, (v1,) = report_of(Seated)
        report.overall(v1).p_driver = "2"
        report.calculate()
        assert report.overall(v1).driver.result is not None
        assert report.overall(v1).driver.result.value == "2"

    def test_a_lettered_seat_is_a_position_like_any_other(self) -> None:
        """``?A…`` is a valid channel code — the reason a position is a `str`, not an `int`."""
        report, (v1,) = report_of(Seated)
        report.overall(v1).p_driver = "A"
        report.calculate()
        assert report.overall(v1).driver.result is not None
        assert report.overall(v1).driver.result.value == "A"
        assert (
            report.overall(v1).driver.code("?{p}HEAD??00??ACRA") == "?AHEAD??00??ACRA"
        )

    def test_children_inherit_the_context(self) -> None:
        class Leaf(Criterion):
            def calculation(self) -> CriterionResult:
                value = float(self.ctx.field("p"))
                return CriterionResult(
                    channel=None, value=value, rating=value, color=None
                )

        class Region(Criterion):
            leaf = sub(Leaf)

            def calculation(self) -> None:
                pass

        class Overall(Criterion):
            p_driver: Manual[str, P_DRIVER]
            driver = sub(Region, at=from_input(P_DRIVER))

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        report.overall(v1).p_driver = "4"
        report.calculate()
        assert report.overall(v1).driver.leaf.result is not None
        assert report.overall(v1).driver.leaf.result.value == 4.0

    def test_where_is_a_second_source_needing_no_framework_change(self) -> None:
        report, (v1,) = report_of(Seated)
        assert dict(report.overall(v1).trolley.ctx.fields) == {"p": "M"}

    def test_a_code_template_is_filled_from_the_context(self) -> None:
        report, (v1,) = report_of(Seated)
        assert (
            report.overall(v1).front_passenger.code("?{p}HEAD??00??ACRA")
            == "?3HEAD??00??ACRA"
        )

    def test_a_template_without_a_placeholder_passes_through(self) -> None:
        report, (v1,) = report_of(Seated)
        assert report.overall(v1).code("M?MBAR0OLC??VEX?") == "M?MBAR0OLC??VEX?"

    def test_a_missing_field_is_n_a_naming_it(self) -> None:
        class Leaf(Criterion):
            def calculation(self) -> CriterionResult:
                channel = self.require_channel(self.code("?{p}HEAD??00??ACRA"))
                return CriterionResult(
                    channel=channel, value=1.0, rating=1.0, color=None
                )

        class Overall(Criterion):
            leaf = sub(Leaf)

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        report.calculate()
        leaf = report.overall(v1).leaf
        assert leaf.status == Status.NA
        assert "p" in str(leaf.na_reason)
        assert leaf.result is None

    def test_a_missing_seat_input_is_n_a_not_a_silent_default(self) -> None:
        class Overall(Criterion):
            # Declares no position at all.
            driver = sub(Occupant, at=from_input(P_DRIVER))

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        report.calculate()
        assert report.overall(v1).driver.status == Status.NA
        assert "Channel-code position of the driver" in str(
            report.overall(v1).driver.na_reason
        )

    def test_from_input_still_accepts_a_name(self) -> None:
        """The string form is the escape hatch for a declaration in another module."""

        class Overall(Criterion):
            p_driver: Manual[str, P_DRIVER]
            driver = sub(Occupant, at=from_input("p_driver"))

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        report.overall(v1).p_driver = "5"
        report.calculate()
        assert report.overall(v1).driver.result is not None
        assert report.overall(v1).driver.result.value == "5"

    def test_a_declaration_is_an_identity_not_a_value(self) -> None:
        """
        Two declarations that read the same are still two declarations.

        Every report's driver position is ``manual("1", source="test report", …)``. If
        ``manual`` compared by value they would be interchangeable — and, worse,
        ``typing.Annotated`` caches ``Annotated[str, meta]`` on ``(type, meta)``, so the
        second report module to be imported would silently inherit the first one's
        annotation object and its ``at=`` would resolve to the wrong module's input.
        """
        twin = manual("1", doc="Channel-code position of the driver.")
        assert twin != P_DRIVER
        assert Manual[str, twin] is not Manual[str, P_DRIVER]

        class Overall(Criterion):
            p_driver: Manual[str, P_DRIVER]
            driver = sub(Occupant, at=from_input(twin))

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        report.calculate()
        assert report.overall(v1).driver.status == Status.NA

    def test_a_resolved_code_of_the_wrong_length_is_an_error(self) -> None:
        ctx = Ctx.__new__(Ctx)
        object.__setattr__(ctx, "report", None)
        object.__setattr__(ctx, "isomme", None)
        object.__setattr__(ctx, "fields", {"p": "12"})
        with pytest.raises(InvalidCodeError):
            ctx.code("?{p}HEAD??00??ACRA")

    def test_character_classes_count_as_one_character(self) -> None:
        report, (v1,) = report_of(Seated)
        assert (
            report.overall(v1).driver.code("?{p}CHST000[03]??DSX?")
            == "?1CHST000[03]??DSX?"
        )

    def test_at_derives_without_mutating(self) -> None:
        report, (v1,) = report_of(Seated)
        overall = report.overall(v1)
        derived = overall.ctx.at(p="1").at(object="M")
        assert dict(derived.fields) == {"p": "1", "object": "M"}
        assert dict(overall.ctx.fields) == {}

    def test_manual_input_api_is_unchanged(self) -> None:
        """Step 4's public API keeps working: the context source is not a second truth."""
        report, (v1,) = report_of(Seated)
        report.set_inputs({"T0": {"p_driver": "2", "p_front_passenger": "5"}})
        report.calculate()
        assert report.overall(v1).front_passenger.result is not None
        assert report.overall(v1).front_passenger.result.value == "5"
        assert report.get_inputs()["T0"]["p_driver"] == "2"

    def test_a_saved_int_position_is_refused(self) -> None:
        """
        Positions were ``int`` before they became the character the code actually is.

        A file saved before that is *rejected*, loudly, by the declaration's own type
        check — not quietly coerced. It says which input and what it expected, which is
        all a user needs to fix the file.
        """
        report, _ = report_of(Seated)
        with pytest.raises(TypeError) as caught:
            report.set_inputs({"T0": {"p_driver": 2}})
        assert "p_driver" in str(caught.value)
        assert "str" in str(caught.value)


# --------------------------------------------------------------------------- #
# no occupant anywhere
# --------------------------------------------------------------------------- #


class Vehicle(Criterion):
    """A vehicle-level criterion: a literal code, no position, no context at all."""

    name = "Door opening"
    source = "§4.4"
    role = Role.MODIFIER

    def calculation(self) -> CriterionResult:
        channel = self.require_channel(self.code("10SILELEOU00DSX0"))
        return CriterionResult(channel=channel, value=0.0, rating=0.0, color=None)


class Correlation(Criterion):
    """A correlation-style criterion: built from channels, no position anywhere."""

    name = "Curve correlation"

    def __init__(
        self,
        report: Report,
        isomme: Isomme,
        channel: Channel | None = None,
    ) -> None:
        super().__init__(report, isomme)
        self._channel = channel

    def calculation(self) -> CriterionResult:
        value = 1.0 if self._channel is not None else 0.0
        return CriterionResult(
            channel=self._channel, value=value, rating=value, color=None
        )


class Structural(Criterion):
    name = "Structural"
    max_rating = 0.0
    source = "§5"
    vehicle = sub(Vehicle)

    def calculation(self) -> CriterionResult:
        rating = self.modifiers_sum()
        return CriterionResult(channel=None, value=rating, rating=rating, color=None)


class TestNoOccupant:
    """`Ctx` is not an occupant object — constructing or calculating must never need one."""

    def test_a_vehicle_level_tree_builds_calculates_and_validates(self) -> None:
        report, (v1,) = report_of(Structural)
        report.calculate()
        overall = report.overall(v1)
        assert overall.status == Status.OK
        assert dict(overall.vehicle.ctx.fields) == {}
        assert [issue for issue in validate_tree(overall) if issue.is_error] == []
        # The empty Isomme carries no channel, so the modifier is n/a and its nan
        # propagates into the aggregate (G9) — nothing here ever asked for an occupant.
        assert overall.vehicle.status == Status.NA
        assert overall.result is not None
        assert np.isnan(overall.result.rating)

    def test_a_correlation_style_criterion_needs_no_context(self) -> None:
        class Overall(Criterion):
            def calculation(self) -> CriterionResult:
                rating = self.sum_of_children()
                return CriterionResult(
                    channel=None, value=rating, rating=rating, color=None
                )

        report, (v1,) = report_of(Overall)
        overall = report.overall(v1)
        channel = Channel("11HEAD0000THACXA", create_sample().data)
        overall.add_child("curve_1", Correlation(report, v1, channel))
        overall.add_child("curve_2", Correlation(report, v1, channel))
        report.calculate()
        assert overall.result is not None
        assert overall.result.rating == 2.0


def constant(value: float) -> Limit:
    return Limit(
        code_patterns=(), func=lambda x: value, name=f"Limit_{value:g}", rating=value
    )


class TestLimits:
    def test_define_limits_is_built_from_the_resolved_context(self) -> None:
        class Leaf(Criterion):
            name = "Leaf"

            def define_limits(self) -> list[Limit]:
                limit = constant(1.0)
                return [
                    replace(limit, code_patterns=(self.code("?{p}HEAD??00??ACRA"),))
                ]

            def calculation(self) -> None:
                pass

        class Overall(Criterion):
            p_driver: Manual[str, P_DRIVER]
            driver = sub(Leaf, at=from_input(P_DRIVER))

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        report.overall(v1).p_driver = "2"
        report.calculate()
        assert [
            limit.code_patterns for limit in report.overall(v1).driver.limits.limit_list
        ] == [("?2HEAD??00??ACRA",)]

    def test_recalculating_does_not_duplicate_limits(self) -> None:
        class Overall(Criterion):
            def define_limits(self) -> list[Limit]:
                return [constant(1.0)]

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        report.calculate().calculate()
        assert len(report.overall(v1).limits.limit_list) == 1
        assert len(report.limits[v1].limit_list) == 1

    def test_limits_reach_the_report_level_list(self) -> None:
        class Overall(Criterion):
            def define_limits(self) -> list[Limit]:
                return [constant(1.0), constant(2.0)]

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        report.calculate()
        assert len(report.limits[v1].limit_list) == 2

    def test_a_criterion_without_the_hook_keeps_its_hand_built_limits(self) -> None:
        """Coexistence: the 13 unmigrated reports build their rows in ``__init__``."""

        class Overall(Criterion):
            def __init__(self, report: Report[Any], isomme: Isomme) -> None:
                super().__init__(report, isomme)
                self.extend_limit_list([constant(1.0)])

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        report.calculate()
        assert len(report.overall(v1).limits.limit_list) == 1
        assert len(report.limits[v1].limit_list) == 1
