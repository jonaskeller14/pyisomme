"""FMVSS 214 moving-barrier and vehicle-to-pole compliance report.

The report implements the advanced-dummy injury requirements in S7.2.5-S7.2.6
and S9.2.1-S9.2.2.  It detects ES-2/ES-2re (``E2``/``ER``) and SID-IIs
(``S2``) occupants from ISO-MME channel codes.  The impact type and the front
and rear struck-side positions are manual inputs: their defaults are derived
from the available channels, but a user can override them before ``calculate()``.

Door integrity under S7.3/S9.2.3 cannot be established from signal channels.
Its three observations therefore remain conservative manual inputs.
"""

from __future__ import annotations

import logging
from dataclasses import replace
from enum import Enum
from typing import Any, cast

import numpy as np
import pandas as pd

from pyisomme.channel import Channel, time_intersect
from pyisomme.isomme import Isomme
from pyisomme.limit import Limit
from pyisomme.report.criterion import Criterion, Role, sub
from pyisomme.report.criterion_result import CriterionResult
from pyisomme.report.ctx import from_input
from pyisomme.report.fmvss.limits import Limit_Fail, Limit_Pass
from pyisomme.report.fmvss.protocols import PROTOCOL_214_2026_07_06
from pyisomme.report.manual import Manual, manual
from pyisomme.report.page2 import (
    ChannelPlotPage,
    CoverPage,
    CriterionTablePage,
    CriterionValuesChartPage,
    HICPage,
    ManualInputsPage,
    ReportStatusPage,
    channel_plot_spec_for,
    criterion_values_chart_spec_for,
    hic_spec_for,
    manual_inputs_spec_for,
    rating_table_spec_for,
    report_status_spec_for,
    values_table_spec_for,
)
from pyisomme.report.report import Report
from pyisomme.unit import Unit, g0

logger = logging.getLogger(__name__)


class ImpactType(str, Enum):
    """FMVSS 214 dynamic side-impact load case."""

    BARRIER = "barrier"
    POLE = "pole"


class DummyType(str, Enum):
    """Dummy families used by the current FMVSS 214 dynamic requirements."""

    ES2RE = "ER"
    SID_IIS = "S2"

    @property
    def label(self) -> str:
        return {
            DummyType.ES2RE: "ES-2re 50th-percentile adult male",
            DummyType.SID_IIS: "SID-IIs 5th-percentile adult female",
        }[self]


IMPACT_TYPE = manual(
    ImpactType.POLE.value,
    source="test report / ISO-MME channel codes",
    doc=(
        "'barrier' for the moving deformable barrier test or 'pole' for the "
        "vehicle-to-pole test. Derived as barrier when a rear SID-IIs position is "
        "detected; otherwise pole."
    ),
)
P_FRONT = manual(
    "1",
    source="test report / ISO-MME channel codes",
    doc=(
        "Channel-code position of the struck-side front occupant. Derived from "
        "ER/E2/S2 channels at a front outboard position when available."
    ),
)
P_REAR = manual(
    "6",
    source="test report / ISO-MME channel codes",
    doc=(
        "Channel-code position of the struck-side rear occupant in a barrier test. "
        "Derived from rear S2 channels or from the side of p_front."
    ),
)
DUMMY_TYPE = manual(
    DummyType.ES2RE.value,
    source="ISO-MME channel codes",
    doc=(
        "'ER' for an ES-2/ES-2re occupant or 'S2' for a SID-IIs occupant. E2 and "
        "ER channel identifiers are both mapped to the ES-2re requirement family."
    ),
)


class _FMVSS214Criterion(Criterion):
    @property
    def selected_dummy_type(self) -> DummyType:
        owner = self.find_input_owner(DUMMY_TYPE)
        if owner is None:
            raise RuntimeError(f"{self.name} has no occupant dummy-type input")
        return DummyType(cast("Criterion_Occupant", owner).dummy_type)


class Criterion_HIC36(_FMVSS214Criterion):
    name = "HIC 36"
    source = "S7.2.5(a), S7.2.6(a); S9.2.1(a), S9.2.2(a)"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}HICR0036??00RX", "?{p}HICRCG36??00RX")
        return [
            Limit_Pass(codes, func=lambda x: 1000, y_unit=1, upper=True),
            Limit_Fail(codes, func=lambda x: 1000, y_unit=1, lower=True),
        ]

    def calculation(self) -> CriterionResult:
        occupant = cast("Criterion_Occupant", self._parent)
        if not occupant.is_active:
            return CriterionResult(channel=None, value=np.nan, rating=1.0, color=None)
        channel = self.require_channel(
            self.ctx.code("?{p}HICR0036??00RX"),
            self.ctx.code("?{p}HICRCG36??00RX"),
        )
        value = float(np.max(channel.get_data()))
        evaluation = self.limits.evaluate(channel)
        return CriterionResult(
            channel=channel,
            value=value,
            rating=evaluation.get_limit_min_rating(interpolate=False),
            color=evaluation.get_limit_min_color(),
        )


class Criterion_ES2re_Rib_Deflection(_FMVSS214Criterion):
    name = "Maximum Rib Deflection"
    source = "S7.2.5(b); S9.2.1(b)"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}RIBS??????DSY?")
        return [
            Limit_Pass(codes, func=lambda x: 44, y_unit="mm", upper=True),
            Limit_Fail(codes, func=lambda x: 44, y_unit="mm", lower=True),
        ]

    def calculation(self) -> CriterionResult:
        occupant = cast("Criterion_Occupant", self._parent)
        if not occupant.is_active or self.selected_dummy_type is not DummyType.ES2RE:
            return CriterionResult(channel=None, value=np.nan, rating=1.0, color=None)
        channels = [
            self.require_channel(
                *self.ctx.codes(
                    f"?{{p}}RIBSLE{level}??DSY?",
                    f"?{{p}}RIBSRI{level}??DSY?",
                    f"?{{p}}RIBSLE0{index}??DSY?",
                    f"?{{p}}RIBSRI0{index}??DSY?",
                )
            ).convert_unit("mm")
            for index, level in enumerate(("UP", "MI", "LO"), 1)
        ]
        value = float(
            np.max([np.max(np.abs(channel.get_data())) for channel in channels])
        )
        channel = Channel(channels[0].code, pd.DataFrame([value]), "mm")
        evaluation = self.limits.evaluate(channel)
        return CriterionResult(
            channel=channel,
            value=value,
            rating=evaluation.get_limit_min_rating(interpolate=False),
            color=evaluation.get_limit_min_color(),
        )


class Criterion_ES2re_Abdominal_Force(_FMVSS214Criterion):
    name = "Sum of Abdominal Forces"
    source = "S7.2.5(c)(1); S9.2.1(c)(1)"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}ABDO??????FOY?")
        return [
            Limit_Pass(codes, func=lambda x: 2500, y_unit="N", upper=True),
            Limit_Fail(codes, func=lambda x: 2500, y_unit="N", lower=True),
        ]

    def calculation(self) -> CriterionResult:
        occupant = cast("Criterion_Occupant", self._parent)
        if not occupant.is_active or self.selected_dummy_type is not DummyType.ES2RE:
            return CriterionResult(channel=None, value=np.nan, rating=1.0, color=None)
        channels = [
            self.require_channel(
                *self.ctx.codes(
                    f"?{{p}}ABDOLE{location}??FOY?",
                    f"?{{p}}ABDORI{location}??FOY?",
                    f"?{{p}}ABDO{location}00??FOY?",
                )
            ).convert_unit("N")
            for location in ("FR", "MI", "RE")
        ]
        time = time_intersect(*channels)
        if not len(time):
            raise ValueError("abdominal force channels have no common time samples")
        combined = np.sum(
            # S7.2.5(c)(1)/S9.2.1(c)(1) do not prescribe a sign convention.
            # Sum force magnitudes so either tension or compression is conservative.
            [np.abs(channel.get_data(t=time)) for channel in channels], axis=0
        )
        value = float(np.max(combined))
        channel = Channel(channels[0].code, pd.DataFrame(combined, index=time), "N")
        evaluation = self.limits.evaluate(channel)
        return CriterionResult(
            channel=channel,
            value=value,
            rating=evaluation.get_limit_min_rating(interpolate=False),
            color=evaluation.get_limit_min_color(),
        )


class Criterion_ES2re_Pubic_Symphysis_Force(_FMVSS214Criterion):
    name = "Pubic Symphysis Force"
    source = "S7.2.5(c)(2); S9.2.1(c)(2)"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}PUBC0000??FOY?")
        return [
            Limit_Pass(codes, func=lambda x: 6000, y_unit="N", upper=True),
            Limit_Fail(codes, func=lambda x: 6000, y_unit="N", lower=True),
        ]

    def calculation(self) -> CriterionResult:
        occupant = cast("Criterion_Occupant", self._parent)
        if not occupant.is_active or self.selected_dummy_type is not DummyType.ES2RE:
            return CriterionResult(channel=None, value=np.nan, rating=1.0, color=None)
        source = self.require_channel(
            *self.ctx.codes("?{p}PUBC0000??FOY?", "?{p}PUBC??????FOR?")
        ).convert_unit("N")
        # The regulation does not restrict the pubic force to one direction.
        # Evaluate its magnitude so either tension or compression can fail.
        data = np.abs(source.get_data())
        value = float(np.max(data))
        channel = Channel(source.code, pd.DataFrame(data, index=source.data.index), "N")
        evaluation = self.limits.evaluate(channel)
        return CriterionResult(
            channel=channel,
            value=value,
            rating=evaluation.get_limit_min_rating(interpolate=False),
            color=evaluation.get_limit_min_color(),
        )


class Criterion_SID_IIs_Lower_Spine_Acceleration(_FMVSS214Criterion):
    name = "Lower Spine Resultant Acceleration"
    source = "S7.2.6(b); S9.2.2(b)"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes(
            "?{p}SPINLO00??ACR?",
            "?{p}LUSP0000??ACR?",
            "?{p}SPIN0000??ACR?",
        )
        return [
            Limit_Pass(codes, func=lambda x: 82, y_unit=Unit(g0), upper=True),
            Limit_Fail(codes, func=lambda x: 82, y_unit=Unit(g0), lower=True),
        ]

    def calculation(self) -> CriterionResult:
        occupant = cast("Criterion_Occupant", self._parent)
        if not occupant.is_active or self.selected_dummy_type is not DummyType.SID_IIS:
            return CriterionResult(channel=None, value=np.nan, rating=1.0, color=None)
        source = self.require_channel(
            *self.ctx.codes(
                "?{p}SPINLO00??ACR?",
                "?{p}LUSP0000??ACR?",
                "?{p}SPIN0000??ACR?",
            )
        ).convert_unit(Unit(g0))
        # This channel is a resultant and is therefore non-negative by definition.
        data = source.get_data()
        value = float(np.max(data))
        channel = Channel(
            source.code, pd.DataFrame(data, index=source.data.index), Unit(g0)
        )
        evaluation = self.limits.evaluate(channel)
        return CriterionResult(
            channel=channel,
            value=value,
            rating=evaluation.get_limit_min_rating(interpolate=False),
            color=evaluation.get_limit_min_color(),
        )


class Criterion_SID_IIs_Pelvic_Force(_FMVSS214Criterion):
    name = "Sum of Acetabular and Iliac Pelvic Forces"
    source = "S7.2.6(c); S9.2.2(c)"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}ACTB??????FOY?", "?{p}ILUM??????FOY?")
        return [
            Limit_Pass(codes, func=lambda x: 5525, y_unit="N", upper=True),
            Limit_Fail(codes, func=lambda x: 5525, y_unit="N", lower=True),
        ]

    def calculation(self) -> CriterionResult:
        occupant = cast("Criterion_Occupant", self._parent)
        if not occupant.is_active or self.selected_dummy_type is not DummyType.SID_IIS:
            return CriterionResult(channel=None, value=np.nan, rating=1.0, color=None)
        channels = [
            self.require_channel(
                *self.ctx.codes(
                    f"?{{p}}{location}LE00??FOY?",
                    f"?{{p}}{location}RI00??FOY?",
                    f"?{{p}}{location}0000??FOY?",
                )
            ).convert_unit("N")
            for location in ("ACTB", "ILUM")
        ]
        time = time_intersect(*channels)
        if not len(time):
            raise ValueError(
                "acetabular and iliac force channels have no common samples"
            )
        combined = np.sum(
            # S7.2.6(c)/S9.2.2(c) do not prescribe a sign convention. Sum force
            # magnitudes so either tension or compression is conservative.
            [np.abs(channel.get_data(t=time)) for channel in channels], axis=0
        )
        value = float(np.max(combined))
        channel = Channel(channels[0].code, pd.DataFrame(combined, index=time), "N")
        evaluation = self.limits.evaluate(channel)
        return CriterionResult(
            channel=channel,
            value=value,
            rating=evaluation.get_limit_min_rating(interpolate=False),
            color=evaluation.get_limit_min_color(),
        )


class Criterion_Occupant(_FMVSS214Criterion):
    name = "Occupant"
    role = Role.AGGREGATE
    dummy_type: Manual[str, DUMMY_TYPE]
    is_active: bool = True

    criterion_hic36 = sub(Criterion_HIC36)
    criterion_es2re_rib_deflection = sub(Criterion_ES2re_Rib_Deflection)
    criterion_es2re_abdominal_force = sub(Criterion_ES2re_Abdominal_Force)
    criterion_es2re_pubic_symphysis_force = sub(Criterion_ES2re_Pubic_Symphysis_Force)
    criterion_sid_iis_lower_spine_acceleration = sub(
        Criterion_SID_IIs_Lower_Spine_Acceleration
    )
    criterion_sid_iis_pelvic_force = sub(Criterion_SID_IIs_Pelvic_Force)

    def prepare(self) -> None:
        position = self.ctx.field("p")
        detected = {
            channel.code.fine_location_3
            for channel in self.isomme.channels
            if channel.code.position == position
            and channel.code.fine_location_3 in {"E2", "ER", "S2"}
        }
        if "S2" in detected and not ({"E2", "ER"} & detected):
            self.set_derived_input("dummy_type", DummyType.SID_IIS.value)
        elif {"E2", "ER"} & detected and "S2" not in detected:
            self.set_derived_input("dummy_type", DummyType.ES2RE.value)

    def calculation(self) -> CriterionResult:
        if not self.is_active:
            return CriterionResult(channel=None, value=np.nan, rating=1.0, color=None)
        criteria: list[Criterion] = [self.criterion_hic36]
        if self.selected_dummy_type is DummyType.ES2RE:
            criteria.extend(
                [
                    self.criterion_es2re_rib_deflection,
                    self.criterion_es2re_abdominal_force,
                    self.criterion_es2re_pubic_symphysis_force,
                ]
            )
        else:
            criteria.extend(
                [
                    self.criterion_sid_iis_lower_spine_acceleration,
                    self.criterion_sid_iis_pelvic_force,
                ]
            )
        rating = float(np.min([Criterion.rating_of(item) for item in criteria]))
        color = Limit_Pass.color if rating else Limit_Fail.color
        return CriterionResult(channel=None, value=rating, rating=rating, color=color)


class Criterion_Rear_Occupant(Criterion_Occupant):
    name = "Rear Occupant"

    def prepare(self) -> None:
        impact_owner = self.find_input_owner(IMPACT_TYPE)
        if impact_owner is None:
            raise RuntimeError("rear occupant has no impact-type input")
        self.is_active = (
            ImpactType(cast("Overall", impact_owner).impact_type) is ImpactType.BARRIER
        )
        super().prepare()


class Criterion_Door_Integrity(Criterion):
    name = "Door Integrity"
    source = "S7.3; S9.2.3"
    struck_door_remained_attached: Manual[
        bool,
        manual(
            False,
            source="video / post-test inspection",
            doc="The door struck by the barrier or pole did not separate totally.",
        ),
    ]
    unstruck_doors_remained_latched: Manual[
        bool,
        manual(
            False,
            source="video / post-test inspection",
            doc="Every unstruck door remained engaged in its latched position.",
        ),
    ]
    latches_hinges_and_anchorages_remained_attached: Manual[
        bool,
        manual(
            False,
            source="post-test inspection",
            doc=(
                "No latch separated from its striker; no hinge component separated; "
                "and no latch or hinge system pulled out of its anchorage."
            ),
        ),
    ]

    def calculation(self) -> CriterionResult:
        passed = all(
            (
                self.struck_door_remained_attached,
                self.unstruck_doors_remained_latched,
                self.latches_hinges_and_anchorages_remained_attached,
            )
        )
        return CriterionResult(
            channel=None,
            value=float(passed),
            rating=float(passed),
            color=Limit_Pass.color if passed else Limit_Fail.color,
        )


class Overall(Criterion):
    name = "Overall"
    source = "S7.2-S7.3; S9.2"
    role = Role.AGGREGATE
    impact_type: Manual[str, IMPACT_TYPE]
    p_front: Manual[str, P_FRONT]
    p_rear: Manual[str, P_REAR]

    def __init__(self, report: Report[Any], isomme: Isomme) -> None:
        super().__init__(report, isomme)
        self.prepare()

    def prepare(self) -> None:
        positions: dict[str, set[str]] = {}
        for channel in self.isomme.channels:
            dummy = channel.code.fine_location_3
            if dummy in {"E2", "ER", "S2"}:
                positions.setdefault(channel.code.position, set()).add(dummy)

        front_positions = sorted(position for position in positions if position in "13")
        rear_positions = sorted(
            position
            for position, dummies in positions.items()
            if position in "46" and "S2" in dummies
        )
        if front_positions:
            self.set_derived_input("p_front", front_positions[0])
        if rear_positions:
            self.set_derived_input("p_rear", rear_positions[0])
        else:
            self.set_derived_input("p_rear", "6" if self.p_front == "1" else "4")
        self.set_derived_input(
            "impact_type",
            ImpactType.BARRIER.value if rear_positions else ImpactType.POLE.value,
        )

    def calculation(self) -> CriterionResult:
        impact_type = ImpactType(self.impact_type)
        criteria: list[Criterion] = [
            self.criterion_front_occupant,
            self.criterion_door_integrity,
        ]
        if impact_type is ImpactType.BARRIER:
            criteria.insert(1, self.criterion_rear_occupant)
        rating = float(np.min([Criterion.rating_of(item) for item in criteria]))
        color = Limit_Pass.color if rating else Limit_Fail.color
        return CriterionResult(channel=None, value=rating, rating=rating, color=color)

    criterion_front_occupant = sub(
        Criterion_Occupant,
        name="Front Occupant",
        at=from_input(P_FRONT),
        role=Role.AGGREGATE,
    )
    criterion_rear_occupant = sub(
        Criterion_Rear_Occupant,
        at=from_input(P_REAR),
        role=Role.AGGREGATE,
    )
    criterion_door_integrity = sub(Criterion_Door_Integrity)


class FMVSS_214(Report[Overall]):
    _name = "FMVSS 214 | Side Impact Protection"
    _protocol = PROTOCOL_214_2026_07_06
    _protocols = (PROTOCOL_214_2026_07_06,)
    Criterion_Overall = Overall

    def __init__(
        self,
        isomme_list: list[Isomme],
        title: str | None = None,
        protocol_version: str | None = None,
    ) -> None:
        super().__init__(
            isomme_list,
            title=title or "FMVSS 214 Compliance",
            protocol_version=protocol_version,
        )

        self._available_pages = (
            CoverPage(self),
            ReportStatusPage(self, spec=report_status_spec_for(self)),
            ManualInputsPage(self, spec=manual_inputs_spec_for(self)),
            CriterionTablePage(
                self,
                name="Overall Compliance",
                title="Overall Compliance",
                spec=replace(
                    rating_table_spec_for(self),
                    cell_text=lambda criterion: (
                        "n/a"
                        if np.isnan(Criterion.value_of(criterion))
                        else "Pass"
                        if Criterion.rating_of(criterion)
                        else "Fail"
                    ),
                ).with_criteria(
                    lambda report: {
                        isomme: [
                            report.overall(isomme).criterion_front_occupant,
                            report.overall(isomme).criterion_rear_occupant,
                            report.overall(isomme).criterion_door_integrity,
                            report.overall(isomme),
                        ]
                        for isomme in report.isomme_list
                    }
                ),
            ),
            CriterionValuesChartPage(
                self,
                spec=criterion_values_chart_spec_for(
                    self,
                    name="Front Occupant Values Chart",
                    title="Front Occupant Values",
                ).with_criteria(
                    lambda report: {
                        isomme: [
                            report.overall(
                                isomme
                            ).criterion_front_occupant.criterion_hic36,
                            report.overall(
                                isomme
                            ).criterion_front_occupant.criterion_es2re_rib_deflection,
                            report.overall(
                                isomme
                            ).criterion_front_occupant.criterion_es2re_abdominal_force,
                            report.overall(
                                isomme
                            ).criterion_front_occupant.criterion_es2re_pubic_symphysis_force,
                            report.overall(
                                isomme
                            ).criterion_front_occupant.criterion_sid_iis_lower_spine_acceleration,
                            report.overall(
                                isomme
                            ).criterion_front_occupant.criterion_sid_iis_pelvic_force,
                        ]
                        for isomme in report.isomme_list
                    }
                ),
            ),
            CriterionTablePage(
                self,
                name="Front Occupant Values Table",
                title="Front Occupant Values",
                spec=values_table_spec_for(self).with_criteria(
                    lambda report: {
                        isomme: [
                            report.overall(
                                isomme
                            ).criterion_front_occupant.criterion_hic36,
                            report.overall(
                                isomme
                            ).criterion_front_occupant.criterion_es2re_rib_deflection,
                            report.overall(
                                isomme
                            ).criterion_front_occupant.criterion_es2re_abdominal_force,
                            report.overall(
                                isomme
                            ).criterion_front_occupant.criterion_es2re_pubic_symphysis_force,
                            report.overall(
                                isomme
                            ).criterion_front_occupant.criterion_sid_iis_lower_spine_acceleration,
                            report.overall(
                                isomme
                            ).criterion_front_occupant.criterion_sid_iis_pelvic_force,
                            report.overall(isomme).criterion_front_occupant,
                        ]
                        for isomme in report.isomme_list
                    }
                ),
            ),
            HICPage(
                self,
                spec=hic_spec_for(
                    self,
                    name="Front Occupant HIC36",
                    title="Front Occupant HIC36",
                    timespan=36,
                )
                .with_position(lambda report, isomme: report.overall(isomme).p_front)
                .with_criterion(
                    lambda report, isomme: (
                        report.overall(isomme).criterion_front_occupant.criterion_hic36
                    )
                ),
            ),
            ChannelPlotPage(
                self,
                spec=channel_plot_spec_for(
                    self,
                    name="Front Occupant Head Acceleration",
                    title="Front Occupant Head Acceleration",
                    nrows=2,
                    ncols=2,
                    sharey=True,
                ).with_channels(
                    lambda report: {
                        isomme: [
                            [f"?{report.overall(isomme).p_front}HEAD??????ACXA"],
                            [f"?{report.overall(isomme).p_front}HEAD??????ACYA"],
                            [f"?{report.overall(isomme).p_front}HEAD??????ACZA"],
                            [f"?{report.overall(isomme).p_front}HEAD??????ACRA"],
                        ]
                        for isomme in report.isomme_list
                    }
                ),
            ),
            ChannelPlotPage(
                self,
                spec=channel_plot_spec_for(
                    self,
                    name="Front Occupant Chest Deflection",
                    title="Front Occupant Chest Deflection",
                    nrows=1,
                    ncols=1,
                ).with_channels(
                    lambda report: {
                        isomme: [[f"?{report.overall(isomme).p_front}RIBS??????DSY?"]]
                        for isomme in report.isomme_list
                    }
                ),
            ),
            ChannelPlotPage(
                self,
                spec=channel_plot_spec_for(
                    self,
                    name="Front Occupant Abdomen Force",
                    title="Front Occupant Abdomen Force",
                    nrows=1,
                    ncols=1,
                ).with_channels(
                    lambda report: {
                        isomme: [[f"?{report.overall(isomme).p_front}ABDO??????FOY?"]]
                        for isomme in report.isomme_list
                    }
                ),
            ),
            ChannelPlotPage(
                self,
                spec=channel_plot_spec_for(
                    self,
                    name="Front Occupant Lower Spine Acceleration",
                    title="Front Occupant Lower Spine Acceleration",
                    nrows=1,
                    ncols=1,
                ).with_channels(
                    lambda report: {
                        isomme: [
                            [
                                f"?{report.overall(isomme).p_front}SPIN??????ACR?",
                                f"?{report.overall(isomme).p_front}LUSP??????ACR?",
                            ]
                        ]
                        for isomme in report.isomme_list
                    }
                ),
            ),
            ChannelPlotPage(
                self,
                spec=channel_plot_spec_for(
                    self,
                    name="Front Occupant Pelvis Force",
                    title="Front Occupant Pelvis Force",
                    nrows=1,
                    ncols=1,
                ).with_channels(
                    lambda report: {
                        isomme: [
                            [
                                f"?{report.overall(isomme).p_front}PUBC??????FOY?",
                                f"?{report.overall(isomme).p_front}ACTB??????FOY?",
                                f"?{report.overall(isomme).p_front}ILUM??????FOY?",
                            ]
                        ]
                        for isomme in report.isomme_list
                    }
                ),
            ),
            CriterionValuesChartPage(
                self,
                spec=criterion_values_chart_spec_for(
                    self,
                    name="Rear Occupant Values Chart",
                    title="Rear Occupant Values",
                ).with_criteria(
                    lambda report: {
                        isomme: [
                            report.overall(
                                isomme
                            ).criterion_rear_occupant.criterion_hic36,
                            report.overall(
                                isomme
                            ).criterion_rear_occupant.criterion_sid_iis_lower_spine_acceleration,
                            report.overall(
                                isomme
                            ).criterion_rear_occupant.criterion_sid_iis_pelvic_force,
                        ]
                        for isomme in report.isomme_list
                    }
                ),
            ),
            CriterionTablePage(
                self,
                name="Rear Occupant Values Table",
                title="Rear Occupant Values",
                spec=values_table_spec_for(self).with_criteria(
                    lambda report: {
                        isomme: [
                            report.overall(
                                isomme
                            ).criterion_rear_occupant.criterion_hic36,
                            report.overall(
                                isomme
                            ).criterion_rear_occupant.criterion_sid_iis_lower_spine_acceleration,
                            report.overall(
                                isomme
                            ).criterion_rear_occupant.criterion_sid_iis_pelvic_force,
                            report.overall(isomme).criterion_rear_occupant,
                        ]
                        for isomme in report.isomme_list
                    }
                ),
            ),
            HICPage(
                self,
                spec=hic_spec_for(
                    self,
                    name="Rear Occupant HIC36",
                    title="Rear Occupant HIC36",
                    timespan=36,
                )
                .with_position(lambda report, isomme: report.overall(isomme).p_rear)
                .with_criterion(
                    lambda report, isomme: (
                        report.overall(isomme).criterion_rear_occupant.criterion_hic36
                    )
                ),
            ),
            ChannelPlotPage(
                self,
                spec=channel_plot_spec_for(
                    self,
                    name="Rear Occupant Head Acceleration",
                    title="Rear Occupant Head Acceleration",
                    nrows=2,
                    ncols=2,
                    sharey=True,
                ).with_channels(
                    lambda report: {
                        isomme: [
                            [f"?{report.overall(isomme).p_rear}HEAD??????ACXA"],
                            [f"?{report.overall(isomme).p_rear}HEAD??????ACYA"],
                            [f"?{report.overall(isomme).p_rear}HEAD??????ACZA"],
                            [f"?{report.overall(isomme).p_rear}HEAD??????ACRA"],
                        ]
                        for isomme in report.isomme_list
                    }
                ),
            ),
            ChannelPlotPage(
                self,
                spec=channel_plot_spec_for(
                    self,
                    name="Rear Occupant Lower Spine Acceleration",
                    title="Rear Occupant Lower Spine Acceleration",
                    nrows=1,
                    ncols=1,
                ).with_channels(
                    lambda report: {
                        isomme: [
                            [
                                f"?{report.overall(isomme).p_rear}SPIN??????ACR?",
                                f"?{report.overall(isomme).p_rear}LUSP??????ACR?",
                            ]
                        ]
                        for isomme in report.isomme_list
                    }
                ),
            ),
            ChannelPlotPage(
                self,
                spec=channel_plot_spec_for(
                    self,
                    name="Rear Occupant Pelvis Force",
                    title="Rear Occupant Pelvis Force",
                    nrows=1,
                    ncols=1,
                ).with_channels(
                    lambda report: {
                        isomme: [
                            [
                                f"?{report.overall(isomme).p_rear}ACTB??????FOY?",
                                f"?{report.overall(isomme).p_rear}ILUM??????FOY?",
                            ]
                        ]
                        for isomme in report.isomme_list
                    }
                ),
            ),
        )
        self._selected_pages = list(self._available_pages)


__all__ = ["DummyType", "FMVSS_214", "ImpactType", "Overall"]
