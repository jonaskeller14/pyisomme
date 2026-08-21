from __future__ import annotations

import io
import json
from contextlib import redirect_stdout

import pytest

import pyisomme
from pyisomme.report.criterion import Criterion
from pyisomme.report.euro_ncap.frontal_50kmh import EuroNCAP_Frontal_50kmh
from pyisomme.report.euro_ncap.frontal_mpdb import EuroNCAP_Frontal_MPDB
from pyisomme.report.manual import Manual, declared_inputs, manual, settable_names
from pyisomme.report.report import Report


@pytest.fixture
def v1() -> pyisomme.Isomme:
    return pyisomme.Isomme(test_number="T0")


@pytest.fixture
def report_50kmh(v1: pyisomme.Isomme) -> Report:
    return EuroNCAP_Frontal_50kmh([v1])


@pytest.fixture
def report_mpdb(v1: pyisomme.Isomme) -> Report:
    return EuroNCAP_Frontal_MPDB([v1])


def position(criterion: Criterion) -> str:
    return str(criterion.ctx.field("p"))


class TestDeclaration:
    def test_default_is_installed_as_a_plain_attribute(self, report_50kmh, v1) -> None:
        """``Manual[bool, manual(True)]`` needs no ``= True``; reads still work."""
        head = report_50kmh.overall(v1).criterion_driver.criterion_head
        assert head.hard_contact is True
        assert type(head).hard_contact is True

    def test_spec_carries_metadata(self, report_50kmh, v1) -> None:
        column = report_50kmh.overall(
            v1
        ).criterion_driver.criterion_head.criterion_DisplacementSteeringColumn
        spec = column.get_input_specs()["displacement_steering_column_rearwards"]
        assert spec.type is float
        assert spec.default == 0.0
        assert spec.unit == "mm"
        assert spec.source == "measurement"
        assert "Rearward" in (spec.doc or "")

    def test_declaration_is_inherited(self, report_50kmh, v1) -> None:
        """The rear passenger reuses the driver's Submarining class."""
        submarining = report_50kmh.overall(
            v1
        ).criterion_rear_passenger.criterion_femur.criterion_submarining
        assert "submarining" in submarining.get_input_specs()

    def test_undeclared_class_attributes_are_not_inputs(self, report_50kmh, v1) -> None:
        """Only ``Manual[...]`` counts — plain class attributes stay invisible."""
        assert "name" not in report_50kmh.overall(v1).get_input_specs()
        assert "value" not in report_50kmh.overall(v1).get_input_specs()


class TestSetattrGuard:
    def test_typo_raises_with_a_suggestion(self, report_50kmh, v1) -> None:
        head = report_50kmh.overall(v1).criterion_driver.criterion_head
        with pytest.raises(AttributeError) as caught:
            head.hard_contct = False
        message = str(caught.value)
        assert "hard_contct" in message
        assert "hard_contact" in message

    def test_unrelated_typo_raises_without_a_suggestion(self, report_50kmh, v1) -> None:
        with pytest.raises(AttributeError):
            report_50kmh.overall(v1).completely_unrelated_name = 1

    def test_wrong_type_is_refused(self, report_50kmh, v1) -> None:
        submarining = report_50kmh.overall(
            v1
        ).criterion_driver.criterion_femur.criterion_submarining
        with pytest.raises(TypeError):
            submarining.submarining = "yes"
        assert submarining.submarining is False

    def test_bool_is_not_a_number(self, report_50kmh, v1) -> None:
        """``isinstance(True, int)`` must not wave through a boolean for a float input."""
        column = report_50kmh.overall(
            v1
        ).criterion_driver.criterion_head.criterion_DisplacementSteeringColumn
        with pytest.raises(TypeError):
            column.displacement_steering_column_rearwards = True

    def test_int_is_accepted_for_a_float_input(self, report_50kmh, v1) -> None:
        column = report_50kmh.overall(
            v1
        ).criterion_driver.criterion_head.criterion_DisplacementSteeringColumn
        column.displacement_steering_column_rearwards = 38
        assert column.displacement_steering_column_rearwards == 38

    def test_valid_assignment_passes(self, report_50kmh, v1) -> None:
        head = report_50kmh.overall(v1).criterion_driver.criterion_head
        head.hard_contact = False
        assert head.hard_contact is False

    def test_framework_fields_stay_assignable(self, report_50kmh, v1) -> None:
        overall = report_50kmh.overall(v1)
        overall.value = 1.0
        overall.rating = 2.0
        overall.color = "green"
        assert (overall.value, overall.rating, overall.color) == (1.0, 2.0, "green")

    def test_private_names_are_exempt(self, report_50kmh, v1) -> None:
        report_50kmh.overall(v1)._scratch = 1
        assert report_50kmh.overall(v1)._scratch == 1

    def test_subcriteria_are_exempt(self, report_50kmh, v1) -> None:
        """Children are attached dynamically in ``__init__`` under names nobody declares."""
        overall = report_50kmh.overall(v1)
        overall.criterion_freshly_attached = overall.criterion_driver
        assert "criterion_freshly_attached" in dict(overall.get_children())


class TestEnumeration:
    def test_every_report_exposes_its_inputs(self, report_50kmh) -> None:
        inputs = report_50kmh.get_inputs()
        assert list(inputs) == ["T0"]
        assert "criterion_driver/criterion_head/hard_contact" in inputs["T0"]
        assert "p_driver" in inputs["T0"]

    def test_print_inputs_marks_deviations(self, report_50kmh, v1) -> None:
        report_50kmh.overall(
            v1
        ).criterion_driver.criterion_femur.criterion_submarining.submarining = True

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            report_50kmh.print_inputs()
        lines = [
            line for line in buffer.getvalue().splitlines() if "submarining" in line
        ]

        assert len(lines) == 2, buffer.getvalue()  # driver (changed) + rear (default)
        assert len([line for line in lines if line.lstrip().startswith("*")]) == 1

    def test_round_trip_is_a_no_op(self, report_50kmh) -> None:
        before = report_50kmh.get_inputs()
        report_50kmh.set_inputs(before)
        assert before == report_50kmh.get_inputs()

    def test_json_round_trip_reproduces_a_run(self, report_50kmh, v1) -> None:
        report_a, a1 = report_50kmh, v1
        report_a.overall(
            a1
        ).criterion_driver.criterion_femur.criterion_submarining.submarining = True
        report_a.overall(
            a1
        ).criterion_door_opening_during_impact.number_of_door_openings_during_impact = 2
        stored = json.loads(json.dumps(report_a.get_inputs()))

        b1 = pyisomme.Isomme(test_number="T0")
        report_b = EuroNCAP_Frontal_50kmh([b1])
        report_b.set_inputs(stored)

        assert (
            report_b.overall(
                b1
            ).criterion_driver.criterion_femur.criterion_submarining.submarining
            is True
        )
        assert (
            report_b.overall(
                b1
            ).criterion_door_opening_during_impact.number_of_door_openings_during_impact
            == 2
        )
        assert report_a.get_inputs() == report_b.get_inputs()

        report_a.calculate()
        report_b.calculate()
        assert (
            report_a.overall(a1).criterion_door_opening_during_impact.rating
            == report_b.overall(b1).criterion_door_opening_during_impact.rating
        )

    def test_unknown_test_is_refused(self, report_50kmh) -> None:
        with pytest.raises(KeyError):
            report_50kmh.set_inputs({"nope": {}})

    def test_unknown_path_is_refused(self, report_50kmh) -> None:
        with pytest.raises(KeyError):
            report_50kmh.set_inputs(
                {"T0": {"criterion_driver/criterion_head/hard_contct": False}}
            )

    def test_wrong_type_from_json_is_refused(self, report_50kmh) -> None:
        with pytest.raises(TypeError):
            report_50kmh.set_inputs(
                {"T0": {"criterion_driver/criterion_head/hard_contact": "yes"}}
            )


class TestPositionSyncF15:
    """
    A seating position set after construction must move the criteria, not only the plots.

    The behaviour under test is unchanged since step 4; the mechanism is gone. Every
    report is migrated as of step 9, so nothing rebuilds anything any more — the context
    is resolved at the start of ``calculate()`` and the same subtree simply reads a
    different position. The ``rebuild`` in the method names below is kept because these
    are the step-4 regression tests and the names are what a failure will be looked up
    by; read it as "a position change that used to need a rebuild".
    """

    def test_position_set_after_construction_reaches_the_criteria(
        self, report_50kmh, v1
    ) -> None:
        overall = report_50kmh.overall(v1)
        assert position(overall.criterion_driver) == "1"

        overall.p_driver = "3"
        report_50kmh.calculate()

        assert position(overall.criterion_driver) == "3"
        assert position(overall.criterion_driver.criterion_head.criterion_hic_15) == "3"
        # ...and the derived positions follow the right-hand-drive rule.
        assert overall.p_front_passenger == "1"
        assert position(overall.criterion_front_passenger) == "1"

    def test_rebuilt_limits_follow_the_new_position(self, report_50kmh, v1) -> None:
        overall = report_50kmh.overall(v1)
        overall.p_driver = "3"
        report_50kmh.calculate()

        patterns = (
            overall.criterion_driver.criterion_head.criterion_hic_15.limits.limit_list[
                0
            ].code_patterns
        )
        assert all(pattern[1] == "3" for pattern in patterns), patterns

    def test_rebuild_preserves_manual_inputs(self, report_50kmh, v1) -> None:
        overall = report_50kmh.overall(v1)
        overall.criterion_driver.criterion_femur.criterion_submarining.submarining = (
            True
        )
        overall.criterion_driver.steering_wheel_airbag_exists = False

        overall.p_driver = "3"
        report_50kmh.calculate()

        assert (
            overall.criterion_driver.criterion_femur.criterion_submarining.submarining
            is True
        )
        assert overall.criterion_driver.steering_wheel_airbag_exists is False

    def test_rebuild_does_not_leave_stale_report_limits(self, report_50kmh, v1) -> None:
        before = len(report_50kmh.limits[v1].limit_list)

        report_50kmh.overall(v1).p_driver = "3"
        report_50kmh.calculate()

        assert len(report_50kmh.limits[v1].limit_list) == before

    def test_unchanged_position_rebuilds_nothing(self, report_50kmh, v1) -> None:
        driver = report_50kmh.overall(v1).criterion_driver
        report_50kmh.calculate()
        assert report_50kmh.overall(v1).criterion_driver is driver

    def test_mpdb_syncs_too(self, report_mpdb, v1) -> None:
        report = report_mpdb
        overall = report.overall(v1)
        overall.p_driver = "3"
        report.calculate()
        assert position(overall.criterion_driver) == "3"
        assert position(overall.criterion_passenger) == "1"


class TestDerivedVsUserSetPositions:
    """A derivation fills what the user left alone — it never overwrites a set input."""

    def test_explicit_passenger_position_survives_the_derivation(
        self, report_50kmh, v1
    ) -> None:
        overall = report_50kmh.overall(v1)

        overall.p_driver = "3"  # right-hand drive: would derive 1 / 4
        overall.p_front_passenger = "5"  # ...but this test seated it centrally
        report_50kmh.calculate()

        assert overall.p_front_passenger == "5"
        assert position(overall.criterion_front_passenger) == "5"
        assert overall.p_rear_passenger == "4"  # untouched -> still derived

    def test_explicit_value_equal_to_the_default_still_wins(
        self, report_50kmh, v1
    ) -> None:
        """The case ``value != default`` cannot see: set explicitly *to* the default."""
        overall = report_50kmh.overall(v1)

        overall.p_driver = "3"
        overall.p_front_passenger = "3"  # the declared default, meant literally
        report_50kmh.calculate()

        assert overall.p_front_passenger == "3"
        assert position(overall.criterion_front_passenger) == "3"

    def test_derivation_is_idempotent_across_recalculation(
        self, report_50kmh, v1
    ) -> None:
        """A derived value must follow ``p_driver`` back, not stick at the old one."""
        overall = report_50kmh.overall(v1)

        overall.p_driver = "3"
        report_50kmh.calculate()
        assert overall.p_front_passenger == "1"

        overall.p_driver = "1"
        report_50kmh.calculate()
        assert overall.p_front_passenger == "3"
        assert position(overall.criterion_front_passenger) == "3"

    def test_set_inputs_counts_as_user_set(self, report_50kmh, v1) -> None:
        """A replayed input file pins the positions it recorded."""
        report_50kmh.set_inputs({"T0": {"p_driver": "3", "p_front_passenger": "5"}})
        report_50kmh.calculate()

        assert position(report_50kmh.overall(v1).criterion_front_passenger) == "5"

    def test_a_rebuilt_subtree_keeps_derived_values_derived(
        self, report_50kmh, v1
    ) -> None:
        """A value the report derived must not be frozen by a rebuild (MPDB nests one)."""
        overall = report_50kmh.overall(v1)

        overall.p_driver = "3"
        report_50kmh.calculate()
        assert not overall.input_is_set("p_front_passenger")

        overall.p_driver = "1"
        report_50kmh.calculate()
        assert position(overall.criterion_front_passenger) == "3"

    def test_input_is_set_reports_the_source(self, report_50kmh, v1) -> None:
        overall = report_50kmh.overall(v1)

        assert not overall.input_is_set("p_driver")
        assert not overall.input_is_set("p_front_passenger")

        overall.p_front_passenger = "5"
        assert overall.input_is_set("p_front_passenger")

    def test_set_derived_input_rejects_an_undeclared_name(
        self, report_50kmh, v1
    ) -> None:
        with pytest.raises(AttributeError):
            report_50kmh.overall(v1).set_derived_input("p_drivr", 3)

    def test_print_inputs_distinguishes_derived_from_user_set(
        self, report_50kmh, v1
    ) -> None:
        report_50kmh.overall(v1).p_driver = "3"  # derives p_front_passenger = 1
        report_50kmh.calculate()

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            report_50kmh.print_inputs()
        # "\t{marker} {path}: {value} ..."
        markers = {
            line[3:].split(":")[0]: line[1]
            for line in buffer.getvalue().splitlines()
            if line.startswith("\t")
        }

        assert markers["p_driver"] == "*"
        assert markers["p_front_passenger"] == "~"
        assert markers["criterion_driver/criterion_head/hard_contact"] == " "


class TestFrameworkInternals:
    def test_settable_names_include_annotations_and_attributes(self) -> None:
        names = settable_names(EuroNCAP_Frontal_50kmh.Criterion_Overall)
        assert "value" in names  # annotated on Criterion, never assigned there
        assert "name" in names  # plain class attribute
        assert "p_driver" in names  # manual input, declared without a value

    def test_declared_inputs_is_cached(self) -> None:
        cls = EuroNCAP_Frontal_50kmh.Criterion_Overall
        assert declared_inputs(cls) is declared_inputs(cls)

    def test_a_locally_declared_input_works_end_to_end(self) -> None:
        """The declaration idiom must work outside the report modules too."""

        class Local(Criterion):
            name = "Local"
            flag: Manual[bool, manual(False, doc="a locally declared input")]

            def calculation(self) -> None:
                self.value = 1.0 if self.flag else 0.0

        class LocalReport(Report[Local]):
            _name = "Local"
            Criterion_Overall = Local

        isomme = pyisomme.Isomme(test_number="T0")
        report = LocalReport([isomme])
        criterion = report.overall(isomme)

        assert criterion.flag is False
        criterion.calculate()
        assert criterion.value == 0.0

        criterion.flag = True
        criterion.calculate()
        assert criterion.value == 1.0

        with pytest.raises(AttributeError):
            criterion.flg = True  # pyright: ignore[reportArgumentType]
