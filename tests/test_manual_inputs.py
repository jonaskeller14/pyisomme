"""
Manual inputs as a declared concept (refactor plan step 4, review proposal P11).

Needs **no fixture data** — every report here is built from empty ``Isomme``
objects, like ``tests/test_describe.py`` — so it runs in CI alongside the lint
job.

Covers the four things the declaration buys:

* the ``manual(...)`` default reaches the instance as a plain attribute (so
  nothing that reads ``self.hard_contact`` had to change);
* a typo'd assignment fails **at the assignment**, with a suggestion (F13);
* a wrongly typed assignment is refused;
* inputs are enumerable, JSON round-trippable and replayable (F14),

plus the F15 fix: a seating position set *after* construction now moves the criteria,
not only the plots.
"""
from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout

import pyisomme
from pyisomme.report.criterion import Criterion
from pyisomme.report.euro_ncap.frontal_50kmh import EuroNCAP_Frontal_50kmh
from pyisomme.report.euro_ncap.frontal_mpdb import EuroNCAP_Frontal_MPDB
from pyisomme.report.manual import Manual, declared_inputs, manual, settable_names
from pyisomme.report.report import Report


def build(report_class=EuroNCAP_Frontal_50kmh, n: int = 1):
    isomme_list = [pyisomme.Isomme(test_number=f"T{i}") for i in range(n)]
    return report_class(isomme_list), isomme_list


def position(criterion: Criterion) -> str:
    """
    The seating position a criterion actually assesses.

    Step 8 replaced the ``p`` threaded through every constructor with the lazily
    resolved context, so this — not ``criterion.p`` — is what says which occupant a
    criterion is looking at. A ``str``, because a position is one character of the
    channel code and the lettered seats (``?A…``) are positions too.
    """
    return str(criterion.ctx.field("p"))


class TestDeclaration(unittest.TestCase):
    def test_default_is_installed_as_a_plain_attribute(self) -> None:
        """``Manual[bool, manual(True)]`` needs no ``= True``; reads still work."""
        report, (v1,) = build()
        head = report.overall(v1).criterion_driver.criterion_head
        self.assertIs(head.hard_contact, True)
        self.assertIs(type(head).hard_contact, True)

    def test_spec_carries_metadata(self) -> None:
        report, (v1,) = build()
        column = report.overall(v1).criterion_driver.criterion_head.criterion_DisplacementSteeringColumn
        spec = column.get_input_specs()["displacement_steering_column_rearwards"]
        self.assertEqual(spec.type, float)
        self.assertEqual(spec.default, 0.0)
        self.assertEqual(spec.unit, "mm")
        self.assertEqual(spec.source, "measurement")
        self.assertIn("Rearward", spec.doc or "")

    def test_declaration_is_inherited(self) -> None:
        """The rear passenger reuses the driver's Submarining class."""
        report, (v1,) = build()
        submarining = report.overall(v1).criterion_rear_passenger.criterion_femur.criterion_submarining
        self.assertIn("submarining", submarining.get_input_specs())

    def test_undeclared_class_attributes_are_not_inputs(self) -> None:
        """Only ``Manual[...]`` counts — plain class attributes stay invisible."""
        report, (v1,) = build()
        self.assertNotIn("name", report.overall(v1).get_input_specs())
        self.assertNotIn("value", report.overall(v1).get_input_specs())


class TestSetattrGuard(unittest.TestCase):
    def test_typo_raises_with_a_suggestion(self) -> None:
        report, (v1,) = build()
        head = report.overall(v1).criterion_driver.criterion_head
        with self.assertRaises(AttributeError) as caught:
            head.hard_contct = False
        message = str(caught.exception)
        self.assertIn("hard_contct", message)
        self.assertIn("hard_contact", message)

    def test_unrelated_typo_raises_without_a_suggestion(self) -> None:
        report, (v1,) = build()
        with self.assertRaises(AttributeError):
            report.overall(v1).completely_unrelated_name = 1

    def test_wrong_type_is_refused(self) -> None:
        report, (v1,) = build()
        submarining = report.overall(v1).criterion_driver.criterion_femur.criterion_submarining
        with self.assertRaises(TypeError):
            submarining.submarining = "yes"
        self.assertIs(submarining.submarining, False)

    def test_bool_is_not_a_number(self) -> None:
        """``isinstance(True, int)`` must not wave through a boolean for a float input."""
        report, (v1,) = build()
        column = report.overall(v1).criterion_driver.criterion_head.criterion_DisplacementSteeringColumn
        with self.assertRaises(TypeError):
            column.displacement_steering_column_rearwards = True

    def test_int_is_accepted_for_a_float_input(self) -> None:
        report, (v1,) = build()
        column = report.overall(v1).criterion_driver.criterion_head.criterion_DisplacementSteeringColumn
        column.displacement_steering_column_rearwards = 38
        self.assertEqual(column.displacement_steering_column_rearwards, 38)

    def test_valid_assignment_passes(self) -> None:
        report, (v1,) = build()
        head = report.overall(v1).criterion_driver.criterion_head
        head.hard_contact = False
        self.assertIs(head.hard_contact, False)

    def test_framework_fields_stay_assignable(self) -> None:
        report, (v1,) = build()
        overall = report.overall(v1)
        overall.value = 1.0
        overall.rating = 2.0
        overall.color = "green"
        self.assertEqual((overall.value, overall.rating, overall.color), (1.0, 2.0, "green"))

    def test_private_names_are_exempt(self) -> None:
        report, (v1,) = build()
        report.overall(v1)._scratch = 1
        self.assertEqual(report.overall(v1)._scratch, 1)

    def test_subcriteria_are_exempt(self) -> None:
        """Children are attached dynamically in ``__init__`` under names nobody declares."""
        report, (v1,) = build()
        overall = report.overall(v1)
        overall.criterion_freshly_attached = overall.criterion_driver
        self.assertIn("criterion_freshly_attached", dict(overall.get_children()))


class TestEnumeration(unittest.TestCase):
    def test_every_report_exposes_its_inputs(self) -> None:
        report, (v1,) = build()
        inputs = report.get_inputs()
        self.assertEqual(list(inputs), ["T0"])
        self.assertIn("criterion_driver/criterion_head/hard_contact", inputs["T0"])
        self.assertIn("p_driver", inputs["T0"])

    def test_print_inputs_marks_deviations(self) -> None:
        report, (v1,) = build()
        report.overall(v1).criterion_driver.criterion_femur.criterion_submarining.submarining = True

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            report.print_inputs()
        lines = [line for line in buffer.getvalue().splitlines() if "submarining" in line]

        self.assertEqual(len(lines), 2, buffer.getvalue())  # driver (changed) + rear (default)
        self.assertEqual(len([line for line in lines if line.lstrip().startswith("*")]), 1)

    def test_round_trip_is_a_no_op(self) -> None:
        report, (v1,) = build()
        before = report.get_inputs()
        report.set_inputs(before)
        self.assertEqual(before, report.get_inputs())

    def test_json_round_trip_reproduces_a_run(self) -> None:
        report_a, (a1,) = build()
        report_a.overall(a1).criterion_driver.criterion_femur.criterion_submarining.submarining = True
        report_a.overall(a1).criterion_door_opening_during_impact.number_of_door_openings_during_impact = 2
        stored = json.loads(json.dumps(report_a.get_inputs()))

        report_b, (b1,) = build()
        report_b.set_inputs(stored)

        self.assertIs(report_b.overall(b1).criterion_driver.criterion_femur.criterion_submarining.submarining, True)
        self.assertEqual(
            report_b.overall(b1).criterion_door_opening_during_impact.number_of_door_openings_during_impact, 2)
        self.assertEqual(report_a.get_inputs(), report_b.get_inputs())

        report_a.calculate()
        report_b.calculate()
        self.assertEqual(report_a.overall(a1).criterion_door_opening_during_impact.rating,
                         report_b.overall(b1).criterion_door_opening_during_impact.rating)

    def test_unknown_test_is_refused(self) -> None:
        report, _ = build()
        with self.assertRaises(KeyError):
            report.set_inputs({"nope": {}})

    def test_unknown_path_is_refused(self) -> None:
        report, _ = build()
        with self.assertRaises(KeyError):
            report.set_inputs({"T0": {"criterion_driver/criterion_head/hard_contct": False}})

    def test_wrong_type_from_json_is_refused(self) -> None:
        report, _ = build()
        with self.assertRaises(TypeError):
            report.set_inputs({"T0": {"criterion_driver/criterion_head/hard_contact": "yes"}})


class TestPositionSyncF15(unittest.TestCase):
    """
    A seating position set after construction must move the criteria, not only the plots.

    The behaviour under test is unchanged since step 4; the mechanism is gone. Every
    report is migrated as of step 9, so nothing rebuilds anything any more — the context
    is resolved at the start of ``calculate()`` and the same subtree simply reads a
    different position. The ``rebuild`` in the method names below is kept because these
    are the step-4 regression tests and the names are what a failure will be looked up
    by; read it as "a position change that used to need a rebuild".
    """

    def test_position_set_after_construction_reaches_the_criteria(self) -> None:
        report, (v1,) = build()
        overall = report.overall(v1)
        self.assertEqual(position(overall.criterion_driver), "1")

        overall.p_driver = "3"
        report.calculate()

        self.assertEqual(position(overall.criterion_driver), "3")
        self.assertEqual(position(overall.criterion_driver.criterion_head.criterion_hic_15), "3")
        # ...and the derived positions follow the right-hand-drive rule.
        self.assertEqual(overall.p_front_passenger, "1")
        self.assertEqual(position(overall.criterion_front_passenger), "1")

    def test_rebuilt_limits_follow_the_new_position(self) -> None:
        report, (v1,) = build()
        overall = report.overall(v1)
        overall.p_driver = "3"
        report.calculate()

        patterns = overall.criterion_driver.criterion_head.criterion_hic_15.limits.limit_list[0].code_patterns
        self.assertTrue(all(pattern[1] == "3" for pattern in patterns), patterns)

    def test_rebuild_preserves_manual_inputs(self) -> None:
        report, (v1,) = build()
        overall = report.overall(v1)
        overall.criterion_driver.criterion_femur.criterion_submarining.submarining = True
        overall.criterion_driver.steering_wheel_airbag_exists = False

        overall.p_driver = "3"
        report.calculate()

        self.assertIs(overall.criterion_driver.criterion_femur.criterion_submarining.submarining, True)
        self.assertIs(overall.criterion_driver.steering_wheel_airbag_exists, False)

    def test_rebuild_does_not_leave_stale_report_limits(self) -> None:
        report, (v1,) = build()
        before = len(report.limits[v1].limit_list)

        report.overall(v1).p_driver = "3"
        report.calculate()

        self.assertEqual(len(report.limits[v1].limit_list), before)

    def test_unchanged_position_rebuilds_nothing(self) -> None:
        report, (v1,) = build()
        driver = report.overall(v1).criterion_driver
        report.calculate()
        self.assertIs(report.overall(v1).criterion_driver, driver)

    def test_mpdb_syncs_too(self) -> None:
        report, (v1,) = build(EuroNCAP_Frontal_MPDB)
        overall = report.overall(v1)
        overall.p_driver = "3"
        report.calculate()
        self.assertEqual(position(overall.criterion_driver), "3")
        self.assertEqual(position(overall.criterion_passenger), "1")


class TestDerivedVsUserSetPositions(unittest.TestCase):
    """A derivation fills what the user left alone — it never overwrites a set input."""

    def test_explicit_passenger_position_survives_the_derivation(self) -> None:
        report, (v1,) = build()
        overall = report.overall(v1)

        overall.p_driver = "3"            # right-hand drive: would derive 1 / 4
        overall.p_front_passenger = "5"   # ...but this test seated it centrally
        report.calculate()

        self.assertEqual(overall.p_front_passenger, "5")
        self.assertEqual(position(overall.criterion_front_passenger), "5")
        self.assertEqual(overall.p_rear_passenger, "4")   # untouched -> still derived

    def test_explicit_value_equal_to_the_default_still_wins(self) -> None:
        """The case ``value != default`` cannot see: set explicitly *to* the default."""
        report, (v1,) = build()
        overall = report.overall(v1)

        overall.p_driver = "3"
        overall.p_front_passenger = "3"   # the declared default, meant literally
        report.calculate()

        self.assertEqual(overall.p_front_passenger, "3")
        self.assertEqual(position(overall.criterion_front_passenger), "3")

    def test_derivation_is_idempotent_across_recalculation(self) -> None:
        """A derived value must follow ``p_driver`` back, not stick at the old one."""
        report, (v1,) = build()
        overall = report.overall(v1)

        overall.p_driver = "3"
        report.calculate()
        self.assertEqual(overall.p_front_passenger, "1")

        overall.p_driver = "1"
        report.calculate()
        self.assertEqual(overall.p_front_passenger, "3")
        self.assertEqual(position(overall.criterion_front_passenger), "3")

    def test_set_inputs_counts_as_user_set(self) -> None:
        """A replayed input file pins the positions it recorded."""
        report, (v1,) = build()
        report.set_inputs({"T0": {"p_driver": "3", "p_front_passenger": "5"}})
        report.calculate()

        self.assertEqual(position(report.overall(v1).criterion_front_passenger), "5")

    def test_a_rebuilt_subtree_keeps_derived_values_derived(self) -> None:
        """A value the report derived must not be frozen by a rebuild (MPDB nests one)."""
        report, (v1,) = build()
        overall = report.overall(v1)

        overall.p_driver = "3"
        report.calculate()
        self.assertFalse(overall.input_is_set("p_front_passenger"))

        overall.p_driver = "1"
        report.calculate()
        self.assertEqual(position(overall.criterion_front_passenger), "3")

    def test_input_is_set_reports_the_source(self) -> None:
        report, (v1,) = build()
        overall = report.overall(v1)

        self.assertFalse(overall.input_is_set("p_driver"))
        self.assertFalse(overall.input_is_set("p_front_passenger"))

        overall.p_front_passenger = "5"
        self.assertTrue(overall.input_is_set("p_front_passenger"))

    def test_set_derived_input_rejects_an_undeclared_name(self) -> None:
        report, (v1,) = build()
        with self.assertRaises(AttributeError):
            report.overall(v1).set_derived_input("p_drivr", 3)

    def test_print_inputs_distinguishes_derived_from_user_set(self) -> None:
        report, (v1,) = build()
        report.overall(v1).p_driver = "3"   # derives p_front_passenger = 1
        report.calculate()

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            report.print_inputs()
        # "\t{marker} {path}: {value} ..."
        markers = {line[3:].split(":")[0]: line[1]
                   for line in buffer.getvalue().splitlines() if line.startswith("\t")}

        self.assertEqual(markers["p_driver"], "*")
        self.assertEqual(markers["p_front_passenger"], "~")
        self.assertEqual(markers["criterion_driver/criterion_head/hard_contact"], " ")


class TestFrameworkInternals(unittest.TestCase):
    def test_settable_names_include_annotations_and_attributes(self) -> None:
        names = settable_names(EuroNCAP_Frontal_50kmh.Criterion_Overall)
        self.assertIn("value", names)       # annotated on Criterion, never assigned there
        self.assertIn("name", names)        # plain class attribute
        self.assertIn("p_driver", names)    # manual input, declared without a value

    def test_declared_inputs_is_cached(self) -> None:
        cls = EuroNCAP_Frontal_50kmh.Criterion_Overall
        self.assertIs(declared_inputs(cls), declared_inputs(cls))

    def test_a_locally_declared_input_works_end_to_end(self) -> None:
        """The declaration idiom must work outside the report modules too."""

        class Local(Criterion):
            name = "Local"
            flag: Manual[bool, manual(False, doc="a locally declared input")]

            def calculation(self) -> None:
                self.value = 1.0 if self.flag else 0.0

        isomme = pyisomme.Isomme(test_number="T0")
        criterion = Local(Report([isomme]), isomme)

        self.assertIs(criterion.flag, False)
        criterion.calculate()
        self.assertEqual(criterion.value, 0.0)

        criterion.flag = True
        criterion.calculate()
        self.assertEqual(criterion.value, 1.0)

        with self.assertRaises(AttributeError):
            criterion.flg = True


if __name__ == "__main__":
    unittest.main()
