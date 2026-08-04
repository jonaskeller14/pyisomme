"""
The ``sub()`` + ``Ctx`` framework — plan step 7.

Framework only: no report is migrated in step 7, so everything here is built from
synthetic criteria and empty ``Isomme`` objects. That is deliberate — the point of the
step is that the machinery works *before* a protocol depends on it, and that it coexists
with the 13 reports still wired by hand.

The invariants under test, in the order the plan lists them:

* :class:`TestDeclarationOrder` — children come out in the order the protocol declares
  them, mixed with dynamically attached and not-yet-migrated ones.
* :class:`TestAutoCalculation` — declared children are calculated by the framework, and
  a not-yet-migrated parent's own children are *not* calculated twice.
* :class:`TestAggregation` — NaN propagates (G9), and modifiers stay out of the headline.
* :class:`TestContext` — the ``p`` threading, lazily resolved; a position set *after*
  construction is honoured (F15).
* :class:`TestNoOccupant` — a tree with no occupant anywhere in it builds, calculates and
  validates. ``Ctx`` is not an occupant object.
* :class:`TestLimits` — ``define_limits()`` rebuilds rows from the resolved context.
"""
from __future__ import annotations

import io
import logging
import unittest
from contextlib import redirect_stdout

import numpy as np

import pyisomme
from pyisomme.errors import InvalidCodeError, MissingData, Status
from pyisomme.limit import Limit
from pyisomme.report.criterion import Criterion, Role, sub
from pyisomme.report.ctx import Ctx, where
from pyisomme.report.manual import Manual, manual
from pyisomme.report.occupant import Seat, seat
from pyisomme.report.report import Report
from pyisomme.report.validate import validate_tree


logging.basicConfig(level=logging.CRITICAL)


def isomme(test_number: str = "T0") -> pyisomme.Isomme:
    return pyisomme.Isomme(test_number=test_number)


def report_of(overall: type[Criterion], n: int = 1) -> tuple[Report, list[pyisomme.Isomme]]:
    """A minimal report around ``overall``, with ``n`` empty tests."""
    made = type("MadeReport", (Report,), {"name": "made", "Criterion_Overall": overall})
    isomme_list = [isomme(f"T{i}") for i in range(n)]
    return made(isomme_list), isomme_list


class Rated(Criterion):
    """A leaf that reports whatever ``rating`` it was given, and counts its calls."""

    name = "Rated"
    calls: int = 0

    def calculation(self) -> None:
        self.calls += 1
        self.value = self.rating


def rated(value: float, role: Role = Role.RESULT, name: str = "Rated") -> type[Criterion]:
    return type("Rated_", (Rated,), {"name": name, "rating": value, "role": role})


# --------------------------------------------------------------------------- #
# declaration order
# --------------------------------------------------------------------------- #

class TestDeclarationOrder(unittest.TestCase):
    def test_declared_children_keep_protocol_order(self) -> None:
        """Not alphabetical: `zulu` is declared first and must come out first."""
        class Overall(Criterion):
            name = "Overall"
            zulu = sub(rated(1.))
            alpha = sub(rated(2.))
            mike = sub(rated(3.))

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        self.assertEqual([attr for attr, _ in report.overall(v1).get_children()],
                         ["zulu", "alpha", "mike"])

    def test_subclass_appends_and_overrides_without_touching_the_base(self) -> None:
        class Base(Criterion):
            first = sub(rated(1.))
            second = sub(rated(2.))

            def calculation(self) -> None:
                pass

        class Derived(Base):
            third = sub(rated(3.))
            second = sub(rated(9., name="Replaced"))

        report, (v1,) = report_of(Derived)
        children = dict(report.overall(v1).get_children())
        self.assertEqual(list(children), ["first", "second", "third"])
        self.assertEqual(children["second"].name, "Replaced")

        base_report, (v2,) = report_of(Base)
        self.assertEqual([attr for attr, _ in base_report.overall(v2).get_children()],
                         ["first", "second"])

    def test_declared_then_added_then_legacy(self) -> None:
        """Coexistence (D-5): all three wiring styles in one node, in that order."""
        class Overall(Criterion):
            declared = sub(rated(1.))

            def __init__(self, report: Report, isomme: pyisomme.Isomme) -> None:
                super().__init__(report, isomme)
                self.legacy_z = rated(2.)(report, isomme)
                self.legacy_a = rated(3.)(report, isomme)

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        overall = report.overall(v1)
        overall.add_child("added", rated(4.)(report, v1))
        self.assertEqual([attr for attr, _ in overall.get_children()],
                         ["declared", "added", "legacy_z", "legacy_a"])

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
        self.assertEqual([path for path, _ in report.overall(v1).walk()],
                         ["", "second", "second/zulu", "second/alpha", "first"])

    def test_print_results_follows_the_protocol_not_the_alphabet(self) -> None:
        class Overall(Criterion):
            name = "Overall"
            zulu = sub(rated(1., name="Zulu"))
            alpha = sub(rated(2., name="Alpha"))

            def calculation(self) -> None:
                pass

        report, _ = report_of(Overall)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            report.calculate().print_results()
        printed = [line.strip().split(":")[0] for line in buffer.getvalue().splitlines()[1:]]
        self.assertEqual(printed, ["Overall", "Zulu", "Alpha"])


# --------------------------------------------------------------------------- #
# automatic calculation
# --------------------------------------------------------------------------- #

class TestAutoCalculation(unittest.TestCase):
    def test_declared_children_are_calculated_by_the_framework(self) -> None:
        class Overall(Criterion):
            child = sub(rated(3.))

            def calculation(self) -> None:
                # No `self.child.calculate()` — that is the point.
                self.rating = self.child.rating

        report, (v1,) = report_of(Overall)
        report.calculate()
        self.assertEqual(report.overall(v1).child.calls, 1)
        self.assertEqual(report.overall(v1).child.status, Status.OK)
        self.assertEqual(report.overall(v1).rating, 3.)

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
        self.assertEqual(order, ["prepare", "child", "parent"])

    def test_grandchildren_are_calculated_too(self) -> None:
        class Branch(Criterion):
            leaf = sub(rated(2.))

            def calculation(self) -> None:
                self.rating = self.leaf.rating

        class Overall(Criterion):
            branch = sub(Branch)

            def calculation(self) -> None:
                self.rating = self.branch.rating

        report, (v1,) = report_of(Overall)
        report.calculate()
        self.assertEqual(report.overall(v1).rating, 2.)
        self.assertEqual(report.overall(v1).branch.leaf.calls, 1)

    def test_added_children_are_calculated(self) -> None:
        class Overall(Criterion):
            def calculation(self) -> None:
                self.rating = self.sum_of_children()

        report, (v1,) = report_of(Overall)
        overall = report.overall(v1)
        overall.add_child("one", rated(1.)(report, v1))
        overall.add_child("two", rated(2.)(report, v1))
        report.calculate()
        self.assertEqual(overall.rating, 3.)
        self.assertEqual([child.calls for _, child in overall.get_children()], [1, 1])

    def test_legacy_children_are_not_calculated_twice(self) -> None:
        """A not-yet-migrated parent calculates its own children; the framework must not."""
        class Overall(Criterion):
            def __init__(self, report: Report, isomme: pyisomme.Isomme) -> None:
                super().__init__(report, isomme)
                self.criterion_legacy = rated(1.)(report, isomme)

            def calculation(self) -> None:
                self.criterion_legacy.calculate()

        report, (v1,) = report_of(Overall)
        report.calculate()
        self.assertEqual(report.overall(v1).criterion_legacy.calls, 1)

    def test_a_failing_child_does_not_stop_its_siblings(self) -> None:
        class Broken(Criterion):
            def calculation(self) -> None:
                raise MissingData("?1HEAD??00??ACRA")

        class Overall(Criterion):
            broken = sub(Broken)
            fine = sub(rated(4.))

            def calculation(self) -> None:
                self.rating = self.fine.rating

        report, (v1,) = report_of(Overall)
        report.calculate()
        overall = report.overall(v1)
        self.assertEqual(overall.broken.status, Status.NA)
        self.assertEqual(overall.fine.status, Status.OK)
        self.assertEqual(overall.status, Status.OK)

    def test_add_child_sets_the_parent_link(self) -> None:
        class Overall(Criterion):
            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        overall = report.overall(v1)
        child = rated(1.)(report, v1)
        overall.add_child("child", child)
        self.assertIs(child.parent, overall)

    def test_sub_sets_the_parent_link(self) -> None:
        class Overall(Criterion):
            child = sub(rated(1.))

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        self.assertIs(report.overall(v1).child.parent, report.overall(v1))
        self.assertIsNone(report.overall(v1).parent)

    def test_the_tree_exists_before_calculate(self) -> None:
        """G8: eager construction — manual inputs are set between build and calculate."""
        class Leaf(Criterion):
            hard_contact: Manual[bool, manual(True, doc="…")]

            def calculation(self) -> None:
                self.rating = 1. if self.hard_contact else 0.

        class Overall(Criterion):
            leaf = sub(Leaf)

            def calculation(self) -> None:
                self.rating = self.leaf.rating

        report, (v1,) = report_of(Overall)
        report.overall(v1).leaf.hard_contact = False
        report.calculate()
        self.assertEqual(report.overall(v1).rating, 0.)


# --------------------------------------------------------------------------- #
# aggregation
# --------------------------------------------------------------------------- #

class Mixed(Criterion):
    """Two results and a modifier — the "min over results plus sum over modifiers" box."""

    name = "Mixed"
    good = sub(rated(4., name="Good"))
    bad = sub(rated(2., name="Bad"))
    penalty = sub(rated(-1., Role.MODIFIER, name="Penalty"))

    def calculation(self) -> None:
        self.rating = self.min_of_children() + self.modifiers_sum()


class TestAggregation(unittest.TestCase):
    def test_modifiers_are_excluded_from_the_headline(self) -> None:
        report, (v1,) = report_of(Mixed)
        report.calculate()
        overall = report.overall(v1)
        self.assertEqual(overall.min_of_children(), 2.)
        self.assertEqual(overall.sum_of_children(), 6.)
        self.assertEqual(overall.modifiers_sum(), -1.)
        self.assertEqual(overall.rating, 1.)

    def test_aggregate_children_count_towards_the_headline(self) -> None:
        class Overall(Criterion):
            leaf = sub(rated(4.))
            branch = sub(rated(1., Role.AGGREGATE))
            penalty = sub(rated(-2., Role.MODIFIER))

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        self.assertEqual(sorted(report.overall(v1).ratings_of_children()), [1., 4.])
        self.assertEqual(report.overall(v1).ratings_of_children(Role.MODIFIER), [-2.])

    def test_explicit_roles_select_exactly_those(self) -> None:
        report, (v1,) = report_of(Mixed)
        overall = report.overall(v1)
        self.assertEqual([c.name for c in overall.children_by_role(Role.RESULT)], ["Good", "Bad"])
        self.assertEqual([c.name for c in overall.children_by_role(Role.MODIFIER)], ["Penalty"])
        self.assertEqual(len(overall.children_by_role(Role.RESULT, Role.MODIFIER)), 3)

    def test_nan_propagates_through_every_helper(self) -> None:
        """G9: a missing measurement must never look like a good score."""
        class Overall(Criterion):
            fine = sub(rated(4.))
            missing = sub(rated(np.nan))

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        overall = report.overall(v1)
        self.assertTrue(np.isnan(overall.min_of_children()))
        self.assertTrue(np.isnan(overall.max_of_children()))
        self.assertTrue(np.isnan(overall.sum_of_children()))
        self.assertTrue(np.isnan(overall.mean_of_children()))

    def test_a_nan_tolerant_mean_needs_a_reason_and_records_it(self) -> None:
        class Overall(Criterion):
            fine = sub(rated(4.))
            missing = sub(rated(np.nan))

            def calculation(self) -> None:
                self.rating = self.mean_of_children(skip_missing="no rear occupant in this test")

        report, (v1,) = report_of(Overall)
        report.calculate()
        overall = report.overall(v1)
        self.assertEqual(overall.rating, 4.)
        self.assertEqual(overall.skip_missing, "no rear occupant in this test")

    def test_skip_missing_stays_unset_when_nothing_was_skipped(self) -> None:
        class Overall(Criterion):
            one = sub(rated(4.))
            two = sub(rated(2.))

            def calculation(self) -> None:
                self.rating = self.mean_of_children(skip_missing="would be a lie")

        report, (v1,) = report_of(Overall)
        report.calculate()
        self.assertEqual(report.overall(v1).rating, 3.)
        self.assertIsNone(report.overall(v1).skip_missing)

    def test_all_missing_stays_nan_even_when_tolerated(self) -> None:
        class Overall(Criterion):
            one = sub(rated(np.nan))

            def calculation(self) -> None:
                self.rating = self.mean_of_children(skip_missing="whatever")

        report, (v1,) = report_of(Overall)
        report.calculate()
        self.assertTrue(np.isnan(report.overall(v1).rating))

    def test_modifiers_sum_is_zero_without_modifiers(self) -> None:
        class Overall(Criterion):
            leaf = sub(rated(4.))

            def calculation(self) -> None:
                self.rating = self.min_of_children() + self.modifiers_sum()

        report, (v1,) = report_of(Overall)
        report.calculate()
        self.assertEqual(report.overall(v1).rating, 4.)

    def test_min_over_no_children_is_nan_not_an_exception(self) -> None:
        class Overall(Criterion):
            def calculation(self) -> None:
                self.rating = self.min_of_children()

        report, (v1,) = report_of(Overall)
        report.calculate()
        self.assertTrue(np.isnan(report.overall(v1).rating))
        self.assertEqual(report.overall(v1).status, Status.OK)

    def test_legacy_children_are_aggregated_too(self) -> None:
        """The helpers read `get_children()`, so they work before a report is migrated."""
        class Overall(Criterion):
            def __init__(self, report: Report, isomme: pyisomme.Isomme) -> None:
                super().__init__(report, isomme)
                self.criterion_a = rated(4.)(report, isomme)
                self.criterion_b = rated(2.)(report, isomme)

            def calculation(self) -> None:
                self.criterion_a.calculate()
                self.criterion_b.calculate()
                self.rating = self.min_of_children()

        report, (v1,) = report_of(Overall)
        report.calculate()
        self.assertEqual(report.overall(v1).rating, 2.)


# --------------------------------------------------------------------------- #
# context
# --------------------------------------------------------------------------- #

class Occupant(Criterion):
    """One occupant class serving every seat — what `p` threading used to prevent."""

    name = "Occupant"

    def calculation(self) -> None:
        self.value = float(self.ctx.field("p"))
        self.rating = self.value


class Seated(Criterion):
    name = "Seated"
    p_driver: Manual[int, manual(1, doc="Channel-code position of the driver.")]
    p_front_passenger: Manual[int, manual(3, doc="… of the front passenger.")]

    driver = sub(Occupant, at=seat(Seat.DRIVER), name="Driver")
    front_passenger = sub(Occupant, at=seat(Seat.FRONT_PASSENGER), name="Front Passenger")
    trolley = sub(Occupant, at=where(p="M"), name="Trolley")

    def calculation(self) -> None:
        pass


class TestContext(unittest.TestCase):
    def test_a_root_has_an_empty_context(self) -> None:
        class Overall(Criterion):
            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        ctx = report.overall(v1).ctx
        self.assertIs(ctx.report, report)
        self.assertIs(ctx.isomme, v1)
        self.assertEqual(dict(ctx.fields), {})

    def test_seat_reads_the_manual_input_of_the_nearest_ancestor(self) -> None:
        report, (v1,) = report_of(Seated)
        report.calculate()
        overall = report.overall(v1)
        self.assertEqual(overall.driver.value, 1.)
        self.assertEqual(overall.front_passenger.value, 3.)

    def test_a_position_set_after_construction_is_honoured(self) -> None:
        """F15, properly: no rebuild_child(), no sync_positions()."""
        report, (v1,) = report_of(Seated)
        report.overall(v1).p_driver = 2
        report.calculate()
        self.assertEqual(report.overall(v1).driver.value, 2.)

    def test_children_inherit_the_context(self) -> None:
        class Leaf(Criterion):
            def calculation(self) -> None:
                self.value = float(self.ctx.field("p"))

        class Region(Criterion):
            leaf = sub(Leaf)

            def calculation(self) -> None:
                pass

        class Overall(Criterion):
            p_driver: Manual[int, manual(1, doc="…")]
            driver = sub(Region, at=seat(Seat.DRIVER))

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        report.overall(v1).p_driver = 4
        report.calculate()
        self.assertEqual(report.overall(v1).driver.leaf.value, 4.)

    def test_where_is_a_second_source_needing_no_framework_change(self) -> None:
        report, (v1,) = report_of(Seated)
        self.assertEqual(dict(report.overall(v1).trolley.ctx.fields), {"p": "M"})

    def test_a_code_template_is_filled_from_the_context(self) -> None:
        report, (v1,) = report_of(Seated)
        self.assertEqual(report.overall(v1).front_passenger.code("?{p}HEAD??00??ACRA"),
                         "?3HEAD??00??ACRA")

    def test_a_template_without_a_placeholder_passes_through(self) -> None:
        report, (v1,) = report_of(Seated)
        self.assertEqual(report.overall(v1).code("M?MBAR0OLC??VEX?"), "M?MBAR0OLC??VEX?")

    def test_a_missing_field_is_n_a_naming_it(self) -> None:
        class Leaf(Criterion):
            def calculation(self) -> None:
                self.channel = self.require_channel(self.code("?{p}HEAD??00??ACRA"))
                self.value = 1.

        class Overall(Criterion):
            leaf = sub(Leaf)

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        report.calculate()
        leaf = report.overall(v1).leaf
        self.assertEqual(leaf.status, Status.NA)
        self.assertIn("p", str(leaf.na_reason))
        self.assertTrue(np.isnan(leaf.value))

    def test_a_missing_seat_input_is_n_a_not_a_silent_default(self) -> None:
        class Overall(Criterion):
            # Declares no p_driver at all.
            driver = sub(Occupant, at=seat(Seat.DRIVER))

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        report.calculate()
        self.assertEqual(report.overall(v1).driver.status, Status.NA)
        self.assertIn("p_driver", str(report.overall(v1).driver.na_reason))

    def test_a_resolved_code_of_the_wrong_length_is_an_error(self) -> None:
        ctx = Ctx.__new__(Ctx)
        object.__setattr__(ctx, "report", None)
        object.__setattr__(ctx, "isomme", None)
        object.__setattr__(ctx, "fields", {"p": 12})
        with self.assertRaises(InvalidCodeError):
            ctx.code("?{p}HEAD??00??ACRA")

    def test_character_classes_count_as_one_character(self) -> None:
        report, (v1,) = report_of(Seated)
        self.assertEqual(report.overall(v1).driver.code("?{p}CHST000[03]??DSX?"),
                         "?1CHST000[03]??DSX?")

    def test_at_derives_without_mutating(self) -> None:
        report, (v1,) = report_of(Seated)
        overall = report.overall(v1)
        derived = overall.ctx.at(p=1).at(object="M")
        self.assertEqual(dict(derived.fields), {"p": 1, "object": "M"})
        self.assertEqual(dict(overall.ctx.fields), {})

    def test_manual_input_api_is_unchanged(self) -> None:
        """Step 4's public API keeps working: the seat source is not a second truth."""
        report, (v1,) = report_of(Seated)
        report.set_inputs({"T0": {"p_driver": 2, "p_front_passenger": 5}})
        report.calculate()
        self.assertEqual(report.overall(v1).front_passenger.value, 5.)
        self.assertEqual(report.get_inputs()["T0"]["p_driver"], 2)


# --------------------------------------------------------------------------- #
# no occupant anywhere
# --------------------------------------------------------------------------- #

class Vehicle(Criterion):
    """A vehicle-level criterion: a literal code, no position, no context at all."""

    name = "Door opening"
    source = "§4.4"
    role = Role.MODIFIER

    def calculation(self) -> None:
        self.channel = self.require_channel(self.code("10SILELEOU00DSX0"))
        self.rating = 0.


class Correlation(Criterion):
    """A correlation-style criterion: built from channels, no position anywhere."""

    name = "Curve correlation"

    def __init__(self, report: Report, isomme: pyisomme.Isomme,
                 channel: pyisomme.Channel | None = None) -> None:
        super().__init__(report, isomme)
        self._channel = channel

    def calculation(self) -> None:
        self.value = 1. if self._channel is not None else 0.
        self.rating = self.value


class Structural(Criterion):
    name = "Structural"
    max_rating = 0.
    source = "§5"
    vehicle = sub(Vehicle)

    def calculation(self) -> None:
        self.rating = self.modifiers_sum()


class TestNoOccupant(unittest.TestCase):
    """`Ctx` is not an occupant object — constructing or calculating must never need one."""

    def test_a_vehicle_level_tree_builds_calculates_and_validates(self) -> None:
        report, (v1,) = report_of(Structural)
        report.calculate()
        overall = report.overall(v1)
        self.assertEqual(overall.status, Status.OK)
        self.assertEqual(dict(overall.vehicle.ctx.fields), {})
        self.assertEqual([issue for issue in validate_tree(overall) if issue.is_error], [])
        # The empty Isomme carries no channel, so the modifier is n/a and its nan
        # propagates into the aggregate (G9) — nothing here ever asked for an occupant.
        self.assertEqual(overall.vehicle.status, Status.NA)
        self.assertTrue(np.isnan(overall.rating))

    def test_a_correlation_style_criterion_needs_no_context(self) -> None:
        class Overall(Criterion):
            def calculation(self) -> None:
                self.rating = self.sum_of_children()

        report, (v1,) = report_of(Overall)
        overall = report.overall(v1)
        channel = pyisomme.Channel("11HEAD0000THACXA", pyisomme.create_sample().data)
        overall.add_child("curve_1", Correlation(report, v1, channel))
        overall.add_child("curve_2", Correlation(report, v1, channel))
        report.calculate()
        self.assertEqual(overall.rating, 2.)


# --------------------------------------------------------------------------- #
# limits
# --------------------------------------------------------------------------- #

def constant(value: float) -> Limit:
    return Limit(code_patterns=[], func=lambda x: value, name=f"Limit_{value:g}", rating=value)


class TestLimits(unittest.TestCase):
    def test_define_limits_is_built_from_the_resolved_context(self) -> None:
        class Leaf(Criterion):
            name = "Leaf"

            def define_limits(self) -> list[Limit]:
                limit = constant(1.)
                limit.code_patterns = [self.code("?{p}HEAD??00??ACRA")]
                return [limit]

            def calculation(self) -> None:
                pass

        class Overall(Criterion):
            p_driver: Manual[int, manual(1, doc="…")]
            driver = sub(Leaf, at=seat(Seat.DRIVER))

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        report.overall(v1).p_driver = 2
        report.calculate()
        self.assertEqual([limit.code_patterns for limit in report.overall(v1).driver.limits.limit_list],
                         [["?2HEAD??00??ACRA"]])

    def test_recalculating_does_not_duplicate_limits(self) -> None:
        class Overall(Criterion):
            def define_limits(self) -> list[Limit]:
                return [constant(1.)]

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        report.calculate().calculate()
        self.assertEqual(len(report.overall(v1).limits.limit_list), 1)
        self.assertEqual(len(report.limits[v1].limit_list), 1)

    def test_limits_reach_the_report_level_list(self) -> None:
        class Overall(Criterion):
            def define_limits(self) -> list[Limit]:
                return [constant(1.), constant(2.)]

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        report.calculate()
        self.assertEqual(len(report.limits[v1].limit_list), 2)

    def test_a_criterion_without_the_hook_keeps_its_hand_built_limits(self) -> None:
        """Coexistence: the 13 unmigrated reports build their rows in ``__init__``."""
        class Overall(Criterion):
            def __init__(self, report: Report, isomme: pyisomme.Isomme) -> None:
                super().__init__(report, isomme)
                self.extend_limit_list([constant(1.)])

            def calculation(self) -> None:
                pass

        report, (v1,) = report_of(Overall)
        report.calculate()
        self.assertEqual(len(report.overall(v1).limits.limit_list), 1)
        self.assertEqual(len(report.limits[v1].limit_list), 1)


if __name__ == "__main__":
    unittest.main()
