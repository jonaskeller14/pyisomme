from __future__ import annotations

import logging
from typing import Any

import numpy as np
from matplotlib.colors import to_rgb
from matplotlib.figure import Figure

from pyisomme.calculate import calculate_olc
from pyisomme.isomme import Isomme
from pyisomme.limit import Limit
from pyisomme.limits import Limits
from pyisomme.report.criterion import Criterion, Role, sub
from pyisomme.report.criterion_result import CriterionResult
from pyisomme.report.ctx import from_input
from pyisomme.report.euro_ncap.frontal_50kmh import (
    Criterion_Chest_VC,
    Criterion_Head_a3ms,
    Criterion_HIC_15,
    Criterion_ShoulderBeltLoad,
    Criterion_Submarining,
    Criterion_UnstableAirbagContact as Criterion_UnstableAirbagContact_F50,
    EuroNCAP_Frontal_50kmh,
    Overall as Overall_Frontal_50kmh,
)
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
    Page_Line_Table,
    Page_OLC,
    Page_Plot_nxn,
)
from pyisomme.report.report import Report
from pyisomme.unit import Unit, g0

logger = logging.getLogger(__name__)

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
        "Channel-code position of the front passenger. Derived from p_driver "
        "('1' for a right-hand-drive test) unless set explicitly."
    ),
)


class Criterion_UnstableAirbagContact(Criterion_UnstableAirbagContact_F50):
    source = "§3.2.1.1"


class Criterion_HazardousAirbagDeployment(
    Overall_Frontal_50kmh.Criterion_Driver.Criterion_Head.Criterion_HazardousAirbagDeployment
):
    source = "§3.2.1.1"


class Criterion_IncorrectAirbagDeployment(
    Overall_Frontal_50kmh.Criterion_Driver.Criterion_Head.Criterion_IncorrectAirbagDeployment
):
    source = "§3.2.1.1"


class Criterion_VariableContact(Criterion):
    name = "Modifier for Variable Contact"
    role = Role.MODIFIER
    source = "§3.2.1.4"
    variable_contact_left: Manual[
        bool,
        manual(
            False,
            source="knee mapping",
            doc=(
                "Over the left knee's contact area, femur loads above 3.8 kN and/or "
                "knee slider displacements above 6 mm would be expected. −1 point."
            ),
        ),
    ]
    variable_contact_right: Manual[
        bool,
        manual(
            False,
            source="knee mapping",
            doc=(
                "Over the right knee's contact area, femur loads above 3.8 kN and/or "
                "knee slider displacements above 6 mm would be expected. −1 point."
            ),
        ),
    ]

    def calculation(self) -> CriterionResult:
        value = int(self.variable_contact_left) + int(self.variable_contact_right)
        rating = -1.0 * value
        return CriterionResult(
            channel=None,
            value=value,
            rating=rating,
            color=None,
        )


class Criterion_ConcentratedLoading(Criterion):
    name = "Modifier for Concentrated Loading"
    role = Role.MODIFIER
    source = "§3.2.1.4"
    concentrated_loading_left: Manual[
        bool,
        manual(
            False,
            source="knee mapping",
            doc=(
                "Structures in the left knee impact area could concentrate forces on "
                "part of the knee. −1 point."
            ),
        ),
    ]
    concentrated_loading_right: Manual[
        bool,
        manual(
            False,
            source="knee mapping",
            doc=(
                "Structures in the right knee impact area could concentrate forces on "
                "part of the knee. −1 point."
            ),
        ),
    ]

    def calculation(self) -> CriterionResult:
        value = int(self.concentrated_loading_left) + int(
            self.concentrated_loading_right
        )
        rating = -1.0 * value
        return CriterionResult(
            channel=None,
            value=value,
            rating=rating,
            color=None,
        )


class Criterion_Femur_Compression(Criterion):
    name = "Femur Compression"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}FEMR??00??FOZ?")
        return [
            Limit_G(
                codes, func=lambda x: -3.8000, y_unit="kN", x_unit="ms", lower=True
            ),
            Limit_A(
                codes, func=lambda x: -3.8000, y_unit="kN", x_unit="ms", upper=True
            ),
            Limit_M(
                codes,
                func=lambda x: np.interp(x, [0, 10], [-5.557, -5.053]),
                y_unit="kN",
                x_unit="ms",
                upper=True,
            ),
            Limit_W(
                codes,
                func=lambda x: np.interp(x, [0, 10], [-7.313, -6.307]),
                y_unit="kN",
                x_unit="ms",
                upper=True,
            ),
            Limit_P(
                codes,
                func=lambda x: np.interp(x, [0, 10], [-9.070, -7.560]),
                y_unit="kN",
                x_unit="ms",
                upper=True,
            ),
        ]

    def calculation(self) -> CriterionResult:
        channel = self.require_channel(
            self.ctx.code("?{p}FEMR0000??FOZB")
        ).convert_unit("kN")
        value = self.limits.get_limit_min_y(channel)
        rating = self.limits.get_limit_min_rating(channel)
        color = self.limits.get_limit_min_color(channel)
        return CriterionResult(
            channel=channel,
            value=value,
            rating=rating,
            color=color,
        )


class Criterion_Knee_Slider_Compression(Criterion):
    name = "Knee Slider Compression"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}KNSL??00??DSX?")
        return [
            Limit_P(codes, func=lambda x: -15.0, y_unit="mm", upper=True),
            Limit_W(codes, func=lambda x: -12.0, y_unit="mm", upper=True),
            Limit_M(codes, func=lambda x: -9.00, y_unit="mm", upper=True),
            Limit_A(codes, func=lambda x: -6.00, y_unit="mm", upper=True),
            Limit_G(codes, func=lambda x: -6.00, y_unit="mm", lower=True),
        ]

    def calculation(self) -> CriterionResult:
        channel = self.require_channel(
            self.ctx.code("?{p}KNSL0000??DSXC")
        ).convert_unit("mm")
        value = np.min(channel.get_data())
        rating = self.limits.get_limit_min_rating(channel)
        color = self.limits.get_limit_min_color(channel)
        return CriterionResult(
            channel=channel,
            value=value,
            rating=rating,
            color=color,
        )


class Criterion_Tibia_Index(Criterion):
    name = "Tibia Index"
    source = "§3.1.5.1"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}TIIN??00??000?")
        return [
            Limit_G(codes, func=lambda x: 0.4, y_unit="1", upper=True),
            Limit_A(codes, func=lambda x: 0.4, y_unit="1", lower=True),
            Limit_M(codes, func=lambda x: 0.7, y_unit="1", lower=True),
            Limit_W(codes, func=lambda x: 1.0, y_unit="1", lower=True),
            Limit_P(codes, func=lambda x: 1.3, y_unit="1", lower=True),
        ]

    def calculation(self) -> CriterionResult:
        channel = self.require_channel(self.ctx.code("?{p}TIIN0000??000B"))
        value = np.max(channel.get_data())
        rating = self.limits.get_limit_min_rating(channel)
        color = self.limits.get_limit_min_color(channel)
        return CriterionResult(
            channel=channel,
            value=value,
            rating=rating,
            color=color,
        )


class Criterion_Tibia_Compression(Criterion):
    name = "Tibia Compression"
    source = "§3.1.5.1"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}TIBI??????FOZ?")
        return [
            Limit_P(codes, func=lambda x: -8, y_unit="kN", upper=True),
            Limit_W(codes, func=lambda x: -6, y_unit="kN", upper=True),
            Limit_M(codes, func=lambda x: -4, y_unit="kN", upper=True),
            Limit_A(codes, func=lambda x: -2, y_unit="kN", upper=True),
            Limit_G(codes, func=lambda x: -2, y_unit="kN", lower=True),
        ]

    def calculation(self) -> CriterionResult:
        channel = self.require_channel(
            self.ctx.code("?{p}TIBI0000??FOZB")
        ).convert_unit("kN")
        value = np.min(channel.get_data())
        rating = self.limits.get_limit_min_rating(channel, interpolate=True)
        color = self.limits.get_limit_min_color(channel)
        return CriterionResult(
            channel=channel,
            value=value,
            rating=rating,
            color=color,
        )


class Overall(Criterion):
    report: EuroNCAP_Frontal_MPDB
    role = Role.AGGREGATE
    name: str = "Overall"
    #: §3.4: the four body regions are scored on the worse of driver and passenger
    #: (16 points), and that sum is halved. The compatibility penalty of §3.3 and
    #: the door modifier then apply to this 8-point test score.
    max_rating = 8.0
    source = "§3"
    p_driver: Manual[str, P_DRIVER]
    p_passenger: Manual[str, P_PASSENGER]

    def __init__(self, report: Report[Any], isomme: Isomme) -> None:
        super().__init__(report, isomme)
        # Also at construction, not only before every calculate(): the pages build
        # their channel patterns from p_driver when the report is constructed.
        self.prepare()

    def prepare(self) -> None:
        """Fill the seating positions before the occupants read them (F15)."""
        p_driver = self.isomme.get_test_info("Driver position object 1")
        if p_driver is not None:
            self.set_derived_input("p_driver", str(p_driver).strip())
        self.derive_positions()

    def derive_positions(self) -> None:
        """Fill the passenger position from ``p_driver`` — see ``Criterion.set_derived_input``."""
        self.set_derived_input("p_passenger", "1" if self.p_driver != "1" else "3")

    def calculation(self) -> CriterionResult:
        rating = np.sum(
            [
                self.min_of(
                    self.criterion_driver.criterion_head_neck,
                    self.criterion_passenger.criterion_head_neck,
                ),
                self.min_of(
                    self.criterion_driver.criterion_chest_abdomen,
                    self.criterion_passenger.criterion_chest,
                ),
                self.min_of(
                    self.criterion_driver.criterion_knee_femur_pelvis,
                    self.criterion_passenger.criterion_knee_femur_pelvis,
                ),
                self.min_of(
                    self.criterion_driver.criterion_lowerleg_foot_ankle,
                    self.criterion_passenger.criterion_lowerleg,
                ),
            ]
        )

        # Capping (-np.inf) leads to 0 points. More than 16 points should not be possible if sub-criteria defined correctly
        rating = float(np.interp(rating, [0, 16], [0, 16], left=0, right=np.nan))
        # §3.4: "This score is halved with a total achievable score of 8 points."
        # TODO(test): no golden fixture reaches this line with a number — the MPDB
        #   driver is nan in all three, so Overall is nan. Verified by hand only
        #   (4/4/4/4 on both occupants -> 8.0; -8 compatibility -> 0.0). Add a
        #   fixture-free regression test once Step 7's Ctx makes pinning a region's
        #   rating cheap.
        rating /= 2

        # Modifier — §3.3 applies the compatibility penalty to the test score, so
        # both modifiers land on the halved scale.

        rating += np.sum(
            [
                self.criterion_door_opening_during_impact.result.rating,
                self.criterion_compatibility_modifier.result.rating,
            ]
        )

        # A modifier must not drive the load case below zero.
        rating = float(np.max([0.0, rating]))
        return CriterionResult(
            channel=None,
            value=rating,
            rating=rating,
            color=None,
        )

    class Criterion_Driver(Criterion):
        role = Role.AGGREGATE
        name = "Driver"
        max_rating, aggregation = 16.0, "sum"

        def calculation(self) -> CriterionResult:

            rating = np.sum(
                [
                    self.criterion_head_neck.result.rating,
                    self.criterion_chest_abdomen.result.rating,
                    self.criterion_knee_femur_pelvis.result.rating,
                    self.criterion_lowerleg_foot_ankle.result.rating,
                ]
            )
            return CriterionResult(
                channel=None,
                value=rating,
                rating=rating,
                color=None,
            )

        class Criterion_Head_Neck(Criterion):
            role = Role.AGGREGATE
            name = "Head & Neck"
            #: §3.4 groups head and neck into one 4-point body region.
            max_rating = 4.0
            source = "§3.1.1"

            steering_wheel_airbag_exists: Manual[
                bool,
                manual(
                    True,
                    source="test report",
                    doc=(
                        "Is a steering-wheel airbag fitted? Without one the head & neck box scores 0."
                    ),
                ),
            ]

            def calculation(self) -> CriterionResult:
                if not self.steering_wheel_airbag_exists:
                    rating = 0.0
                else:
                    rating = self.min_of_children()
                return CriterionResult(
                    channel=None,
                    value=rating,
                    rating=rating,
                    color=None,
                )

            class Criterion_Head(Criterion):
                role = Role.AGGREGATE
                name = "Head"
                source = "§3.1.1"
                hard_contact: Manual[
                    bool,
                    manual(
                        True,
                        source="video",
                        doc=(
                            "Was hard head contact observed? A head-acceleration peak above "
                            "80 g forces this to True regardless (Appendix A2: 'video OR curve')."
                        ),
                    ),
                ]

                def calculation(self) -> CriterionResult:
                    if (
                        np.max(
                            np.abs(
                                self.require_channel(
                                    self.ctx.code("?{p}HEAD??00??ACRA")
                                ).get_data(unit=g0)
                            )
                        )
                        > 80
                    ):
                        logger.info(
                            f"Hard Head contact assumed for p={self.ctx.field('p')} in {self.isomme}"
                        )
                        self.hard_contact = True

                    if self.hard_contact:
                        rating = self.min_of_children()
                    else:
                        rating = 4

                    # Modifier

                    rating += np.sum(
                        [
                            self.criterion_damage.result.rating,
                            self.criterion_UnstableAirbagContact.result.rating,
                            self.criterion_HazardousAirbagDeployment.result.rating,
                            self.criterion_IncorrectAirbagDeployment.result.rating,
                            self.criterion_DisplacementSteeringColumn.result.rating,
                        ]
                    )
                    return CriterionResult(
                        channel=None,
                        value=rating,
                        rating=rating,
                        color=None,
                    )

                # §3.2.1.1 repeats §4.2.1 word for word; only the section differs.

                class Criterion_DisplacementSteeringColumn(
                    Overall_Frontal_50kmh.Criterion_Driver.Criterion_Head.Criterion_DisplacementSteeringColumn
                ):
                    source = "§3.2.1.1"

                class Criterion_DAMAGE(Criterion):
                    name = "Modifier for Brain Injury - DAMAGE"
                    role = Role.MODIFIER
                    source = "§3.2.1.1"

                    def define_limits(self) -> list[Limit]:
                        codes = self.ctx.codes("?{p}HEADDAMA??AAR?")
                        return [
                            Limit(
                                codes,
                                func=lambda x: 0.42,
                                y_unit="rad/s^2",
                                rating=0.0,
                                color="green",
                                name="0 pt. Modifier",
                                upper=True,
                            ),
                            Limit(
                                codes,
                                func=lambda x: 0.42,
                                y_unit="rad/s^2",
                                rating=-1.0,
                                color="orange",
                                name="-1 pt. Modifier",
                                lower=True,
                            ),
                            Limit(
                                codes,
                                func=lambda x: 0.47,
                                y_unit="rad/s^2",
                                rating=-2.0,
                                color="red",
                                name="-2 pt. Modifier",
                                lower=True,
                            ),
                        ]

                    def calculation(self) -> CriterionResult:
                        channel = self.require_channel(
                            self.ctx.code("?{p}HEADDAMA??AARA")
                        )
                        value = np.max(channel.get_data())
                        rating = self.limits.get_limit_min_rating(
                            channel, interpolate=False
                        )
                        color = self.limits.get_limit_min_color(channel)
                        return CriterionResult(
                            channel=channel,
                            value=value,
                            rating=rating,
                            color=color,
                        )

                criterion_hic_15 = sub(Criterion_HIC_15)
                criterion_head_a3ms = sub(Criterion_Head_a3ms)
                criterion_damage = sub(Criterion_DAMAGE)
                criterion_UnstableAirbagContact = sub(Criterion_UnstableAirbagContact)
                criterion_HazardousAirbagDeployment = sub(
                    Criterion_HazardousAirbagDeployment
                )
                criterion_IncorrectAirbagDeployment = sub(
                    Criterion_IncorrectAirbagDeployment
                )
                criterion_DisplacementSteeringColumn = sub(
                    Criterion_DisplacementSteeringColumn
                )

            class Criterion_Neck(Criterion):
                role = Role.AGGREGATE
                name = "Neck"
                source = "§3.1.2"

                def calculation(self) -> CriterionResult:

                    rating = self.min_of_children()
                    return CriterionResult(
                        channel=None,
                        value=rating,
                        rating=rating,
                        color=None,
                    )

                class Criterion_My_Extension(Criterion):
                    name = "Neck My extension"

                    def define_limits(self) -> list[Limit]:
                        codes = self.ctx.codes("?{p}NECKUP00??MOY?")
                        return [
                            Limit_G(codes, func=lambda x: -42, y_unit="Nm", lower=True),
                            Limit_A(codes, func=lambda x: -42, y_unit="Nm", upper=True),
                            Limit_M(codes, func=lambda x: -47, y_unit="Nm", upper=True),
                            Limit_W(codes, func=lambda x: -52, y_unit="Nm", upper=True),
                            Limit_P(codes, func=lambda x: -57, y_unit="Nm"),
                            Limit_C(codes, func=lambda x: -57, y_unit="Nm", upper=True),
                        ]

                    def calculation(self) -> CriterionResult:
                        channel = self.require_channel(
                            self.ctx.code("?{p}NECKUP00??MOYB")
                        ).convert_unit("Nm")
                        value = np.min(channel.get_data())
                        rating = self.limits.get_limit_min_rating(channel)
                        color = self.limits.get_limit_min_color(channel)
                        return CriterionResult(
                            channel=channel,
                            value=value,
                            rating=rating,
                            color=color,
                        )

                class Criterion_Fz_Tension(Criterion):
                    name = "Neck Fz tension"

                    def define_limits(self) -> list[Limit]:
                        codes = self.ctx.codes("?{p}NECKUP00??FOZ?")
                        return [
                            Limit_G(
                                codes,
                                func=lambda x: 2.7,
                                y_unit="kN",
                                x_unit="ms",
                                upper=True,
                            ),
                            Limit_A(
                                codes,
                                func=lambda x: 2.7,
                                y_unit="kN",
                                x_unit="ms",
                                lower=True,
                            ),
                            Limit_M(
                                codes,
                                func=lambda x: 2.9,
                                y_unit="kN",
                                x_unit="ms",
                                lower=True,
                            ),
                            Limit_W(
                                codes,
                                func=lambda x: 3.1,
                                y_unit="kN",
                                x_unit="ms",
                                lower=True,
                            ),
                            Limit_P(
                                codes, func=lambda x: 3.3, y_unit="kN", x_unit="ms"
                            ),
                            Limit_C(
                                codes,
                                func=lambda x: 3.3,
                                y_unit="kN",
                                x_unit="ms",
                                lower=True,
                            ),
                        ]

                    def calculation(self) -> CriterionResult:
                        channel = self.require_channel(
                            self.ctx.code("?{p}NECKUP00??FOZA")
                        ).convert_unit("kN")
                        value = np.max(channel.get_data())
                        rating = self.limits.get_limit_min_rating(channel)
                        color = self.limits.get_limit_min_color(channel)
                        return CriterionResult(
                            channel=channel,
                            value=value,
                            rating=rating,
                            color=color,
                        )

                class Criterion_Fx_Shear(Criterion):
                    name = "Neck Fx shear"

                    def define_limits(self) -> list[Limit]:
                        codes = self.ctx.codes("?{p}NECKUP00??FOX?")
                        return [
                            Limit_G(
                                codes,
                                func=lambda x: 1.9,
                                y_unit="kN",
                                x_unit="ms",
                                upper=True,
                            ),
                            Limit_A(
                                codes,
                                func=lambda x: 1.9,
                                y_unit="kN",
                                x_unit="ms",
                                lower=True,
                            ),
                            Limit_M(
                                codes,
                                func=lambda x: 2.3,
                                y_unit="kN",
                                x_unit="ms",
                                lower=True,
                            ),
                            Limit_W(
                                codes,
                                func=lambda x: 2.7,
                                y_unit="kN",
                                x_unit="ms",
                                lower=True,
                            ),
                            Limit_P(
                                codes, func=lambda x: 3.1, y_unit="kN", x_unit="ms"
                            ),
                            Limit_C(
                                codes,
                                func=lambda x: 3.1,
                                y_unit="kN",
                                x_unit="ms",
                                lower=True,
                            ),
                            Limit_G(
                                codes,
                                func=lambda x: -1.9,
                                y_unit="kN",
                                x_unit="ms",
                                lower=True,
                            ),
                            Limit_A(
                                codes,
                                func=lambda x: -1.9,
                                y_unit="kN",
                                x_unit="ms",
                                upper=True,
                            ),
                            Limit_M(
                                codes,
                                func=lambda x: -2.3,
                                y_unit="kN",
                                x_unit="ms",
                                upper=True,
                            ),
                            Limit_W(
                                codes,
                                func=lambda x: -2.7,
                                y_unit="kN",
                                x_unit="ms",
                                upper=True,
                            ),
                            Limit_P(
                                codes, func=lambda x: -3.1, y_unit="kN", x_unit="ms"
                            ),
                            Limit_C(
                                codes,
                                func=lambda x: -3.1,
                                y_unit="kN",
                                x_unit="ms",
                                upper=True,
                            ),
                        ]

                    def calculation(self) -> CriterionResult:
                        channel = self.require_channel(
                            self.ctx.code("?{p}NECKUP00??FOXA")
                        ).convert_unit("kN")
                        value = channel.get_data()[
                            np.argmax(np.abs(channel.get_data()))
                        ]
                        rating = self.limits.get_limit_min_rating(channel)
                        color = self.limits.get_limit_min_color(channel)
                        return CriterionResult(
                            channel=channel,
                            value=value,
                            rating=rating,
                            color=color,
                        )

                criterion_my_extension = sub(Criterion_My_Extension)
                criterion_fz_tension = sub(Criterion_Fz_Tension)
                criterion_fx_shear = sub(Criterion_Fx_Shear)

            criterion_head = sub(Criterion_Head)
            criterion_neck = sub(Criterion_Neck)

        class Criterion_Chest_Abdomen(Criterion):
            role = Role.AGGREGATE
            name = "Chest and Abdomen"
            #: §3.4 groups chest and abdomen into one 4-point body region.
            max_rating = 4.0
            source = "§3.1.3"

            def calculation(self) -> CriterionResult:

                rating = self.min_of_children()
                return CriterionResult(
                    channel=None,
                    value=rating,
                    rating=rating,
                    color=None,
                )

            class Criterion_Chest(Criterion):
                role = Role.AGGREGATE
                name = "Chest"
                source = "§3.1.3.1"

                def calculation(self) -> CriterionResult:

                    rating = self.criterion_chest_compression.result.rating

                    # Modifier

                    rating += np.sum(
                        [
                            self.criterion_shoulder_belt_load.result.rating,
                            self.criterion_SteeringWheelContact.result.rating,
                            self.criterion_DisplacementAPillar.result.rating,
                            self.criterion_CompartmentIntegrity.result.rating,
                        ]
                    )
                    return CriterionResult(
                        channel=None,
                        value=rating,
                        rating=rating,
                        color=None,
                    )

                # §3.2.1.2 repeats §4.2.2 word for word; only the section differs.
                class Criterion_SteeringWheelContact(
                    Overall_Frontal_50kmh.Criterion_Driver.Criterion_Chest.Criterion_SteeringWheelContact
                ):
                    source = "§3.2.1.2"

                class Criterion_DisplacementAPillar(Criterion):
                    report: EuroNCAP_Frontal_MPDB
                    name = "Modifier for Displacement of the A Pillar"
                    role = Role.MODIFIER
                    source = "§3.2.1.2"
                    displacement_a_pillar: Manual[
                        float,
                        manual(
                            0.0,
                            unit="mm",
                            source="measurement",
                            doc=(
                                "Rearward displacement of the driver's front door pillar, "
                                "100 mm below the lowest level of the side window aperture. "
                                "No penalty up to 100 mm, −2 points above 200 mm, linear "
                                "in between (driver only)."
                            ),
                        ),
                    ]

                    def calculation(self) -> CriterionResult:
                        if self.report.criterion_overall[
                            self.isomme
                        ].p_driver != self.ctx.field("p"):
                            rating = 0.0
                            return CriterionResult(
                                channel=None,
                                value=rating,
                                rating=rating,
                                color=None,
                            )

                        value = self.displacement_a_pillar
                        rating = float(
                            np.interp(value, [100, 200], [0, -2], left=0, right=-2)
                        )
                        return CriterionResult(
                            channel=None,
                            value=value,
                            rating=rating,
                            color=None,
                        )

                class Criterion_CompartmentIntegrity(Criterion):
                    report: EuroNCAP_Frontal_MPDB
                    name = "Modifier for Integrity of the Passenger Compartment"
                    role = Role.MODIFIER
                    source = "§3.2.1.2"
                    compartment_integrity_compromised: Manual[
                        bool,
                        manual(
                            False,
                            source="test report",
                            doc=(
                                "Structural integrity of the passenger compartment compromised "
                                "— door latch/hinge failure, door buckling, cross facia rail to "
                                "A pillar separation, or severe loss of door aperture strength. "
                                "−1 point (driver only)."
                            ),
                        ),
                    ]

                    def calculation(self) -> CriterionResult:
                        is_driver = self.report.criterion_overall[
                            self.isomme
                        ].p_driver == self.ctx.field("p")
                        value = self.compartment_integrity_compromised
                        rating = (
                            -1
                            if is_driver and self.compartment_integrity_compromised
                            else 0
                        )
                        return CriterionResult(
                            channel=None,
                            value=value,
                            rating=rating,
                            color=None,
                        )

                class Criterion_Chest_Compression(Criterion):
                    name = "Chest Compression"

                    def define_limits(self) -> list[Limit]:
                        codes = self.ctx.codes("?{p}CHST??????DSX?")
                        return [
                            Limit_C(
                                codes, func=lambda x: -60.000, y_unit="mm", upper=True
                            ),
                            Limit_P(codes, func=lambda x: -60.000, y_unit="mm"),
                            Limit_W(
                                codes, func=lambda x: -51.667, y_unit="mm", upper=True
                            ),
                            Limit_M(
                                codes, func=lambda x: -43.333, y_unit="mm", upper=True
                            ),
                            Limit_A(
                                codes, func=lambda x: -35.000, y_unit="mm", upper=True
                            ),
                            Limit_G(
                                codes, func=lambda x: -35.000, y_unit="mm", lower=True
                            ),
                        ]

                    def calculation(self) -> CriterionResult:
                        # TODO(channel): §3.1.3.1 rates "max compression of all 4 ribs";
                        #   this reads the single aggregate channel. Confirm get_channel
                        #   synthesises the worst of the four THOR IR-TRACC channels, or
                        #   take the minimum over them here.
                        channel = self.require_channel(
                            self.ctx.code("?{p}CHST0000??DSXC")
                        ).convert_unit("mm")
                        value = np.min(channel.get_data())
                        rating = self.limits.get_limit_min_rating(channel)
                        color = self.limits.get_limit_min_color(channel)
                        return CriterionResult(
                            channel=channel,
                            value=value,
                            rating=rating,
                            color=color,
                        )

                criterion_chest_compression = sub(Criterion_Chest_Compression)
                criterion_shoulder_belt_load = sub(Criterion_ShoulderBeltLoad)
                criterion_SteeringWheelContact = sub(Criterion_SteeringWheelContact)
                criterion_DisplacementAPillar = sub(Criterion_DisplacementAPillar)
                criterion_CompartmentIntegrity = sub(Criterion_CompartmentIntegrity)

            class Criterion_Abdomen(Criterion):
                role = Role.AGGREGATE
                name = "Abdomen"
                source = "§3.1.3.2"

                def calculation(self) -> CriterionResult:

                    rating = self.criterion_abdomen_compression.result.rating
                    return CriterionResult(
                        channel=None,
                        value=rating,
                        rating=rating,
                        color=None,
                    )

                class Criterion_Abdomen_Compression(Criterion):
                    name = "Abdomen Compression"

                    def define_limits(self) -> list[Limit]:
                        codes = self.ctx.codes("?{p}ABDO??????DSX?")
                        return [
                            Limit_P(codes, func=lambda x: -88, y_unit="mm", upper=True),
                            Limit_G(codes, func=lambda x: -88, y_unit="mm", lower=True),
                        ]

                    def calculation(self) -> CriterionResult:
                        # TODO(channel): §3.1.3.2 rates "max compression (left or right)";
                        #   this reads the single aggregate channel. Same question as the
                        #   chest above.
                        channel = self.require_channel(
                            self.ctx.code("?{p}ABDO0000??DSXC")
                        ).convert_unit("mm")
                        value = np.min(channel.get_data())
                        rating = self.limits.get_limit_min_rating(
                            channel, interpolate=False
                        )
                        color = self.limits.get_limit_min_color(channel)
                        return CriterionResult(
                            channel=channel,
                            value=value,
                            rating=rating,
                            color=color,
                        )

                criterion_abdomen_compression = sub(Criterion_Abdomen_Compression)

            criterion_chest = sub(Criterion_Chest)
            criterion_abdomen = sub(Criterion_Abdomen)

        class Criterion_Knee_Femur_Pelvis(Criterion):
            role = Role.AGGREGATE
            name = "Knee, Femur and Pelvis"
            max_rating = 4.0
            source = "§3.1.4"

            def calculation(self) -> CriterionResult:

                rating = self.min_of_children()

                # Modifier

                rating += np.sum(
                    [
                        self.criterion_submarining.result.rating,
                        self.criterion_VariableContact.result.rating,
                        self.criterion_ConcentratedLoading.result.rating,
                    ]
                )
                return CriterionResult(
                    channel=None,
                    value=rating,
                    rating=rating,
                    color=None,
                )

            class Criterion_Pelvis(Criterion):
                role = Role.AGGREGATE
                name = "Pelvis"
                source = "§3.1.4.1"

                def calculation(self) -> CriterionResult:

                    rating = self.criterion_acetabulum_force.result.rating
                    return CriterionResult(
                        channel=None,
                        value=rating,
                        rating=rating,
                        color=None,
                    )

                class Criterion_Acetabulum_Force(Criterion):
                    name = "Acetabulum Force"

                    def define_limits(self) -> list[Limit]:
                        codes = self.ctx.codes("?{p}ACTB??00??FOR?")
                        return [
                            Limit_P(
                                codes, func=lambda x: -4.100, y_unit="kN", upper=True
                            ),
                            Limit_W(
                                codes, func=lambda x: -3.827, y_unit="kN", upper=True
                            ),
                            Limit_M(
                                codes, func=lambda x: -3.553, y_unit="kN", upper=True
                            ),
                            Limit_A(
                                codes, func=lambda x: -3.280, y_unit="kN", upper=True
                            ),
                            Limit_G(
                                codes, func=lambda x: -3.280, y_unit="kN", lower=True
                            ),
                        ]

                    def calculation(self) -> CriterionResult:
                        channel = self.require_channel(
                            self.ctx.code("?{p}ACTB0000??FORB")
                        ).convert_unit("kN")
                        value = np.min(channel.get_data())
                        rating = self.limits.get_limit_min_rating(channel)
                        color = self.limits.get_limit_min_color(channel)
                        return CriterionResult(
                            channel=channel,
                            value=value,
                            rating=rating,
                            color=color,
                        )

                criterion_acetabulum_force = sub(Criterion_Acetabulum_Force)

            class Criterion_Femur(Criterion):
                role = Role.AGGREGATE
                name = "Femur"

                def calculation(self) -> CriterionResult:

                    rating = self.criterion_femur_compression.result.rating
                    return CriterionResult(
                        channel=None,
                        value=rating,
                        rating=rating,
                        color=None,
                    )

                criterion_femur_compression = sub(Criterion_Femur_Compression)

            class Criterion_Knee(Criterion):
                role = Role.AGGREGATE
                name = "Knee"

                def calculation(self) -> CriterionResult:

                    rating = self.criterion_knee_slider_compression.result.rating
                    return CriterionResult(
                        channel=None,
                        value=rating,
                        rating=rating,
                        color=None,
                    )

                criterion_knee_slider_compression = sub(
                    Criterion_Knee_Slider_Compression
                )

            criterion_pelvis = sub(Criterion_Pelvis)
            criterion_femur = sub(Criterion_Femur)
            criterion_knee = sub(Criterion_Knee)
            criterion_submarining = sub(Criterion_Submarining)
            criterion_VariableContact = sub(Criterion_VariableContact)
            criterion_ConcentratedLoading = sub(Criterion_ConcentratedLoading)

        class Criterion_LowerLeg_Foot_Ankle(Criterion):
            role = Role.AGGREGATE
            name = "Lower Leg, Foot and Ankle"
            max_rating = 4.0
            source = "§3.1.5"

            def calculation(self) -> CriterionResult:

                rating = self.min_of_children()

                # Modifier

                rating += np.sum(
                    [
                        self.criterion_PedalUpwardDisplacement.result.rating,
                        self.criterion_FootwellRupture.result.rating,
                        self.criterion_PedalBlocking.result.rating,
                    ]
                )
                return CriterionResult(
                    channel=None,
                    value=rating,
                    rating=rating,
                    color=None,
                )

            class Criterion_PedalUpwardDisplacement(Criterion):
                name = "Modifier for Upward Displacement of the Worst Performing Pedal"
                role = Role.MODIFIER
                source = "§3.2.1.5"
                pedal_upward_displacement: Manual[
                    float,
                    manual(
                        0.0,
                        unit="mm",
                        source="measurement",
                        doc=(
                            "Upward static displacement of the worst performing pedal. No "
                            "penalty up to 90 % of the 80 mm EEVC limit, −1 point beyond "
                            "110 %, linear in between."
                        ),
                    ),
                ]

                def calculation(self) -> CriterionResult:
                    value = self.pedal_upward_displacement / 80
                    rating = float(
                        np.interp(value, [0.9, 1.1], [0, -1], left=0, right=-1)
                    )
                    return CriterionResult(
                        channel=None,
                        value=value,
                        rating=rating,
                        color=None,
                    )

            class Criterion_FootwellRupture(Criterion):
                name = "Modifier for Footwell Rupture"
                role = Role.MODIFIER
                source = "§3.2.1.6"
                footwell_rupture: Manual[
                    bool,
                    manual(
                        False,
                        source="test report",
                        doc=(
                            "Significant rupture of the footwell area, usually separation of spot "
                            "welded seams. −1 point."
                        ),
                    ),
                ]

                def calculation(self) -> CriterionResult:
                    value = self.footwell_rupture
                    rating = -1 if self.footwell_rupture else 0
                    return CriterionResult(
                        channel=None,
                        value=value,
                        rating=rating,
                        color=None,
                    )

            class Criterion_PedalBlocking(Criterion):
                name = "Modifier for Pedal Blocking"
                role = Role.MODIFIER
                source = "§3.2.1.6"
                blocked_pedal_rearward_displacement: Manual[
                    float,
                    manual(
                        0.0,
                        unit="mm",
                        source="measurement",
                        doc=(
                            "Rearward displacement of a 'blocked' pedal relative to the pre-test "
                            "measurement. A pedal is blocked when its forward movement under a "
                            "200 N load is below 25 mm. Sliding scale 0 to −1 point between "
                            "50 mm and 175 mm."
                        ),
                    ),
                ]

                def calculation(self) -> CriterionResult:
                    value = self.blocked_pedal_rearward_displacement
                    rating = float(
                        np.interp(value, [50, 175], [0, -1], left=0, right=-1)
                    )
                    return CriterionResult(
                        channel=None,
                        value=value,
                        rating=rating,
                        color=None,
                    )

            class Criterion_Pedal_Rearward_Displacement(Criterion):
                name = "Pedal Rearward Displacement"
                source = "§3.1.5.2"
                pedal_rearward_displacement: Manual[
                    float,
                    manual(
                        0,
                        unit="mm",
                        source="measurement",
                        doc="Rearward displacement of the pedal (4 points below 100 mm, 0 above 200 mm).",
                    ),
                ]

                def calculation(self) -> CriterionResult:
                    value = self.pedal_rearward_displacement
                    rating = float(np.interp(value, [100, 200], [4, 0], left=4))
                    return CriterionResult(
                        channel=None,
                        value=value,
                        rating=rating,
                        color=None,
                    )

            criterion_tibia_index = sub(Criterion_Tibia_Index)
            criterion_tibia_compression = sub(Criterion_Tibia_Compression)
            criterion_pedal_rearward_displacement = sub(
                Criterion_Pedal_Rearward_Displacement
            )
            criterion_PedalUpwardDisplacement = sub(Criterion_PedalUpwardDisplacement)
            criterion_FootwellRupture = sub(Criterion_FootwellRupture)
            criterion_PedalBlocking = sub(Criterion_PedalBlocking)

        criterion_head_neck = sub(Criterion_Head_Neck)
        criterion_chest_abdomen = sub(Criterion_Chest_Abdomen)
        criterion_knee_femur_pelvis = sub(Criterion_Knee_Femur_Pelvis)
        criterion_lowerleg_foot_ankle = sub(Criterion_LowerLeg_Foot_Ankle)

    class Criterion_Passenger(Criterion):
        report: EuroNCAP_Frontal_MPDB
        role = Role.AGGREGATE
        name = "Passenger"
        max_rating, aggregation = 16.0, "sum"

        def calculation(self) -> CriterionResult:

            rating = np.sum(
                [
                    self.criterion_head_neck.result.rating,
                    self.criterion_chest.result.rating,
                    self.criterion_knee_femur_pelvis.result.rating,
                    self.criterion_lowerleg.result.rating,
                ]
            )
            return CriterionResult(
                channel=None,
                value=rating,
                rating=rating,
                color=None,
            )

        class Criterion_Head_Neck(Criterion):
            role = Role.AGGREGATE
            name = "Head and Neck"
            max_rating = 4.0
            source = "§3.1.6"

            def calculation(self) -> CriterionResult:

                rating = value = self.min_of_children()
                return CriterionResult(
                    channel=None,
                    value=value,
                    rating=rating,
                    color=None,
                )

            class Criterion_Head(Criterion):
                role = Role.AGGREGATE
                name = "Head"
                source = "§3.1.6.1"

                def calculation(self) -> CriterionResult:

                    rating = value = self.min_of_children()

                    # Modifier — §3.2.2 gives the passenger the airbag modifiers but
                    # neither the steering column nor the compartment ones.

                    rating += np.sum(
                        [
                            self.criterion_UnstableAirbagContact.result.rating,
                            self.criterion_HazardousAirbagDeployment.result.rating,
                            self.criterion_IncorrectAirbagDeployment.result.rating,
                        ]
                    )
                    return CriterionResult(
                        channel=None,
                        value=value,
                        rating=rating,
                        color=None,
                    )

                # §3.1.1.1: "These criteria are always used for the passenger" —
                # no hard-contact branch here, unlike the driver.
                criterion_hic_15 = sub(Criterion_HIC_15)
                criterion_head_a3ms = sub(Criterion_Head_a3ms)
                criterion_UnstableAirbagContact = sub(Criterion_UnstableAirbagContact)
                criterion_HazardousAirbagDeployment = sub(
                    Criterion_HazardousAirbagDeployment
                )
                criterion_IncorrectAirbagDeployment = sub(
                    Criterion_IncorrectAirbagDeployment
                )

            class Criterion_Neck(Criterion):
                role = Role.AGGREGATE
                name = "Neck"
                source = "§3.1.6.2"

                def calculation(self) -> CriterionResult:

                    rating = value = self.min_of_children()
                    return CriterionResult(
                        channel=None,
                        value=value,
                        rating=rating,
                        color=None,
                    )

                class Criterion_Fx_Shear(Criterion):
                    name = "Neck Fx shear"

                    def define_limits(self) -> list[Limit]:
                        codes = self.ctx.codes("?{p}NECKUP00??FOX?")
                        return [
                            Limit_G(
                                codes,
                                func=lambda x: np.interp(
                                    x, [0, 25, 35, 45], [1.9, 1.2, 1.2, 1.1]
                                ),
                                y_unit="kN",
                                x_unit="ms",
                                upper=True,
                            ),
                            Limit_A(
                                codes,
                                func=lambda x: np.interp(
                                    x, [0, 25, 35, 45], [1.9, 1.2, 1.2, 1.1]
                                ),
                                y_unit="kN",
                                x_unit="ms",
                                lower=True,
                            ),
                            Limit_M(
                                codes,
                                func=lambda x: np.interp(
                                    x, [0, 25, 35, 45], [2.3, 1.3, 1.3, 1.1]
                                ),
                                y_unit="kN",
                                x_unit="ms",
                                lower=True,
                            ),
                            Limit_W(
                                codes,
                                func=lambda x: np.interp(
                                    x, [0, 25, 35, 45], [2.7, 1.4, 1.4, 1.1]
                                ),
                                y_unit="kN",
                                x_unit="ms",
                                lower=True,
                            ),
                            Limit_P(
                                codes,
                                func=lambda x: np.interp(
                                    x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1]
                                ),
                                y_unit="kN",
                                x_unit="ms",
                            ),
                            Limit_C(
                                codes,
                                func=lambda x: np.interp(
                                    x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1]
                                ),
                                y_unit="kN",
                                x_unit="ms",
                                lower=True,
                            ),
                            Limit_G(
                                codes,
                                func=lambda x: np.interp(
                                    x, [0, 25, 35, 45], [-1.9, -1.2, -1.2, -1.1]
                                ),
                                y_unit="kN",
                                x_unit="ms",
                                lower=True,
                            ),
                            Limit_A(
                                codes,
                                func=lambda x: np.interp(
                                    x, [0, 25, 35, 45], [-1.9, -1.2, -1.2, -1.1]
                                ),
                                y_unit="kN",
                                x_unit="ms",
                                upper=True,
                            ),
                            Limit_M(
                                codes,
                                func=lambda x: np.interp(
                                    x, [0, 25, 35, 45], [-2.3, -1.3, -1.3, -1.1]
                                ),
                                y_unit="kN",
                                x_unit="ms",
                                upper=True,
                            ),
                            Limit_W(
                                codes,
                                func=lambda x: np.interp(
                                    x, [0, 25, 35, 45], [-2.7, -1.4, -1.4, -1.1]
                                ),
                                y_unit="kN",
                                x_unit="ms",
                                upper=True,
                            ),
                            Limit_P(
                                codes,
                                func=lambda x: np.interp(
                                    x, [0, 25, 35, 45], [-3.1, -1.5, -1.5, -1.1]
                                ),
                                y_unit="kN",
                                x_unit="ms",
                            ),
                            Limit_C(
                                codes,
                                func=lambda x: np.interp(
                                    x, [0, 25, 35, 45], [-3.1, -1.5, -1.5, -1.1]
                                ),
                                y_unit="kN",
                                x_unit="ms",
                                upper=True,
                            ),
                        ]

                    def calculation(self) -> CriterionResult:
                        channel = self.require_channel(
                            self.ctx.code("?{p}NECKUP00??FOXA")
                        ).convert_unit("kN")
                        value = self.limits.get_limit_min_y(channel)
                        rating = self.limits.get_limit_min_rating(channel)
                        color = self.limits.get_limit_min_color(channel)
                        return CriterionResult(
                            channel=channel,
                            value=value,
                            rating=rating,
                            color=color,
                        )

                class Criterion_Fz_Tension(Criterion):
                    name = "Fz Tension"

                    def define_limits(self) -> list[Limit]:
                        codes = self.ctx.codes("?{p}NECKUP00??FOZ?")
                        return [
                            Limit_G(
                                codes,
                                func=lambda x: np.interp(
                                    x, [0, 35, 60], [2.7, 2.3, 1.1]
                                ),
                                y_unit="kN",
                                x_unit="ms",
                                upper=True,
                            ),
                            Limit_A(
                                codes,
                                func=lambda x: np.interp(
                                    x, [0, 35, 60], [2.7, 2.3, 1.1]
                                ),
                                y_unit="kN",
                                x_unit="ms",
                                lower=True,
                            ),
                            Limit_M(
                                codes,
                                func=lambda x: np.interp(
                                    x, [0, 35, 60], [2.9, 2.5, 1.1]
                                ),
                                y_unit="kN",
                                x_unit="ms",
                                lower=True,
                            ),
                            Limit_W(
                                codes,
                                func=lambda x: np.interp(
                                    x, [0, 35, 60], [3.1, 2.7, 1.1]
                                ),
                                y_unit="kN",
                                x_unit="ms",
                                lower=True,
                            ),
                            Limit_P(
                                codes,
                                func=lambda x: np.interp(
                                    x, [0, 35, 60], [3.3, 2.9, 1.1]
                                ),
                                y_unit="kN",
                                x_unit="ms",
                            ),
                            Limit_C(
                                codes,
                                func=lambda x: np.interp(
                                    x, [0, 35, 60], [3.3, 2.9, 1.1]
                                ),
                                y_unit="kN",
                                x_unit="ms",
                                lower=True,
                            ),
                        ]

                    def calculation(self) -> CriterionResult:
                        channel = self.require_channel(
                            self.ctx.code("?{p}NECKUP00??FOZA")
                        ).convert_unit("kN")
                        value = self.limits.get_limit_min_y(channel)
                        rating = self.limits.get_limit_min_rating(channel)
                        color = self.limits.get_limit_min_color(channel)
                        return CriterionResult(
                            channel=channel,
                            value=value,
                            rating=rating,
                            color=color,
                        )

                class Criterion_My_Extension(Criterion):
                    name = "My Extension"

                    def define_limits(self) -> list[Limit]:
                        codes = self.ctx.codes("?{p}NECKUP00??MOY?")
                        return [
                            Limit_G(codes, func=lambda x: -42, y_unit="Nm", lower=True),
                            Limit_A(codes, func=lambda x: -42, y_unit="Nm", upper=True),
                            Limit_M(codes, func=lambda x: -47, y_unit="Nm", upper=True),
                            Limit_W(codes, func=lambda x: -52, y_unit="Nm", upper=True),
                            Limit_P(codes, func=lambda x: -57, y_unit="Nm"),
                            Limit_C(codes, func=lambda x: -57, y_unit="Nm", upper=True),
                        ]

                    def calculation(self) -> CriterionResult:
                        channel = self.require_channel(
                            self.ctx.code("?{p}NECKUP00??MOYB")
                        ).convert_unit("Nm")
                        value = np.min(channel.get_data())
                        rating = self.limits.get_limit_min_rating(channel)
                        color = self.limits.get_limit_min_color(channel)
                        return CriterionResult(
                            channel=channel,
                            value=value,
                            rating=rating,
                            color=color,
                        )

                criterion_fx_shear = sub(Criterion_Fx_Shear)
                criterion_fz_tension = sub(Criterion_Fz_Tension)
                criterion_my_extension = sub(Criterion_My_Extension)

            criterion_head = sub(Criterion_Head)
            criterion_neck = sub(Criterion_Neck)

        class Criterion_Chest(Criterion):
            role = Role.AGGREGATE
            name = "Chest"
            #: §3.4 groups chest and abdomen into one 4-point body region; only the
            #: chest is measured on the passenger (§3.1.7).
            max_rating = 4.0
            source = "§3.1.7"

            def calculation(self) -> CriterionResult:

                rating = value = self.min_of_children()

                # Modifier
                rating += self.criterion_shoulder_belt_load.result.rating
                return CriterionResult(
                    channel=None,
                    value=value,
                    rating=rating,
                    color=None,
                )

            class Criterion_Chest_Compression(Criterion):
                name = "Chest Compression"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}CHST000[03]??DSX?")
                    return [
                        Limit_C(codes, func=lambda x: -42.000, y_unit="mm", upper=True),
                        Limit_P(codes, func=lambda x: -42.000, y_unit="mm"),
                        Limit_W(codes, func=lambda x: -35.333, y_unit="mm", upper=True),
                        Limit_M(codes, func=lambda x: -28.667, y_unit="mm", upper=True),
                        Limit_A(codes, func=lambda x: -22.000, y_unit="mm", upper=True),
                        Limit_G(codes, func=lambda x: -22.000, y_unit="mm", lower=True),
                    ]

                def calculation(self) -> CriterionResult:
                    channel = self.require_channel(
                        self.ctx.code("?{p}CHST0003??DSXC"),
                        self.ctx.code("?{p}CHST0000??DSXC"),
                    ).convert_unit("mm")
                    value = np.min(channel.get_data())
                    rating = self.limits.get_limit_min_rating(channel, interpolate=True)
                    color = self.limits.get_limit_min_color(channel)
                    return CriterionResult(
                        channel=channel,
                        value=value,
                        rating=rating,
                        color=color,
                    )

            criterion_chest_compression = sub(Criterion_Chest_Compression)
            criterion_chest_vc = sub(Criterion_Chest_VC)
            criterion_shoulder_belt_load = sub(Criterion_ShoulderBeltLoad)

        class Criterion_Knee_Femur_Pelvis(Criterion):
            report: EuroNCAP_Frontal_MPDB
            role = Role.AGGREGATE
            name = "Knee, Femur and Pelvis"
            #: §3.4 groups pelvis and upper leg into one 4-point body region; §3.1.8
            #: has no acetabulum row for the passenger.
            max_rating = 4.0
            source = "§3.1.8"

            def calculation(self) -> CriterionResult:

                rating = value = self.min_of_children()

                # Modifier

                rating += np.sum(
                    [
                        self.criterion_VariableContact.result.rating,
                        self.criterion_ConcentratedLoading.result.rating,
                    ]
                )
                return CriterionResult(
                    channel=None,
                    value=value,
                    rating=rating,
                    color=None,
                )

            criterion_femur_compression = sub(Criterion_Femur_Compression)
            criterion_knee_slider_compression = sub(Criterion_Knee_Slider_Compression)
            # §3.2.2: the passenger gets the two knee modifiers but not
            # submarining, which §3.2.1.3 scopes to the driver.
            criterion_VariableContact = sub(Criterion_VariableContact)
            criterion_ConcentratedLoading = sub(Criterion_ConcentratedLoading)

        class Criterion_LowerLeg(Criterion):
            report: EuroNCAP_Frontal_MPDB
            role = Role.AGGREGATE
            name = "Lower Leg"
            #: §3.4 groups lower leg and foot into one 4-point body region; §3.1.9
            #: has no pedal row for the passenger.
            max_rating = 4.0
            source = "§3.1.9"

            def calculation(self) -> CriterionResult:

                rating = self.min_of_children()
                return CriterionResult(
                    channel=None,
                    value=rating,
                    rating=rating,
                    color=None,
                )

            criterion_tibia_index = sub(Criterion_Tibia_Index)
            criterion_tibia_compression = sub(Criterion_Tibia_Compression)

        criterion_head_neck = sub(Criterion_Head_Neck)
        criterion_chest = sub(Criterion_Chest)
        criterion_knee_femur_pelvis = sub(Criterion_Knee_Femur_Pelvis)
        criterion_lowerleg = sub(Criterion_LowerLeg)

    class Criterion_Compatibility_Modifier(Criterion):
        role = Role.AGGREGATE
        name = "Compatibility Modifier"
        source = "§3.3"

        def calculation(self) -> CriterionResult:
            # self.criterion_sd_modifier.calculate()
            # self.criterion_bo_modifier.calculate()

            value = np.sum(
                [
                    self.criterion_olc_modifier.result.rating,
                    # self.criterion_sd_modifier.result.rating,
                    # self.criterion_bo_modifier.result.rating
                ]
            )
            rating = float(
                np.interp(value, [-8, 0], [-8, 0])
            )  # penalty will not exceed -8 pts.
            return CriterionResult(
                channel=None,
                value=value,
                rating=rating,
                color=None,
            )

        class Criterion_OLC_Modifier(Criterion):
            name = "Occupant Load Criterion (OLC) Modifier"

            def define_limits(self) -> list[Limit]:
                return [
                    Limit(
                        ("M?MBAR0OLC??VEX?",),
                        func=lambda x: 25,
                        y_unit=Unit(g0),
                        color=Limit_G.color,
                        name="0 pt. Modifier",
                        rating=0,
                        upper=True,
                    ),
                    Limit(
                        ("M?MBAR0OLC??VEX?",),
                        func=lambda x: 25,
                        y_unit=Unit(g0),
                        color=Limit_P.color,
                        name="-2..0 pt. Modifier",
                        rating=0,
                        lower=True,
                    ),
                    Limit(
                        ("M?MBAR0OLC??VEX?",),
                        func=lambda x: 40,
                        y_unit=Unit(g0),
                        color=Limit_P.color,
                        name="-2 pt. Modifier",
                        rating=-2,
                        lower=True,
                    ),
                ]

            def calculation(self) -> CriterionResult:
                channel = calculate_olc(
                    self.require_channel("M?MBAR0000??VEXA", "M?MBARCG00??VEXA")
                )[0].convert_unit(Unit(g0))
                value = channel.get_data()[0]
                rating = self.limits.get_limit_min_rating(channel, interpolate=True)
                color = self.limits.get_limits(channel)[0].color
                return CriterionResult(
                    channel=channel,
                    value=value,
                    rating=rating,
                    color=color,
                )

        # TODO(protocol): §3.3 bases the compatibility penalty on three parameters;
        #   only OLC (§3.3.2) is implemented. Missing: §3.3.1 barrier deformation,
        #   assessed on the standard deviation of the post-test measurements over
        #   50-150 mm, and §3.3.3 barrier face bottoming out, a flat -2 points for a
        #   630 mm penetration caused by a load bearing structure over an area larger
        #   than 40x40 mm. Both need TB027 for the exact scaling. Until they exist the
        #   penalty cannot reach the -8 that §3.3 caps it at.
        class Criterion_SD_Modifier(Criterion):
            pass

        class Criterion_BO_Modifier(Criterion):
            pass

        criterion_olc_modifier = sub(Criterion_OLC_Modifier)
        # self.criterion_sd_modifier = self.Criterion_SD_Modifier(report, isomme)
        # self.criterion_bo_modifier = self.Criterion_BO_Modifier(report, isomme)

    criterion_driver = sub(Criterion_Driver, at=from_input(P_DRIVER))
    criterion_passenger = sub(Criterion_Passenger, at=from_input(P_PASSENGER))
    criterion_door_opening_during_impact = sub(
        Overall_Frontal_50kmh.Criterion_DoorOpeningDuringImpact, role=Role.MODIFIER
    )
    criterion_compatibility_modifier = sub(
        Criterion_Compatibility_Modifier, role=Role.MODIFIER
    )


class EuroNCAP_Frontal_MPDB(Report[Overall]):
    _name = "Euro NCAP | Frontal-Impact against MPDB with 50 % Overlap at 50/50 km/h"
    _protocol = PROTOCOL_9_3
    _protocols = (PROTOCOL_9_3,)
    Criterion_Overall = Overall

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._available_pages = (
            Page_Cover(self),
            self.Page_Rating_Table(self),
            self.Page_Driver_Result_Values_Chart(self),
            self.Page_Driver_Rating_Table(self),
            self.Page_Driver_Values_Table(self),
            self.Page_Driver_Belt(self),
            self.Page_Driver_Head_Acceleration(self),
            self.Page_Driver_Head_Damage(self),
            self.Page_Driver_Neck_Load(self),
            self.Page_Driver_Chest_Compression(self),
            self.Page_Driver_Abdomen_Compression(self),
            self.Page_Driver_Femur_Axial_Force(self),
            self.Page_Driver_Knee_Slider_Compression(self),
            self.Page_Driver_Tibia_Compression(self),
            self.Page_Driver_Tibia_Index(self),
            self.Page_Passenger_Result_Values_Chart(self),
            self.Page_Passenger_Rating_Table(self),
            self.Page_Passenger_Values_Table(self),
            self.Page_Passenger_Belt(self),
            self.Page_Passenger_Head_Acceleration(self),
            self.Page_Passenger_Neck_Load(self),
            self.Page_Passenger_Chest_Deflection(self),
            self.Page_Passenger_Femur_Axial_Force(self),
            self.Page_Passenger_Knee_Slider_Compression(self),
            self.Page_Passenger_Tibia_Compression(self),
            self.Page_Passenger_Tibia_Index(self),
            Page_OLC(self),
            self.Page_OLC_Trolley(self),
        )
        self._selected_pages = list(self._available_pages)

    class Page_Rating_Table(Page_Criterion_Rating_Table):
        report: EuroNCAP_Frontal_MPDB
        name = "Rating"
        title = "Rating"

        def __init__(self, report: EuroNCAP_Frontal_MPDB) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[isomme].criterion_driver,
                    self.report.criterion_overall[isomme].criterion_passenger,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_compatibility_modifier,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_door_opening_during_impact,
                    self.report.criterion_overall[isomme],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Driver_Result_Values_Chart(Page_Criterion_Values_Chart):
        report: EuroNCAP_Frontal_MPDB
        name = "Driver Result Values Chart"
        title = "Driver Result"

        def __init__(self, report: EuroNCAP_Frontal_MPDB) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_head_neck.criterion_head.criterion_hic_15,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_head_neck.criterion_head.criterion_head_a3ms,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_head_neck.criterion_head.criterion_damage,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_head_neck.criterion_neck.criterion_my_extension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_head_neck.criterion_neck.criterion_fz_tension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_head_neck.criterion_neck.criterion_fx_shear,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_chest_abdomen.criterion_chest.criterion_shoulder_belt_load,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_chest_abdomen.criterion_chest.criterion_chest_compression,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_chest_abdomen.criterion_abdomen.criterion_abdomen_compression,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_knee_femur_pelvis.criterion_pelvis.criterion_acetabulum_force,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_knee_femur_pelvis.criterion_femur.criterion_femur_compression,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_knee_femur_pelvis.criterion_knee.criterion_knee_slider_compression,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_lowerleg_foot_ankle.criterion_tibia_index,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_lowerleg_foot_ankle.criterion_tibia_compression,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Driver_Rating_Table(Page_Criterion_Rating_Table):
        report: EuroNCAP_Frontal_MPDB
        name = "Driver Rating Table"
        title = "Driver Rating"

        def __init__(self, report: EuroNCAP_Frontal_MPDB) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_head_neck,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_chest_abdomen,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_knee_femur_pelvis.criterion_knee,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_lowerleg_foot_ankle,
                    self.report.criterion_overall[isomme].criterion_driver,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Driver_Values_Table(Page_Criterion_Values_Table):
        report: EuroNCAP_Frontal_MPDB
        name = "Driver Values Table"
        title = "Driver Values"

        def __init__(self, report: EuroNCAP_Frontal_MPDB) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_head_neck.criterion_head.criterion_hic_15,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_head_neck.criterion_head.criterion_head_a3ms,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_head_neck.criterion_head.criterion_damage,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_head_neck.criterion_neck.criterion_my_extension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_head_neck.criterion_neck.criterion_fz_tension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_head_neck.criterion_neck.criterion_fx_shear,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_chest_abdomen.criterion_chest.criterion_shoulder_belt_load,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_chest_abdomen.criterion_chest.criterion_chest_compression,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_chest_abdomen.criterion_abdomen.criterion_abdomen_compression,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_knee_femur_pelvis.criterion_pelvis.criterion_acetabulum_force,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_knee_femur_pelvis.criterion_femur.criterion_femur_compression,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_knee_femur_pelvis.criterion_knee.criterion_knee_slider_compression,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_lowerleg_foot_ankle.criterion_tibia_index,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_lowerleg_foot_ankle.criterion_tibia_compression,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Driver_Belt(EuroNCAP_Frontal_50kmh.Page_Driver_Belt):
        pass

    class Page_Driver_Head_Acceleration(
        EuroNCAP_Frontal_50kmh.Page_Driver_Head_Acceleration
    ):
        pass

    class Page_Driver_Head_Damage(Page_Plot_nxn):
        report: EuroNCAP_Frontal_MPDB
        name = "Driver Head DAMAGE"
        title = "Driver Head DAMAGE"
        nrows = 2
        ncols = 2
        sharey = True

        def __init__(self, report: EuroNCAP_Frontal_MPDB) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}HEADDAMA??AAXA"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}HEADDAMA??AAYA"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}HEADDAMA??AAZA"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}HEADDAMA??AARA"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Driver_Neck_Load(EuroNCAP_Frontal_50kmh.Page_Driver_Neck_Load):
        pass

    class Page_Driver_Chest_Compression(Page_Plot_nxn):
        report: EuroNCAP_Frontal_MPDB
        name = "Driver Chest Compression"
        title = "Driver Chest Compression"
        nrows = 2
        ncols = 2
        sharey = True

        def __init__(self, report: EuroNCAP_Frontal_MPDB) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}CHSTLEUP??DSXC"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}CHSTRIUP??DSXC"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}CHSTLELO??DSXC"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}CHSTRILO??DSXC"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Driver_Abdomen_Compression(Page_Plot_nxn):
        report: EuroNCAP_Frontal_MPDB
        name = "Driver Abdomen Compression"
        title = "Driver Abdomen Compression"
        nrows = 1
        ncols = 2

        def __init__(self, report: EuroNCAP_Frontal_MPDB) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}ABDOLE00??DSXC"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}ABDORI00??DSXC"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Driver_Femur_Axial_Force(
        EuroNCAP_Frontal_50kmh.Page_Driver_Femur_Axial_Force
    ):
        pass

    class Page_Driver_Tibia_Compression(Page_Plot_nxn):
        name = "Driver Tibia Compression"
        title = "Driver Tibia Compression"
        nrows = 2
        ncols = 2
        sharey = True

        def __init__(self, report: Report[Any]) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}TIBILEUP??FOZB"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}TIBIRIUP??FOZB"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}TIBILELO??FOZB"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}TIBIRILO??FOZB"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Driver_Tibia_Index(Page_Plot_nxn):
        name = "Driver Tibia Index"
        title = "Driver Tibia Index"
        nrows = 2
        ncols = 2
        sharey = True

        def __init__(self, report: Report[Any]) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}TIINLU00??000B"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}TIINRU00??000B"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}TIINLL00??000B"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}TIINRL00??000B"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Driver_Knee_Slider_Compression(Page_Plot_nxn):
        name = "Driver Knee Slider Compression"
        title = "Driver Knee Slider Compression"
        nrows = 1
        ncols = 2
        sharey = True

        def __init__(self, report: Report[Any]) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}KNSLLE00??DSXC"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}KNSLRI00??DSXC"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Passenger_Result_Values_Chart(Page_Criterion_Values_Chart):
        report: EuroNCAP_Frontal_MPDB
        name = "Passenger Result Values Chart"
        title = "Passenger Result"

        def __init__(self, report: EuroNCAP_Frontal_MPDB) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_head_neck.criterion_head.criterion_hic_15,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_head_neck.criterion_head.criterion_head_a3ms,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_head_neck.criterion_neck.criterion_fx_shear,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_head_neck.criterion_neck.criterion_fz_tension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_head_neck.criterion_neck.criterion_my_extension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_chest.criterion_shoulder_belt_load,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_chest.criterion_chest_compression,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_chest.criterion_chest_vc,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_knee_femur_pelvis.criterion_femur_compression,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_knee_femur_pelvis.criterion_knee_slider_compression,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_lowerleg.criterion_tibia_index,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_lowerleg.criterion_tibia_compression,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Passenger_Rating_Table(Page_Criterion_Rating_Table):
        report: EuroNCAP_Frontal_MPDB
        name: str = "Passenger Rating Table"
        title: str = "Passenger Rating"

        def __init__(self, report: EuroNCAP_Frontal_MPDB) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_head_neck,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_chest,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_knee_femur_pelvis,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_lowerleg,
                    self.report.criterion_overall[isomme].criterion_passenger,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Passenger_Values_Table(Page_Criterion_Values_Table):
        report: EuroNCAP_Frontal_MPDB
        name: str = "Passenger Values Table"
        title: str = "Passenger Values"

        def __init__(self, report: EuroNCAP_Frontal_MPDB) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_head_neck.criterion_head.criterion_hic_15,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_head_neck.criterion_head.criterion_head_a3ms,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_head_neck.criterion_neck.criterion_fx_shear,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_head_neck.criterion_neck.criterion_fz_tension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_head_neck.criterion_neck.criterion_my_extension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_chest.criterion_shoulder_belt_load,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_chest.criterion_chest_compression,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_chest.criterion_chest_vc,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_knee_femur_pelvis.criterion_femur_compression,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_knee_femur_pelvis.criterion_knee_slider_compression,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_lowerleg.criterion_tibia_index,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_lowerleg.criterion_tibia_compression,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Passenger_Belt(Page_Plot_nxn):
        report: EuroNCAP_Frontal_MPDB
        name: str = "Passenger Belt"
        title: str = "Passenger Belt"
        nrows: int = 3
        ncols: int = 2
        sharey: bool = False

        def __init__(self, report: EuroNCAP_Frontal_MPDB) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}SEBE000[30]B1FO[X0]C"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}SEBE000[30]B2FO[X0]C"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}SEBE000[30]B3FO[X0]C"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}SEBE000[30]B4FO[X0]C"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}SEBE000[30]B5FO[X0]C"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}SEBE000[30]B6FO[X0]C"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Passenger_Head_Acceleration(Page_Plot_nxn):
        name: str = "Passenger Head Acceleration"
        title: str = "Passenger Head Acceleration"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: Report[Any]) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}HEAD??????AC{xyzr}A"
                    ]
                    for xyzr in "XYZR"
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Passenger_Neck_Load(Page_Plot_nxn):
        name: str = "Passenger Neck Load"
        title: str = "Passenger Neck Load"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = False

        def __init__(self, report: Report[Any]) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}NECKUP00??MOYB"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}NECKUP00??FOZA"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}NECKUP00??FOXA"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Passenger_Chest_Deflection(Page_Plot_nxn):
        name: str = "Passenger Chest Deflection"
        title: str = "Passenger Chest Deflection"
        nrows: int = 1
        ncols: int = 2

        def __init__(self, report: Report[Any]) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}CHST000???DSXC"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}VCCR000???VEXC"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Passenger_Femur_Axial_Force(Page_Plot_nxn):
        name: str = "Passenger Femur Axial Force"
        title: str = "Passenger Femur Axial Force"
        nrows: int = 1
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: Report[Any]) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}FEMRLE00??FOZB"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}FEMRRI00??FOZB"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Passenger_Knee_Slider_Compression(Page_Plot_nxn):
        name = "Passenger Knee Slider Compression"
        title = "Passenger Knee Slider Compression"
        nrows = 1
        ncols = 2
        sharey = True

        def __init__(self, report: Report[Any]) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}KNSLLE00??DSXC"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}KNSLRI00??DSXC"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Passenger_Tibia_Compression(Page_Plot_nxn):
        name = "Passenger Tibia Compression"
        title = "Passenger Tibia Compression"
        nrows = 2
        ncols = 2
        sharey = True

        def __init__(self, report: Report[Any]) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}TIBILEUP??FOZB"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}TIBIRIUP??FOZB"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}TIBILELO??FOZB"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}TIBIRILO??FOZB"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Passenger_Tibia_Index(Page_Plot_nxn):
        name = "Passenger Tibia Index"
        title = "Passenger Tibia Index"
        nrows = 2
        ncols = 2
        sharey = True

        def __init__(self, report: Report[Any]) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}TIINLU00??000B"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}TIINRU00??000B"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}TIINLL00??000B"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_passenger}TIINRL00??000B"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_OLC_Trolley(Page_Line_Table):
        name: str = "OLC Trolley"
        title: str = "Occupant Load Criterion (OLC) of Trolley"
        nrows: int = 1
        ncols: int = 2

        def __init__(self, report: EuroNCAP_Frontal_MPDB) -> None:
            # This page plots the trolley velocity and its OLC velocity
            # construction. The report-level OLC limits are accelerations (g0),
            # so they cannot be applied to this m/s plot.
            super().__init__(report, limits=Limits())
            self.channels = {}
            cell_texts = []
            cell_colors = []
            row_labels = []
            self.col_labels = [["OLC [g]"]]
            for isomme in self.report.isomme_list:
                channel = isomme.get_channel("M?MBAR0000??VEXA", "M?MBARCG00??VEXA")
                if channel is None:
                    logger.info(
                        f"No trolley velocity channel in {isomme}. OLC trolley plot left empty."
                    )
                    self.channels[isomme] = [[]]
                    cell_texts.append([f"{np.nan:.2f}"])
                    cell_colors.append([(0.0, 0.0, 0.0, 0.0)])
                    row_labels.append(isomme.test_number)
                    continue
                olc, olc_visual = calculate_olc(channel)
                criterion = self.report.criterion_overall[
                    isomme
                ].criterion_compatibility_modifier.criterion_olc_modifier
                result = criterion.result
                self.channels[isomme] = [[channel, olc_visual]]
                cell_texts.append([f"{olc.get_data(unit=Unit(g0))[0]:.2f}"])
                cell_colors.append(
                    [
                        (*to_rgb(result.color), 0.5)
                        if result is not None and result.color is not None
                        else (0.0, 0.0, 0.0, 0.0)
                    ]
                )
                row_labels.append(isomme.test_number)
            self.cell_texts = [cell_texts]
            self._cell_colors = cell_colors
            self.row_labels = [row_labels]

        def figure(self, figsize: tuple[float, float]) -> Figure:
            def result_color(
                isomme: Isomme, fallback: tuple[float, float, float, float]
            ) -> tuple[float, float, float, float]:
                result = self.report.criterion_overall[
                    isomme
                ].criterion_compatibility_modifier.criterion_olc_modifier.result
                return (
                    (*to_rgb(result.color), 0.5)
                    if result is not None and result.color is not None
                    else fallback
                )

            self.cell_colors = [
                [
                    [result_color(isomme, self._cell_colors[idx][0])]
                    for idx, isomme in enumerate(self.report.isomme_list)
                ]
            ]
            return super().figure(figsize)
