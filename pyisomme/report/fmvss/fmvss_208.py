"""FMVSS 208 adult frontal rigid-barrier injury-criteria report.

The deliberately narrow compliance scope and conservative assumptions are documented in
``docs/log/20260809_FMVSS-208-Report.md``. In short, one report instance assesses the
front outboard occupants in one modern rigid-barrier test. Each occupant independently
uses the Hybrid III 50th-percentile male (``H3``) or 5th-percentile female (``HF``)
criteria detected from its ISO-MME channels. The stricter ``HF`` family is the fallback;
test setup and equipment provisions remain external checks.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import cast

import numpy as np

from pyisomme.isomme import Isomme
from pyisomme.limit import Limit
from pyisomme.report.criterion import Criterion, Role, sub
from pyisomme.report.ctx import from_input
from pyisomme.report.fmvss.limits import Limit_Fail, Limit_Pass
from pyisomme.report.fmvss.protocols import PROTOCOL_2022_10_14
from pyisomme.report.manual import Manual, manual
from pyisomme.report.page import (
    Page_Cover,
    Page_Criterion_Rating_Table,
    Page_Criterion_Values_Chart,
    Page_Criterion_Values_Table,
    Page_Plot_nxn,
)
from pyisomme.report.report import Report
from pyisomme.unit import Unit, g0

logger = logging.getLogger(__name__)


class DummyType(str, Enum):
    """Adult dummy family whose FMVSS 208 thresholds and channel codes are used."""

    FEMALE_5TH = "HF"
    MALE_50TH = "H3"

    @property
    def label(self) -> str:
        return {
            DummyType.FEMALE_5TH: "Hybrid III 5th-percentile adult female",
            DummyType.MALE_50TH: "Hybrid III 50th-percentile adult male",
        }[self]


P_DRIVER = manual(
    "1",
    source="test report",
    doc=(
        "Channel-code position of the driver. Defaults to the "
        "'Driver position object 1' test-info field when the test carries it."
    ),
)
P_PASSENGER = manual(
    "3",
    source="test report",
    doc=(
        "Channel-code position of the front outboard passenger. Derived from p_driver "
        "('1' for a right-hand-drive test) unless set explicitly."
    ),
)
DUMMY_TYPE = manual(
    DummyType.FEMALE_5TH.value,
    source="ISO-MME channel codes",
    doc=(
        "ISO-MME dummy identifier for this occupant: 'H3' for a Hybrid III "
        "50th-percentile male or 'HF' for a Hybrid III 5th-percentile female. Derived "
        "from channels at the occupant position; conservatively defaults to 'HF' when "
        "the channels are absent or ambiguous."
    ),
)


class _FMVSSCriterion(Criterion):
    """Small FMVSS-specific conveniences; leaf calculations remain explicit."""

    @property
    def selected_dummy_type(self) -> DummyType:
        owner = self.find_input_owner(DUMMY_TYPE)
        if owner is None:
            raise RuntimeError(f"{self.name} has no occupant dummy-type input")
        return DummyType(cast("Criterion_Occupant", owner).dummy_type)

    @property
    def dummy_identifier(self) -> str:
        return self.selected_dummy_type.value

    def dummy_code(self, template: str) -> str:
        return self.ctx.code(template.replace("{dummy}", self.dummy_identifier))

    def dummy_codes(self, *templates: str) -> tuple[str, ...]:
        return tuple(self.dummy_code(template) for template in templates)

    def dummy_threshold(self, *, male_50th: float, female_5th: float) -> float:
        return (
            female_5th
            if self.selected_dummy_type is DummyType.FEMALE_5TH
            else male_50th
        )


class Criterion_Containment(_FMVSSCriterion):
    name = "Dummy Containment"
    source = "S6.1; S15.3.1"
    contained: Manual[
        bool,
        manual(
            False,
            source="video / post-test inspection",
            doc=(
                "Were all portions of the dummy contained within the outer surfaces of the "
                "passenger compartment? Defaults to False until positively confirmed."
            ),
        ),
    ]

    def calculation(self) -> None:
        self.value = float(self.contained)
        self.rating = float(self.contained)
        self.color = Limit_Pass.color if self.contained else Limit_Fail.color


class Criterion_HIC15(_FMVSSCriterion):
    name = "HIC 15"
    source = "S6.2(b); S15.3.2"

    def define_limits(self) -> list[Limit]:
        codes = self.dummy_codes("?{p}HICR0015{dummy}00R?")
        return [
            Limit_Pass(codes, func=lambda x: 700, y_unit=1, upper=True),
            Limit_Fail(codes, func=lambda x: 700, y_unit=1, lower=True),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(self.dummy_code("?{p}HICR0015{dummy}00RX"))
        self.value = float(np.max(self.channel.get_data()))
        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
        self.color = self.limits.get_limit_min_color(self.channel)


class Criterion_Chest_a3ms(_FMVSSCriterion):
    name = "Chest a3ms"
    source = "S6.3; S15.3.3"

    def define_limits(self) -> list[Limit]:
        codes = self.dummy_codes(
            "?{p}CHST003C{dummy}ACR?",
            "?{p}CHST????{dummy}ACR?",
        )
        return [
            Limit_Pass(codes, func=lambda x: 60, y_unit=Unit(g0), upper=True),
            Limit_Fail(codes, func=lambda x: 60, y_unit=Unit(g0), lower=True),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(
            self.dummy_code("?{p}CHST003C{dummy}ACRX")
        ).convert_unit(Unit(g0))
        self.value = float(np.max(self.channel.get_data()))
        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
        self.color = self.limits.get_limit_min_color(self.channel)


class Criterion_Chest_Deflection(_FMVSSCriterion):
    name = "Chest Deflection"
    source = "S6.4(b); S15.3.4"

    def define_limits(self) -> list[Limit]:
        threshold = self.dummy_threshold(male_50th=-63, female_5th=-52)
        codes = self.dummy_codes("?{p}CHST000[03]{dummy}DSX?")
        return [
            Limit_Fail(codes, func=lambda x: threshold, y_unit="mm", upper=True),
            Limit_Pass(codes, func=lambda x: threshold, y_unit="mm", lower=True),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(
            *self.dummy_codes(
                "?{p}CHST0003{dummy}DSXC",
                "?{p}CHST0000{dummy}DSXC",
            )
        ).convert_unit("mm")
        self.value = float(np.min(self.channel.get_data()))
        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
        self.color = self.limits.get_limit_min_color(self.channel)


class Criterion_Nij(_FMVSSCriterion):
    name = "Nij"
    source = "S6.6(a); S15.3.6(a)"

    def define_limits(self) -> list[Limit]:
        codes = self.dummy_codes(
            "?{p}NIJCIP00{dummy}00Y?",
            "?{p}NIJCIPCF{dummy}00Y?",
            "?{p}NIJCIPCE{dummy}00Y?",
            "?{p}NIJCIPTF{dummy}00Y?",
            "?{p}NIJCIPTE{dummy}00Y?",
        )
        return [
            Limit_Pass(codes, func=lambda x: 1.0, y_unit=1, upper=True),
            Limit_Fail(codes, func=lambda x: 1.0, y_unit=1, lower=True),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(self.dummy_code("?{p}NIJCIP00{dummy}00YB"))
        self.value = float(np.max(self.channel.get_data()))
        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
        self.color = self.limits.get_limit_min_color(self.channel)


class Criterion_Neck_Tension(_FMVSSCriterion):
    name = "Neck Tension Force"
    source = "S6.6(b); S15.3.6(b)"

    def define_limits(self) -> list[Limit]:
        threshold = self.dummy_threshold(male_50th=4170, female_5th=2620)
        codes = self.dummy_codes("?{p}NECKUP00{dummy}FOZ?")
        return [
            Limit_Pass(codes, func=lambda x: threshold, y_unit="N", upper=True),
            Limit_Fail(codes, func=lambda x: threshold, y_unit="N", lower=True),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(
            self.dummy_code("?{p}NECKUP00{dummy}FOZB")
        ).convert_unit("N")
        self.value = float(np.max(self.channel.get_data()))
        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
        self.color = self.limits.get_limit_min_color(self.channel)


class Criterion_Neck_Compression(_FMVSSCriterion):
    name = "Neck Compression Force"
    source = "S6.6(c); S15.3.6(c)"

    def define_limits(self) -> list[Limit]:
        threshold = self.dummy_threshold(male_50th=-4000, female_5th=-2520)
        codes = self.dummy_codes("?{p}NECKUP00{dummy}FOZ?")
        return [
            Limit_Fail(codes, func=lambda x: threshold, y_unit="N", upper=True),
            Limit_Pass(codes, func=lambda x: threshold, y_unit="N", lower=True),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(
            self.dummy_code("?{p}NECKUP00{dummy}FOZB")
        ).convert_unit("N")
        self.value = float(np.min(self.channel.get_data()))
        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
        self.color = self.limits.get_limit_min_color(self.channel)


class Criterion_Femur_Force(_FMVSSCriterion):
    side: str

    def define_limits(self) -> list[Limit]:
        threshold = self.dummy_threshold(male_50th=-10008, female_5th=-6805)
        codes = self.dummy_codes(f"?{{p}}FEMR{self.side}00{{dummy}}FOZ?")
        return [
            Limit_Fail(codes, func=lambda x: threshold, y_unit="N", upper=True),
            Limit_Pass(codes, func=lambda x: threshold, y_unit="N", lower=True),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(
            self.dummy_code(f"?{{p}}FEMR{self.side}00{{dummy}}FOZB")
        ).convert_unit("N")
        self.value = float(np.min(self.channel.get_data()))
        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
        self.color = self.limits.get_limit_min_color(self.channel)


class Criterion_Femur_Axial_Force(_FMVSSCriterion):
    name = "Femur Axial Force"
    source = "S6.5; S15.3.5"
    role = Role.AGGREGATE

    class Criterion_Left(Criterion_Femur_Force):
        name = "Left Femur Axial Force"
        side = "LE"

    class Criterion_Right(Criterion_Femur_Force):
        name = "Right Femur Axial Force"
        side = "RI"

    criterion_left = sub(Criterion_Left)
    criterion_right = sub(Criterion_Right)

    def calculation(self) -> None:
        self.rating = self.min_of_children()
        self.value = self.rating
        if not np.isnan(self.rating):
            self.color = Limit_Pass.color if self.rating else Limit_Fail.color


class Criterion_Occupant(_FMVSSCriterion):
    role = Role.AGGREGATE
    dummy_type: Manual[str, DUMMY_TYPE]

    criterion_containment = sub(Criterion_Containment)
    criterion_hic15 = sub(Criterion_HIC15)
    criterion_chest_a3ms = sub(Criterion_Chest_a3ms)
    criterion_chest_deflection = sub(Criterion_Chest_Deflection)
    criterion_nij = sub(Criterion_Nij)
    criterion_neck_tension = sub(Criterion_Neck_Tension)
    criterion_neck_compression = sub(Criterion_Neck_Compression)
    criterion_femur_axial_force = sub(Criterion_Femur_Axial_Force, role=Role.AGGREGATE)

    def prepare(self) -> None:
        position = self.ctx.field("p")
        detected = {
            channel.code.fine_location_3
            for channel in self.isomme.channels
            if channel.code.position == position
            and channel.code.fine_location_3 in {dummy.value for dummy in DummyType}
        }
        dummy_type = (
            next(iter(detected)) if len(detected) == 1 else DummyType.FEMALE_5TH.value
        )
        self.set_derived_input("dummy_type", dummy_type)

    def calculation(self) -> None:
        self.rating = self.min_of_children()
        self.value = self.rating
        if not np.isnan(self.rating):
            self.color = Limit_Pass.color if self.rating else Limit_Fail.color


class Overall(_FMVSSCriterion):
    name = "Overall"
    source = "S14.4-S15.3"
    role = Role.AGGREGATE

    p_driver: Manual[str, P_DRIVER]
    p_passenger: Manual[str, P_PASSENGER]

    def __init__(self, report: Report, isomme: Isomme) -> None:
        super().__init__(report, isomme)
        self.prepare()

    def prepare(self) -> None:
        p_driver = self.isomme.get_test_info("Driver position object 1")
        if p_driver is not None:
            self.set_derived_input("p_driver", str(p_driver).strip())
        self.set_derived_input("p_passenger", "1" if self.p_driver != "1" else "3")
        self.criterion_driver.prepare()
        self.criterion_passenger.prepare()

    def calculation(self) -> None:
        self.rating = self.min_of_children()
        self.value = self.rating
        if not np.isnan(self.rating):
            self.color = Limit_Pass.color if self.rating else Limit_Fail.color

    criterion_driver = sub(
        Criterion_Occupant,
        name="Driver",
        at=from_input(P_DRIVER),
        role=Role.AGGREGATE,
    )
    criterion_passenger = sub(
        Criterion_Occupant,
        name="Front Passenger",
        at=from_input(P_PASSENGER),
        role=Role.AGGREGATE,
    )


def _measurement_criteria(occupant: Criterion_Occupant) -> list[Criterion]:
    return [
        occupant.criterion_hic15,
        occupant.criterion_chest_a3ms,
        occupant.criterion_chest_deflection,
        occupant.criterion_nij,
        occupant.criterion_neck_tension,
        occupant.criterion_neck_compression,
        occupant.criterion_femur_axial_force.criterion_left,
        occupant.criterion_femur_axial_force.criterion_right,
    ]


def _compliance_criteria(occupant: Criterion_Occupant) -> list[Criterion]:
    return [occupant.criterion_containment, *_measurement_criteria(occupant), occupant]


class FMVSS_208(Report[Overall]):
    _name = "FMVSS 208 | Adult Frontal Rigid-Barrier Occupant Protection"
    _protocol = PROTOCOL_2022_10_14
    _protocols = (PROTOCOL_2022_10_14,)
    Criterion_Overall = Overall

    def __init__(
        self,
        isomme_list: list[Isomme],
        title: str | None = None,
        protocol_version: str | None = None,
    ) -> None:
        super().__init__(
            isomme_list,
            title=title or "FMVSS 208 Compliance",
            protocol_version=protocol_version,
        )

        self._available_pages = (
            Page_Cover(self),
            self.Page_Overall_Compliance(self),
            self.Page_Driver_Compliance(self),
            self.Page_Driver_Result_Values_Chart(self),
            self.Page_Driver_Values_Table(self),
            self.Page_Driver_Head_Acceleration(self),
            self.Page_Driver_Neck_Load(self),
            self.Page_Driver_Nij(self),
            self.Page_Driver_Chest(self),
            self.Page_Driver_Femur_Axial_Force(self),
            self.Page_Passenger_Compliance(self),
            self.Page_Passenger_Result_Values_Chart(self),
            self.Page_Passenger_Values_Table(self),
            self.Page_Passenger_Head_Acceleration(self),
            self.Page_Passenger_Neck_Load(self),
            self.Page_Passenger_Nij(self),
            self.Page_Passenger_Chest(self),
            self.Page_Passenger_Femur_Axial_Force(self),
        )
        self._selected_pages = list(self._available_pages)

    class Page_Compliance_Table(Page_Criterion_Rating_Table):
        @staticmethod
        def cell_text(criterion: Criterion) -> str:
            if np.isnan(criterion.rating):
                return "n/a"
            return "Pass" if criterion.rating else "Fail"

    class Page_Overall_Compliance(Page_Compliance_Table):
        report: FMVSS_208
        name = "Overall Compliance"
        title = "Overall Compliance"

        def __init__(self, report: FMVSS_208) -> None:
            super().__init__(report)
            self.criteria = {
                isomme: [
                    report.overall(isomme).criterion_driver,
                    report.overall(isomme).criterion_passenger,
                    report.overall(isomme),
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Compliance(Page_Compliance_Table):
        report: FMVSS_208
        name = "Driver Compliance"
        title = "Driver Compliance"

        def __init__(self, report: FMVSS_208) -> None:
            super().__init__(report)
            self.criteria = {
                isomme: _compliance_criteria(report.overall(isomme).criterion_driver)
                for isomme in report.isomme_list
            }

    class Page_Driver_Result_Values_Chart(Page_Criterion_Values_Chart):
        report: FMVSS_208
        name = "Driver Result Values Chart"
        title = "Driver Result Values"

        def __init__(self, report: FMVSS_208) -> None:
            super().__init__(report)
            self.criteria = {
                isomme: _measurement_criteria(report.overall(isomme).criterion_driver)
                for isomme in report.isomme_list
            }

    class Page_Driver_Values_Table(Page_Criterion_Values_Table):
        report: FMVSS_208
        name = "Driver Values Table"
        title = "Driver Values"

        def __init__(self, report: FMVSS_208) -> None:
            super().__init__(report)
            self.criteria = {
                isomme: _measurement_criteria(report.overall(isomme).criterion_driver)
                for isomme in report.isomme_list
            }

    class Page_Driver_Head_Acceleration(Page_Plot_nxn):
        report: FMVSS_208
        name = "Driver Head Acceleration"
        title = "Driver Head Acceleration"
        nrows = 2
        ncols = 2
        sharey = True

        def __init__(self, report: FMVSS_208) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{report.overall(isomme).p_driver}HEAD????"
                        f"{report.overall(isomme).criterion_driver.dummy_identifier}AC{axis}A"
                    ]
                    for axis in "XYZR"
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Neck_Load(Page_Plot_nxn):
        report: FMVSS_208
        name = "Driver Neck Load"
        title = "Driver Neck Load"
        nrows = 1
        ncols = 2
        sharey = False

        def __init__(self, report: FMVSS_208) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{report.overall(isomme).p_driver}NECKUP00"
                        f"{report.overall(isomme).criterion_driver.dummy_identifier}FOZB"
                    ],
                    [
                        f"?{report.overall(isomme).p_driver}NECKUP00"
                        f"{report.overall(isomme).criterion_driver.dummy_identifier}MOYB"
                    ],
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Nij(Page_Plot_nxn):
        report: FMVSS_208
        name = "Driver Neck NIJ"
        title = "Driver Neck NIJ"
        nrows = 2
        ncols = 2
        sharey = True

        def __init__(self, report: FMVSS_208) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{report.overall(isomme).p_driver}NIJCIP{mode}"
                        f"{report.overall(isomme).criterion_driver.dummy_identifier}00YB"
                    ]
                    for mode in ("CF", "CE", "TF", "TE")
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Chest(Page_Plot_nxn):
        report: FMVSS_208
        name = "Driver Chest"
        title = "Driver Chest"
        nrows = 1
        ncols = 2
        sharey = False

        def __init__(self, report: FMVSS_208) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{report.overall(isomme).p_driver}CHST????"
                        f"{report.overall(isomme).criterion_driver.dummy_identifier}ACRA"
                    ],
                    [
                        f"?{report.overall(isomme).p_driver}CHST000?"
                        f"{report.overall(isomme).criterion_driver.dummy_identifier}DSXC"
                    ],
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Femur_Axial_Force(Page_Plot_nxn):
        report: FMVSS_208
        name = "Driver Femur Axial Force"
        title = "Driver Femur Axial Force"
        nrows = 1
        ncols = 2
        sharey = True

        def __init__(self, report: FMVSS_208) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{report.overall(isomme).p_driver}FEMRLE00"
                        f"{report.overall(isomme).criterion_driver.dummy_identifier}FOZB"
                    ],
                    [
                        f"?{report.overall(isomme).p_driver}FEMRRI00"
                        f"{report.overall(isomme).criterion_driver.dummy_identifier}FOZB"
                    ],
                ]
                for isomme in report.isomme_list
            }

    class Page_Passenger_Compliance(Page_Compliance_Table):
        report: FMVSS_208
        name = "Front Passenger Compliance"
        title = "Front Passenger Compliance"

        def __init__(self, report: FMVSS_208) -> None:
            super().__init__(report)
            self.criteria = {
                isomme: _compliance_criteria(report.overall(isomme).criterion_passenger)
                for isomme in report.isomme_list
            }

    class Page_Passenger_Result_Values_Chart(Page_Criterion_Values_Chart):
        report: FMVSS_208
        name = "Front Passenger Result Values Chart"
        title = "Front Passenger Result Values"

        def __init__(self, report: FMVSS_208) -> None:
            super().__init__(report)
            self.criteria = {
                isomme: _measurement_criteria(
                    report.overall(isomme).criterion_passenger
                )
                for isomme in report.isomme_list
            }

    class Page_Passenger_Values_Table(Page_Criterion_Values_Table):
        report: FMVSS_208
        name = "Front Passenger Values Table"
        title = "Front Passenger Values"

        def __init__(self, report: FMVSS_208) -> None:
            super().__init__(report)
            self.criteria = {
                isomme: _measurement_criteria(
                    report.overall(isomme).criterion_passenger
                )
                for isomme in report.isomme_list
            }

    class Page_Passenger_Head_Acceleration(Page_Plot_nxn):
        report: FMVSS_208
        name = "Front Passenger Head Acceleration"
        title = "Front Passenger Head Acceleration"
        nrows = 2
        ncols = 2
        sharey = True

        def __init__(self, report: FMVSS_208) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{report.overall(isomme).p_passenger}HEAD????"
                        f"{report.overall(isomme).criterion_passenger.dummy_identifier}AC{axis}A"
                    ]
                    for axis in "XYZR"
                ]
                for isomme in report.isomme_list
            }

    class Page_Passenger_Neck_Load(Page_Plot_nxn):
        report: FMVSS_208
        name = "Front Passenger Neck Load"
        title = "Front Passenger Neck Load"
        nrows = 1
        ncols = 2
        sharey = False

        def __init__(self, report: FMVSS_208) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{report.overall(isomme).p_passenger}NECKUP00"
                        f"{report.overall(isomme).criterion_passenger.dummy_identifier}FOZB"
                    ],
                    [
                        f"?{report.overall(isomme).p_passenger}NECKUP00"
                        f"{report.overall(isomme).criterion_passenger.dummy_identifier}MOYB"
                    ],
                ]
                for isomme in report.isomme_list
            }

    class Page_Passenger_Nij(Page_Plot_nxn):
        report: FMVSS_208
        name = "Front Passenger Neck NIJ"
        title = "Front Passenger Neck NIJ"
        nrows = 2
        ncols = 2
        sharey = True

        def __init__(self, report: FMVSS_208) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{report.overall(isomme).p_passenger}NIJCIP{mode}"
                        f"{report.overall(isomme).criterion_passenger.dummy_identifier}00YB"
                    ]
                    for mode in ("CF", "CE", "TF", "TE")
                ]
                for isomme in report.isomme_list
            }

    class Page_Passenger_Chest(Page_Plot_nxn):
        report: FMVSS_208
        name = "Front Passenger Chest"
        title = "Front Passenger Chest"
        nrows = 1
        ncols = 2
        sharey = False

        def __init__(self, report: FMVSS_208) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{report.overall(isomme).p_passenger}CHST????"
                        f"{report.overall(isomme).criterion_passenger.dummy_identifier}ACRA"
                    ],
                    [
                        f"?{report.overall(isomme).p_passenger}CHST000?"
                        f"{report.overall(isomme).criterion_passenger.dummy_identifier}DSXC"
                    ],
                ]
                for isomme in report.isomme_list
            }

    class Page_Passenger_Femur_Axial_Force(Page_Plot_nxn):
        report: FMVSS_208
        name = "Front Passenger Femur Axial Force"
        title = "Front Passenger Femur Axial Force"
        nrows = 1
        ncols = 2
        sharey = True

        def __init__(self, report: FMVSS_208) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{report.overall(isomme).p_passenger}FEMRLE00"
                        f"{report.overall(isomme).criterion_passenger.dummy_identifier}FOZB"
                    ],
                    [
                        f"?{report.overall(isomme).p_passenger}FEMRRI00"
                        f"{report.overall(isomme).criterion_passenger.dummy_identifier}FOZB"
                    ],
                ]
                for isomme in report.isomme_list
            }


__all__ = ["DummyType", "FMVSS_208", "Overall"]
