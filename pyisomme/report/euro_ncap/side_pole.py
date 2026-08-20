from __future__ import annotations

import logging
from typing import Any

import numpy as np

from pyisomme.isomme import Isomme
from pyisomme.limit import Limit
from pyisomme.report.criterion import Criterion, Role, sub
from pyisomme.report.ctx import from_input
from pyisomme.report.euro_ncap.limits import (
    Limit_A,
    Limit_C,
    Limit_G,
    Limit_M,
    Limit_P,
    Limit_W,
)
from pyisomme.report.euro_ncap.protocols import PROTOCOL_9_3
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

P = manual(
    "1",
    source="test report",
    doc=(
        "Channel-code position of the struck-side occupant — the only occupant "
        "§5 assesses. Defaults to the 'Driver position object 1' test-info field "
        "when the test carries it."
    ),
)


class Overall(Criterion):
    name = "Overall"
    role = Role.AGGREGATE
    max_rating = 16.0
    source = "§5"
    p: Manual[str, P]

    def __init__(self, report: Report, isomme: Isomme) -> None:
        super().__init__(report, isomme)
        # Also at construction: the pages read `p` when the report is built.
        self.prepare()

    def prepare(self) -> None:
        """Take the struck-side position from the test info before the occupant reads it."""
        p = self.isomme.get_test_info("Driver position object 1")
        if p is not None:
            self.set_derived_input("p", str(p).strip())

    def calculation(self) -> None:
        self.rating = np.sum(
            [
                self.criterion_head.rating,
                self.criterion_chest.rating,
                self.criterion_abdomen.rating,
                self.criterion_pelvis.rating,
            ]
        )
        self.rating = float(
            np.interp(self.rating, [0, 16], [0, 16], left=0, right=np.nan)
        )

        # Modifier — §5.2.3 and §5.2.5 apply to the overall test score.

        self.rating += np.sum(
            [
                self.criterion_side_head_protection_device.rating,
                self.criterion_incorrect_airbag_deployment.rating,
                self.criterion_door_opening_during_impact.rating,
            ]
        )

        # A modifier must not drive the load case below zero.
        self.rating = float(np.max([0.0, self.rating]))

    class Criterion_SideHeadProtectionDevice(Criterion):
        name = "Modifier for Side Head Protection Device"
        role = Role.MODIFIER
        source = "§5.2.3"
        head_protection_device_insufficient_front: Manual[
            bool,
            manual(
                False,
                source="geometric assessment",
                doc=(
                    "The head protection device does not cover the front seat positions "
                    "sufficiently, on the worst performing side. −2 points."
                ),
            ),
        ]
        head_protection_device_insufficient_rear: Manual[
            bool,
            manual(
                False,
                source="geometric assessment",
                doc=(
                    "The head protection device does not cover the rear seat positions "
                    "sufficiently, on the worst performing side. −2 points."
                ),
            ),
        ]

        def calculation(self) -> None:
            self.value = int(self.head_protection_device_insufficient_front) + int(
                self.head_protection_device_insufficient_rear
            )
            self.rating = -2.0 * self.value

    class Criterion_IncorrectAirbagDeployment(Criterion):
        name = "Modifier for Incorrect Airbag Deployment"
        role = Role.MODIFIER
        source = "§5.2.4"
        number_of_body_regions_with_incorrect_airbag_deployment: Manual[
            int,
            manual(
                0,
                source="test report",
                doc=(
                    "How many body regions (head, chest, abdomen, pelvis) an incorrectly "
                    "deployed airbag was intended to protect. −1 point each."
                ),
            ),
        ]

        def calculation(self) -> None:
            self.value = self.number_of_body_regions_with_incorrect_airbag_deployment
            self.rating = (
                -1.0 * self.number_of_body_regions_with_incorrect_airbag_deployment
            )

    class Criterion_DoorOpeningDuringImpact(Criterion):
        name = "Door Opening During Impact"
        source = "§5.2.5"
        number_of_door_openings_during_impact: Manual[
            int,
            manual(
                0,
                source="test report",
                doc=(
                    "How many doors, tailgates or moveable roofs opened during the impact. "
                    "−1 point each."
                ),
            ),
        ]

        def calculation(self) -> None:
            self.value = self.number_of_door_openings_during_impact
            self.rating = -1.0 * self.number_of_door_openings_during_impact

    class Criterion_Head(Criterion):
        name = "Head"
        max_rating = 4.0
        source = "§5.1.1.2"

        def calculation(self) -> None:

            self.rating = np.min(
                [
                    self.criterion_hic_15.rating,
                    self.criterion_head_acceleration.rating,
                    self.criterion_direct_head_contact_with_the_pole.rating,
                ]
            )

        class Criterion_HIC_15(Criterion):
            name = "HIC 15"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}HICR0015??00RX", "?{p}HICRCG15??00RX")
                return [
                    Limit_G(codes, func=lambda x: 700.000, y_unit=1, upper=True),
                    Limit_C(codes, func=lambda x: 700.000, y_unit=1, lower=True),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(
                    self.ctx.code("?{p}HICR0015??00RX"),
                    self.ctx.code("?{p}HICRCG15??00RX"),
                )
                self.value = self.channel.get_data()[0]
                self.rating = self.limits.get_limit_min_rating(
                    self.channel, interpolate=False
                )
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Head_Peak_Acceleration(Criterion):
            #: §5.1.1.2 caps the pole test on the *peak* resultant head acceleration.
            #: The barrier test uses the 3 ms exceedance instead (§5.1.1.1), so this
            #: class is deliberately not shared with EuroNCAP_Side_Barrier.
            name = "Head Peak Acceleration"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}HEAD??00??ACR?", "?{p}HEADCG00??ACR?")
                return [
                    Limit_G(codes, func=lambda x: 80.000, y_unit=Unit(g0), upper=True),
                    Limit_C(codes, func=lambda x: 80.000, y_unit=Unit(g0), lower=True),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(
                    self.ctx.code("?{p}HEAD??00??ACRA"),
                    self.ctx.code("?{p}HEADCG00??ACRA"),
                )
                self.value = np.max(self.channel.get_data(unit=g0))
                self.rating = self.limits.get_limit_min_rating(
                    self.channel, interpolate=False
                )
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_DirectHeadContactWithThePole(Criterion):
            name = "Direct head contact with the pole"
            source = "§5.1.1.2"
            direct_head_contact_with_the_pole: Manual[
                bool,
                manual(
                    False,
                    source="video",
                    doc=(
                        "Direct head contact with the pole. Caps the head box (−inf → 0 points)."
                    ),
                ),
            ]

            def calculation(self) -> None:
                self.value = self.direct_head_contact_with_the_pole
                self.rating = -np.inf if self.direct_head_contact_with_the_pole else 4

        criterion_hic_15 = sub(Criterion_HIC_15)
        criterion_head_acceleration = sub(Criterion_Head_Peak_Acceleration)
        criterion_direct_head_contact_with_the_pole = sub(
            Criterion_DirectHeadContactWithThePole
        )

    class Criterion_Chest(Criterion):
        name = "Chest"
        max_rating = 4.0
        source = "§5.1.2"

        def calculation(self) -> None:

            self.rating = np.min(
                [
                    self.criterion_chest_lateral_compression.rating,
                    self.criterion_chest_lateral_vc.rating,
                    self.criterion_shoulder_lateral_force.rating,
                ]
            )

        class Criterion_Chest_Lateral_Compression(Criterion):
            name = "Chest Lateral Compression"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}TRRI??0[0123]??DSY?")
                return [
                    Limit_C(codes, func=lambda x: -55.000, y_unit="mm", upper=True),
                    Limit_P(codes, func=lambda x: -50.000, y_unit="mm", upper=True),
                    Limit_W(codes, func=lambda x: -42.667, y_unit="mm", upper=True),
                    Limit_M(codes, func=lambda x: -35.333, y_unit="mm", upper=True),
                    Limit_A(codes, func=lambda x: -28.000, y_unit="mm", upper=True),
                    Limit_G(codes, func=lambda x: -28.000, y_unit="mm", lower=True),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(
                    self.ctx.code("?{p}TRRI??00??DSYC")
                ).convert_unit("mm")
                self.value = np.min(self.channel.get_data())
                self.rating = self.limits.get_limit_min_rating(
                    self.channel, interpolate=True
                )
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Chest_Lateral_VC(Criterion):
            name = "Modifier Chest Lateral Viscous Criterion"
            role = Role.MODIFIER
            source = "§5.2.2"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}VCCR??????VEYC")
                return [
                    Limit_P(codes, func=lambda x: -1, y_unit="m/s", upper=True),
                    Limit_G(codes, func=lambda x: -1, y_unit="m/s", lower=True),
                    Limit_G(codes, func=lambda x: 1, y_unit="m/s", upper=True),
                    Limit_P(codes, func=lambda x: 1, y_unit="m/s", lower=True),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(self.ctx.code("?{p}VCCR??00??VEYC"))
                self.value = self.channel.get_data()[
                    np.argmax(np.abs(self.channel.get_data()))
                ]
                self.rating = self.limits.get_limit_min_rating(
                    self.channel, interpolate=False
                )
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Shoulder_Lateral_Force(Criterion):
            name = "Modifier Shoulder Lateral Force"
            role = Role.MODIFIER
            source = "§5.2.1"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes(
                    "?{p}SHLD0000??FOY?", "?{p}SHLDLE00??FOY?", "?{p}SHLDRI00??FOY?"
                )
                return [
                    Limit_P(codes, func=lambda x: -3, y_unit="kN", upper=True),
                    Limit_G(codes, func=lambda x: -3, y_unit="kN", lower=True),
                    Limit_G(codes, func=lambda x: 3, y_unit="kN", upper=True),
                    Limit_P(codes, func=lambda x: 3.0, y_unit="kN", lower=True),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(
                    self.ctx.code("?{p}SHLD0000??FOYB")
                ).convert_unit("kN")
                self.value = self.channel.get_data()[
                    np.argmax(np.abs(self.channel.get_data()))
                ]
                self.rating = self.limits.get_limit_min_rating(
                    self.channel, interpolate=False
                )
                self.color = self.limits.get_limit_min_color(self.channel)

        criterion_chest_lateral_compression = sub(Criterion_Chest_Lateral_Compression)
        criterion_chest_lateral_vc = sub(Criterion_Chest_Lateral_VC)
        criterion_shoulder_lateral_force = sub(Criterion_Shoulder_Lateral_Force)

    class Criterion_Abdomen(Criterion):
        name = "Abdomen"
        max_rating = 4.0
        source = "§5.1.3"

        def calculation(self) -> None:

            self.rating = np.min(
                [
                    self.criterion_abdomen_lateral_compression.rating,
                    self.criterion_abdomen_lateral_vc.rating,
                ]
            )

        class Criterion_Abdomen_Lateral_Compression(Criterion):
            name = "Abdomen Lateral Compression"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}ABRI??0[012]??DSY?")
                return [
                    Limit_C(codes, func=lambda x: -65, y_unit="mm", upper=True),
                    Limit_P(codes, func=lambda x: -65, y_unit="mm"),
                    Limit_W(codes, func=lambda x: -59, y_unit="mm", upper=True),
                    Limit_M(codes, func=lambda x: -53, y_unit="mm", upper=True),
                    Limit_A(codes, func=lambda x: -47, y_unit="mm", upper=True),
                    Limit_G(codes, func=lambda x: -47, y_unit="mm", lower=True),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(
                    self.ctx.code("?{p}ABRI??00??DSYC")
                ).convert_unit("mm")
                self.value = np.min(self.channel.get_data())
                self.rating = self.limits.get_limit_min_rating(
                    self.channel, interpolate=True
                )
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Abdomen_Lateral_VC(Criterion):
            name = "Modifier Abdomen Lateral Viscous Criterion"
            role = Role.MODIFIER
            source = "§5.2.2"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}VCAR??????VEYC")
                return [
                    Limit_P(codes, func=lambda x: -1, y_unit="m/s", upper=True),
                    Limit_G(codes, func=lambda x: -1, y_unit="m/s", lower=True),
                    Limit_G(codes, func=lambda x: 1, y_unit="m/s", upper=True),
                    Limit_P(codes, func=lambda x: 1, y_unit="m/s", lower=True),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(self.ctx.code("?{p}VCAR??00??VEYC"))
                self.value = self.channel.get_data()[
                    np.argmax(np.abs(self.channel.get_data()))
                ]
                self.rating = self.limits.get_limit_min_rating(
                    self.channel, interpolate=False
                )
                self.color = self.limits.get_limit_min_color(self.channel)

        criterion_abdomen_lateral_compression = sub(
            Criterion_Abdomen_Lateral_Compression
        )
        criterion_abdomen_lateral_vc = sub(Criterion_Abdomen_Lateral_VC)

    class Criterion_Pelvis(Criterion):
        name = "Pelvis"
        max_rating = 4.0
        source = "§5.1.4"

        def calculation(self) -> None:

            self.rating = self.criterion_pubic_symphysis_force.rating

        class Criterion_Pubic_Symphysis_Force(Criterion):
            name = "Pubic Symphysis Force"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}PUBC0000??FOY?")
                return [
                    Limit_C(codes, func=lambda x: -2.800, y_unit="kN", upper=True),
                    Limit_P(codes, func=lambda x: -2.800, y_unit="kN"),
                    Limit_W(codes, func=lambda x: -2.433, y_unit="kN", upper=True),
                    Limit_M(codes, func=lambda x: -2.067, y_unit="kN", upper=True),
                    Limit_A(codes, func=lambda x: -1.700, y_unit="kN", upper=True),
                    Limit_G(codes, func=lambda x: -1.700, y_unit="kN", lower=True),
                    Limit_G(codes, func=lambda x: 1.700, y_unit="kN", upper=True),
                    Limit_A(codes, func=lambda x: 1.700, y_unit="kN", lower=True),
                    Limit_M(codes, func=lambda x: 2.067, y_unit="kN", lower=True),
                    Limit_W(codes, func=lambda x: 2.433, y_unit="kN", lower=True),
                    Limit_P(codes, func=lambda x: 2.800, y_unit="kN"),
                    Limit_C(codes, func=lambda x: 2.800, y_unit="kN", lower=True),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(
                    self.ctx.code("?{p}PUBC0000??FOYB")
                ).convert_unit("kN")
                self.value = self.channel.get_data()[
                    np.argmax(np.abs(self.channel.get_data()))
                ]
                self.rating = self.limits.get_limit_min_rating(
                    self.channel, interpolate=True
                )
                self.color = self.limits.get_limit_min_color(self.channel)

        criterion_pubic_symphysis_force = sub(Criterion_Pubic_Symphysis_Force)

    criterion_head = sub(Criterion_Head, at=from_input(P), role=Role.AGGREGATE)
    criterion_chest = sub(Criterion_Chest, at=from_input(P), role=Role.AGGREGATE)
    criterion_abdomen = sub(Criterion_Abdomen, at=from_input(P), role=Role.AGGREGATE)
    criterion_pelvis = sub(Criterion_Pelvis, at=from_input(P), role=Role.AGGREGATE)
    criterion_side_head_protection_device = sub(
        Criterion_SideHeadProtectionDevice, role=Role.MODIFIER
    )
    criterion_incorrect_airbag_deployment = sub(
        Criterion_IncorrectAirbagDeployment, role=Role.MODIFIER
    )
    criterion_door_opening_during_impact = sub(
        Criterion_DoorOpeningDuringImpact, role=Role.MODIFIER
    )


class EuroNCAP_Side_Pole(Report[Overall]):
    _name = "Euro NCAP | Pole Side Impact at 32 km/h"
    _protocol = PROTOCOL_9_3
    _protocols = (PROTOCOL_9_3,)
    Criterion_Overall = Overall

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._available_pages = (
            Page_Cover(self),
            self.Page_Values_Chart(self),
            self.Page_Rating_Table(self),
            self.Page_Values_Table(self),
            self.Page_Head_Acceleration(self),
            self.Page_Shoulder_Lateral_Force(self),
            self.Page_Chest_Lateral_Compression(self),
            self.Page_Chest_Lateral_VC(self),
            self.Page_Abdomen_Lateral_Compression(self),
            self.Page_Abdomen_Lateral_VC(self),
            self.Page_Pubic_Symphysis_Force(self),
        )
        self._selected_pages = list(self._available_pages)

    class Page_Values_Chart(Page_Criterion_Values_Chart):
        name = "Values Chart"
        title = "Values"

        def __init__(self, report: Report) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_head.criterion_hic_15,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_head.criterion_head_acceleration,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_chest.criterion_chest_lateral_compression,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_chest.criterion_chest_lateral_vc,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_chest.criterion_shoulder_lateral_force,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_abdomen.criterion_abdomen_lateral_compression,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_abdomen.criterion_abdomen_lateral_vc,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_pelvis.criterion_pubic_symphysis_force,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Values_Table(Page_Criterion_Values_Table):
        name = "Values Table"
        title = "Values"

        def __init__(self, report: Report) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_head.criterion_hic_15,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_head.criterion_head_acceleration,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_chest.criterion_chest_lateral_compression,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_chest.criterion_chest_lateral_vc,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_chest.criterion_shoulder_lateral_force,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_abdomen.criterion_abdomen_lateral_compression,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_abdomen.criterion_abdomen_lateral_vc,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_pelvis.criterion_pubic_symphysis_force,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Rating_Table(Page_Criterion_Rating_Table):
        name: str = "Rating Table"
        title: str = "Rating"

        def __init__(self, report: Report) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[isomme].criterion_head,
                    self.report.criterion_overall[isomme].criterion_chest,
                    self.report.criterion_overall[isomme].criterion_abdomen,
                    self.report.criterion_overall[isomme].criterion_pelvis,
                    self.report.criterion_overall[isomme],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Head_Acceleration(Page_Plot_nxn):
        name: str = "Head Acceleration"
        title: str = "Head Acceleration"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: Report) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{self.report.criterion_overall[isomme].p}HEAD??????AC{xyzr}A"]
                    for xyzr in "XYZR"
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Chest_Lateral_Compression(Page_Plot_nxn):
        name: str = "Chest Lateral Compression"
        title: str = "Chest Lateral Compression"
        nrows: int = 3
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: Report) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{self.report.criterion_overall[isomme].p}TRRILE01??DSYC"],
                    [f"?{self.report.criterion_overall[isomme].p}TRRIRI01??DSYC"],
                    [f"?{self.report.criterion_overall[isomme].p}TRRILE02??DSYC"],
                    [f"?{self.report.criterion_overall[isomme].p}TRRIRI02??DSYC"],
                    [f"?{self.report.criterion_overall[isomme].p}TRRILE03??DSYC"],
                    [f"?{self.report.criterion_overall[isomme].p}TRRIRI04??DSYC"],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Chest_Lateral_VC(Page_Plot_nxn):
        name: str = "Chest Lateral VC"
        title: str = "Chest Lateral VC"
        nrows: int = 3
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: Report) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{self.report.criterion_overall[isomme].p}VCCRLE01??DSYC"],
                    [f"?{self.report.criterion_overall[isomme].p}VCCRRI01??DSYC"],
                    [f"?{self.report.criterion_overall[isomme].p}VCCRLE02??DSYC"],
                    [f"?{self.report.criterion_overall[isomme].p}VCCRRI02??DSYC"],
                    [f"?{self.report.criterion_overall[isomme].p}VCCRLE03??DSYC"],
                    [f"?{self.report.criterion_overall[isomme].p}VCCRRI04??DSYC"],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Shoulder_Lateral_Force(Page_Plot_nxn):
        name = "Shoulder Lateral Force"
        title = "Shoulder Lateral Force"
        nrows = 1
        ncols = 2
        sharey = True

        def __init__(self, report: Report) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{self.report.criterion_overall[isomme].p}SHLDLE00??FOYC"],
                    [f"?{self.report.criterion_overall[isomme].p}SHLDRI00??FOYC"],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Abdomen_Lateral_Compression(Page_Plot_nxn):
        name: str = "Abdomen Lateral Compression"
        title: str = "Abdomen Lateral Compression"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: Report) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{self.report.criterion_overall[isomme].p}ABRILE01??DSYC"],
                    [f"?{self.report.criterion_overall[isomme].p}ABRIRI01??DSYC"],
                    [f"?{self.report.criterion_overall[isomme].p}ABRILE02??DSYC"],
                    [f"?{self.report.criterion_overall[isomme].p}ABRIRI03??DSYC"],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Abdomen_Lateral_VC(Page_Plot_nxn):
        name: str = "Abdomen Lateral VC"
        title: str = "Abdomen Lateral VC"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: Report) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{self.report.criterion_overall[isomme].p}VCARLE01??VEYC"],
                    [f"?{self.report.criterion_overall[isomme].p}VCARRI01??VEYC"],
                    [f"?{self.report.criterion_overall[isomme].p}VCARLE02??VEYC"],
                    [f"?{self.report.criterion_overall[isomme].p}VCARRI03??VEYC"],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Pubic_Symphysis_Force(Page_Plot_nxn):
        name: str = "Pubic Symphysis Force"
        title: str = "Pubic Symphysis Force"

        def __init__(self, report: Report) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [[f"?{self.report.criterion_overall[isomme].p}PUBC0000??FOYB"]]
                for isomme in self.report.isomme_list
            }
