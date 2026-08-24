from __future__ import annotations

import logging
from typing import Any

import numpy as np
from matplotlib.figure import Figure

from pyisomme.isomme import Isomme
from pyisomme.limit import Limit
from pyisomme.plotting import Plot_Line_Table
from pyisomme.report.criterion import Criterion, Role, sub
from pyisomme.report.criterion_result import CriterionResult
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
P_FRONT_PASSENGER = manual(
    "3",
    source="test report",
    doc=(
        "Channel-code position of the front passenger. Derived from p_driver "
        "('1' for a right-hand-drive test) unless set explicitly."
    ),
)
P_REAR_PASSENGER = manual(
    "6",
    source="test report",
    doc=(
        "Channel-code position of the rear passenger. Derived from p_driver "
        "('4' for a right-hand-drive test) unless set explicitly."
    ),
)


class Criterion_HIC_15(Criterion):
    name = "HIC 15"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}HICR0015??00RX", "?{p}HICRCG15??00RX")
        return [
            Limit_G(codes, func=lambda x: 500.000, y_unit=1, upper=True),
            Limit_A(codes, func=lambda x: 500.000, y_unit=1, lower=True),
            Limit_M(codes, func=lambda x: 566.667, y_unit=1, lower=True),
            Limit_W(codes, func=lambda x: 633.333, y_unit=1, lower=True),
            Limit_P(codes, func=lambda x: 700.000, y_unit=1),
            Limit_C(codes, func=lambda x: 700.000, y_unit=1, lower=True),
        ]

    def calculation(self) -> CriterionResult:
        channel = self.require_channel(
            *self.ctx.codes("?{p}HICR0015??00RX", "?{p}HICRCG15??00RX")
        )
        value = channel.get_data()[0]
        rating = self.limits.get_limit_min_rating(channel, interpolate=True)
        color = self.limits.get_limit_min_color(channel)
        return CriterionResult(
            channel=channel,
            value=value,
            rating=rating,
            color=color,
        )


class Criterion_Head_a3ms(Criterion):
    name = "Head a3ms"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}HEAD003C??ACR?", "?{p}HEADCG3C??ACR?")
        return [
            Limit_G(codes, func=lambda x: 72.000, y_unit=Unit(g0), upper=True),
            Limit_A(codes, func=lambda x: 72.000, y_unit=Unit(g0), lower=True),
            Limit_M(codes, func=lambda x: 74.667, y_unit=Unit(g0), lower=True),
            Limit_W(codes, func=lambda x: 77.333, y_unit=Unit(g0), lower=True),
            Limit_P(codes, func=lambda x: 80.000, y_unit=Unit(g0)),
            Limit_C(codes, func=lambda x: 80.000, y_unit=Unit(g0), lower=True),
        ]

    def calculation(self) -> CriterionResult:
        channel = self.require_channel(
            *self.ctx.codes("?{p}HEAD003C??ACRX", "?{p}HEADCG3C??ACRX")
        ).convert_unit(Unit(g0))
        value = channel.get_data()[0]
        rating = self.limits.get_limit_min_rating(channel, interpolate=True)
        color = self.limits.get_limit_min_color(channel)
        return CriterionResult(
            channel=channel,
            value=value,
            rating=rating,
            color=color,
        )


class Criterion_UnstableAirbagContact(Criterion):
    #: §4.2.1 scopes this to "Driver and Rear Passenger", so the class is
    #: shared by both — hence no steering wheel in the name. Detachment of
    #: the steering wheel is only one (driver-specific) example of the
    #: compromised airbag protection the modifier really covers.
    name = "Modifier for Unstable Airbag Contact"
    source = "§4.2.1"
    role = Role.MODIFIER
    unstable_airbag_contact: Manual[
        bool,
        manual(
            False,
            source="video",
            doc=(
                "During the head's forward movement its centre of gravity moved "
                "further than the outside edge of the airbag, or head protection by "
                "the airbag was otherwise compromised — steering wheel detached from "
                "the column, airbag bottomed out by the head. −1 point."
            ),
        ),
    ]

    def calculation(self) -> CriterionResult:
        value = self.unstable_airbag_contact
        rating = -1 if self.unstable_airbag_contact else 0
        return CriterionResult(
            channel=None,
            value=value,
            rating=rating,
            color=None,
        )


class Criterion_Chest_Deflection(Criterion):
    name = "Chest Deflection"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}CHST000[03]??DSX?")
        return [
            Limit_C(codes, func=lambda x: -34.000, y_unit="mm", upper=True),
            Limit_P(codes, func=lambda x: -34.000, y_unit="mm"),
            Limit_W(codes, func=lambda x: -28.667, y_unit="mm", upper=True),
            Limit_M(codes, func=lambda x: -23.333, y_unit="mm", upper=True),
            Limit_A(codes, func=lambda x: -18.000, y_unit="mm", upper=True),
            Limit_G(codes, func=lambda x: -18.000, y_unit="mm", lower=True),
        ]

    def calculation(self) -> CriterionResult:
        channel = self.require_channel(
            *self.ctx.codes("?{p}CHST0003??DSXC", "?{p}CHST0000??DSXC")
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


class Criterion_Chest_VC(Criterion):
    name = "Chest VC"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}VCCR000[03]??VEX?")
        return [
            Limit_G(codes, func=lambda x: 0.500, y_unit="m/s", upper=True),
            Limit_A(codes, func=lambda x: 0.500, y_unit="m/s", lower=True),
            Limit_M(codes, func=lambda x: 0.667, y_unit="m/s", lower=True),
            Limit_W(codes, func=lambda x: 0.833, y_unit="m/s", lower=True),
            Limit_P(codes, func=lambda x: 1.000, y_unit="m/s"),
            Limit_C(codes, func=lambda x: 1.000, y_unit="m/s", lower=True),
        ]

    def calculation(self) -> CriterionResult:
        channel = self.require_channel(
            *self.ctx.codes("?{p}VCCR0003??VEXC", "?{p}VCCR0000??VEXC")
        ).convert_unit("m/s")
        value = channel.get_data()[np.argmax(np.abs(channel.get_data()))]
        rating = self.limits.get_limit_min_rating(channel, interpolate=True)
        color = self.limits.get_limit_min_color(channel)
        return CriterionResult(
            channel=channel,
            value=value,
            rating=rating,
            color=color,
        )


class Criterion_ShoulderBeltLoad(Criterion):
    name = "Modifier Shoulder Belt Load"
    role = Role.MODIFIER

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}SEBE????B3FO[X0]?")
        return [
            Limit(
                codes,
                name="0 pt. Modifier",
                func=lambda x: 6.0,
                y_unit="kN",
                upper=True,
                color="green",
                rating=0,
            ),
            Limit(
                codes,
                name="-2 pt. Modifier",
                func=lambda x: 6.0,
                y_unit="kN",
                lower=True,
                color="red",
                rating=-2,
            ),
        ]

    def calculation(self) -> CriterionResult:
        channel = self.require_channel(
            self.ctx.code("?{p}SEBE????B3FO[X0]D")
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


class Criterion_Femur_Axial_Force(Criterion):
    name = "Femur Axial Force"
    role = Role.AGGREGATE

    class Criterion_Femur_Axial_Force_Left(Criterion):
        name = "Femur Axial Force Left"

        def define_limits(self) -> list[Limit]:
            codes = self.ctx.codes("?{p}FEMRLE00??FOZ?")
            return [
                Limit_G(codes, func=lambda x: -2.6, y_unit="kN", lower=True),
                Limit_A(codes, func=lambda x: -2.6, y_unit="kN", upper=True),
                Limit_M(codes, func=lambda x: -3.8, y_unit="kN", upper=True),
                Limit_W(codes, func=lambda x: -5.0, y_unit="kN", upper=True),
                Limit_P(codes, func=lambda x: -6.2, y_unit="kN", upper=True),
            ]

        def calculation(self) -> CriterionResult:
            channel = self.require_channel(
                self.ctx.code("?{p}FEMRLE00??FOZB")
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

    class Criterion_Femur_Axial_Force_Right(Criterion):
        name = "Femur Axial Force Right"

        def define_limits(self) -> list[Limit]:
            codes = self.ctx.codes("?{p}FEMRRI00??FOZ?")
            return [
                Limit_G(codes, func=lambda x: -2.6, y_unit="kN", lower=True),
                Limit_A(codes, func=lambda x: -2.6, y_unit="kN", upper=True),
                Limit_M(codes, func=lambda x: -3.8, y_unit="kN", upper=True),
                Limit_W(codes, func=lambda x: -5.0, y_unit="kN", upper=True),
                Limit_P(codes, func=lambda x: -6.2, y_unit="kN", upper=True),
            ]

        def calculation(self) -> CriterionResult:
            channel = self.require_channel(
                self.ctx.code("?{p}FEMRRI00??FOZB")
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

    criterion_femur_axial_force_left = sub(Criterion_Femur_Axial_Force_Left)
    criterion_femur_axial_force_right = sub(Criterion_Femur_Axial_Force_Right)

    def calculation(self) -> CriterionResult:
        value = np.min(
            [
                Criterion.value_of(self.criterion_femur_axial_force_left),
                Criterion.value_of(self.criterion_femur_axial_force_right),
            ]
        )
        rating = self.min_of_children()
        return CriterionResult(
            channel=None,
            value=value,
            rating=rating,
            color=None,
        )


class Criterion_Submarining(Criterion):
    name = "Submarining"
    role = Role.MODIFIER
    submarining: Manual[
        bool,
        manual(
            False,
            source="video",
            doc=("Pelvis slid under the lap belt. Caps the femur box at 0 points."),
        ),
    ]

    def calculation(self) -> CriterionResult:
        value = self.submarining
        rating = -4 if self.submarining else 0
        return CriterionResult(
            channel=None,
            value=value,
            rating=rating,
            color=None,
        )


class Overall(Criterion):
    report: EuroNCAP_Frontal_50kmh
    name = "Overall"
    max_rating = 8.0
    source = "§4"
    role = Role.AGGREGATE
    front_passenger_meets_90_percent: Manual[
        bool,
        manual(
            True,
            source="test report",
            doc=(
                "Does the manufacturer-provided front-passenger dummy score reach 90 % of "
                "the driver's total (§4.3)? When it does not, every front-row body region "
                "is assessed on the worse of driver and front passenger."
            ),
        ),
    ]
    p_driver: Manual[str, P_DRIVER]
    p_front_passenger: Manual[str, P_FRONT_PASSENGER]
    p_rear_passenger: Manual[str, P_REAR_PASSENGER]

    def __init__(self, report: Report[Any], isomme: Isomme) -> None:
        super().__init__(report, isomme)
        # Also at construction, not only before every calculate(): the pages build
        # their channel patterns from p_driver when the report is constructed.
        self.prepare()

    def prepare(self) -> None:
        """
        Fill the seating positions from the test info and from ``p_driver``.

        Runs before the occupants are calculated, which is when their ``from_input()``
        context reads these inputs — so a position set after construction is honoured
        with nothing to rebuild (F15). Idempotent: :meth:`set_derived_input` never
        overrules a value the user assigned.
        """
        p_driver = self.isomme.get_test_info("Driver position object 1")
        if p_driver is not None:
            self.set_derived_input("p_driver", str(p_driver).strip())
        self.derive_positions()

    def derive_positions(self) -> None:
        """
        Fill the passenger positions from ``p_driver``.

        The common case is that only the driver position is known — it comes out
        of the test info, or the user sets it — and the vehicle is either left- or
        right-hand drive. A passenger position the user set explicitly is left
        alone (see :meth:`Criterion.set_derived_input`).
        """
        right_hand_drive = self.p_driver != "1"
        self.set_derived_input("p_front_passenger", "1" if right_hand_drive else "3")
        self.set_derived_input("p_rear_passenger", "4" if right_hand_drive else "6")

    def calculation(self) -> CriterionResult:
        # §4.3: the front row scores the driver. The front passenger enters only
        # when the manufacturer-provided data misses the 90 % requirement — then
        # each body region is taken from the worse of the two front occupants.
        if self.front_passenger_meets_90_percent:
            front_row = Criterion.rating_of(self.criterion_driver)
        else:
            front_row = float(
                np.sum(
                    [
                        np.min(
                            [
                                getattr(self.criterion_driver, attr).rating,
                                getattr(self.criterion_front_passenger, attr).rating,
                            ]
                        )
                        for attr in (
                            "criterion_head",
                            "criterion_neck",
                            "criterion_chest",
                            "criterion_femur",
                        )
                    ]
                )
            )

        # §4.3: front row and rear passenger (16 points each) averaged, then halved.
        rating = (
            float(
                np.nanmean(
                    [front_row, Criterion.rating_of(self.criterion_rear_passenger)]
                )
            )
            / 2
        )
        # Capping (-np.inf) leads to 0 points. More than 8 points should not be possible if sub-criteria defined correctly
        rating = float(np.interp(rating, [0, 8], [0, 8], left=0, right=np.nan))

        rating += self.modifiers_sum()
        return CriterionResult(
            channel=None,
            value=rating,
            rating=rating,
            color=None,
        )

    class Criterion_Driver(Criterion):
        report: EuroNCAP_Frontal_50kmh
        name = "Driver"
        max_rating, aggregation = 16.0, "sum"
        role = Role.AGGREGATE
        steering_wheel_airbag_exists: Manual[
            bool,
            manual(
                True,
                source="test report",
                doc=(
                    "Is a steering-wheel airbag fitted? Without one the head and neck "
                    "boxes score 0."
                ),
            ),
        ]

        def calculation(self) -> CriterionResult:
            rating = value = self.sum_of_children()
            return CriterionResult(
                channel=None,
                value=value,
                rating=rating,
                color=None,
            )

        class Criterion_Head(Criterion):
            report: EuroNCAP_Frontal_50kmh
            name = "Head"
            max_rating = 4.0
            #: Narrower than the root's section; the two rated leaves below inherit
            #: it. The modifiers carry §4.2.1 themselves.
            source = "§4.1.1"
            role = Role.AGGREGATE
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
                if self.report.criterion_overall[
                    self.isomme
                ].criterion_driver.steering_wheel_airbag_exists:
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

                    # The two rated leaves are always calculated — the framework does
                    # it — so the numbers stay visible in the report even when only
                    # the 4 pt. default is scored. Only the aggregation is conditional.
                    if self.hard_contact:
                        rating = self.min_of_children()
                    else:
                        rating = 4
                else:
                    rating = 0

                rating += self.modifiers_sum()
                return CriterionResult(
                    channel=None,
                    value=rating,
                    rating=rating,
                    color=None,
                )

            class Criterion_HazardousAirbagDeployment(Criterion):
                name = "Modifier for Hazardous Airbag Deployment"
                source = "§4.2.1"
                role = Role.MODIFIER
                hazardous_airbag_deployment: Manual[
                    bool,
                    manual(
                        False,
                        source="video",
                        doc=("Hazardous airbag deployment observed. −1 point."),
                    ),
                ]

                def calculation(self) -> CriterionResult:
                    value = self.hazardous_airbag_deployment
                    rating = -1 if self.hazardous_airbag_deployment else 0
                    return CriterionResult(
                        channel=None,
                        value=value,
                        rating=rating,
                        color=None,
                    )

            class Criterion_IncorrectAirbagDeployment(Criterion):
                name = "Modifier for Incorrect Airbag Deployment"
                source = "§4.2.1"
                role = Role.MODIFIER
                incorrect_airbag_deployment: Manual[
                    bool,
                    manual(
                        False,
                        source="video",
                        doc=("Incorrect airbag deployment observed. −1 point."),
                    ),
                ]

                def calculation(self) -> CriterionResult:
                    value = self.incorrect_airbag_deployment
                    rating = -1 if self.incorrect_airbag_deployment else 0
                    return CriterionResult(
                        channel=None,
                        value=value,
                        rating=rating,
                        color=None,
                    )

            class Criterion_DisplacementSteeringColumn(Criterion):
                report: EuroNCAP_Frontal_50kmh
                name = "Modifier for Displacement of Steering Column"
                source = "§4.2.1"
                role = Role.MODIFIER
                displacement_steering_column_rearwards: Manual[
                    float,
                    manual(
                        0.0,
                        unit="mm",
                        source="measurement",
                        doc="Rearward displacement of the steering column (limit 100 mm).",
                    ),
                ]
                displacement_steering_column_upwards: Manual[
                    float,
                    manual(
                        0.0,
                        unit="mm",
                        source="measurement",
                        doc="Upward displacement of the steering column (limit 80 mm).",
                    ),
                ]
                displacement_steering_column_lateral: Manual[
                    float,
                    manual(
                        0.0,
                        unit="mm",
                        source="measurement",
                        doc="Lateral displacement of the steering column (limit 100 mm).",
                    ),
                ]

                def calculation(self) -> CriterionResult:
                    is_driver = self.report.criterion_overall[
                        self.isomme
                    ].p_driver == self.ctx.field("p")

                    if is_driver:
                        rearwards_percent = (
                            self.displacement_steering_column_rearwards / 100
                        )
                        upwards_percent = self.displacement_steering_column_upwards / 80
                        lateral_percent = (
                            self.displacement_steering_column_lateral / 100
                        )

                        value = float(
                            np.max(
                                [rearwards_percent, upwards_percent, lateral_percent]
                            )
                        )
                        rating = float(
                            np.interp(value, [0.9, 1.1], [0, -1], left=0, right=-1)
                        )
                    else:
                        rating = 0
                    return CriterionResult(
                        channel=None,
                        value=value,
                        rating=rating,
                        color=None,
                    )

            #: The leaves themselves live at module level so every occupant can reuse
            #: them; these aliases keep the unmigrated reports' deep class paths
            #: working. TODO(step-10): drop with the shared criteria library.
            Criterion_HIC_15 = Criterion_HIC_15
            Criterion_Head_a3ms = Criterion_Head_a3ms
            Criterion_UnstableAirbagContact = Criterion_UnstableAirbagContact

            criterion_hic_15 = sub(Criterion_HIC_15)
            criterion_head_a3ms = sub(Criterion_Head_a3ms)
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
            report: EuroNCAP_Frontal_50kmh
            name = "Neck"
            max_rating = 4.0
            source = "§4.1.2"
            role = Role.AGGREGATE

            def calculation(self) -> CriterionResult:
                if not self.report.criterion_overall[
                    self.isomme
                ].criterion_driver.steering_wheel_airbag_exists:
                    rating = 0.0
                else:
                    rating = self.min_of_children()
                return CriterionResult(
                    channel=None,
                    value=rating,
                    rating=rating,
                    color=None,
                )

            class Criterion_My_extension(Criterion):
                name = "Neck My extension"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}NECKUP00??MOY?")
                    return [
                        Limit_G(codes, func=lambda x: -36.000, y_unit="Nm", lower=True),
                        Limit_A(codes, func=lambda x: -36.000, y_unit="Nm", upper=True),
                        Limit_M(codes, func=lambda x: -40.333, y_unit="Nm", upper=True),
                        Limit_W(codes, func=lambda x: -44.667, y_unit="Nm", upper=True),
                        Limit_P(codes, func=lambda x: -49.000, y_unit="Nm", upper=True),
                        Limit_C(codes, func=lambda x: -57.000, y_unit="Nm", upper=True),
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

            class Criterion_Fz_tension(Criterion):
                name = "Neck Fz tension"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}NECKUP00??FOZ?")
                    return [
                        Limit_G(codes, func=lambda x: 1.700, y_unit="kN", upper=True),
                        Limit_A(codes, func=lambda x: 1.700, y_unit="kN", lower=True),
                        Limit_M(codes, func=lambda x: 2.007, y_unit="kN", lower=True),
                        Limit_W(codes, func=lambda x: 2.313, y_unit="kN", lower=True),
                        Limit_P(codes, func=lambda x: 2.620, y_unit="kN", lower=True),
                        Limit_C(codes, func=lambda x: 2.900, y_unit="kN", lower=True),
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

            class Criterion_Fx_shear(Criterion):
                name = "Neck Fx shear"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}NECKUP00??FOX?")
                    return [
                        Limit_G(codes, func=lambda x: 1.20, y_unit="kN", upper=True),
                        Limit_A(codes, func=lambda x: 1.20, y_unit="kN", lower=True),
                        Limit_M(codes, func=lambda x: 1.45, y_unit="kN", lower=True),
                        Limit_W(codes, func=lambda x: 1.70, y_unit="kN", lower=True),
                        Limit_P(codes, func=lambda x: 1.95, y_unit="kN", lower=True),
                        Limit_G(codes, func=lambda x: -1.20, y_unit="kN", lower=True),
                        Limit_A(codes, func=lambda x: -1.20, y_unit="kN", upper=True),
                        Limit_M(codes, func=lambda x: -1.45, y_unit="kN", upper=True),
                        Limit_W(codes, func=lambda x: -1.70, y_unit="kN", upper=True),
                        Limit_P(codes, func=lambda x: -1.95, y_unit="kN", upper=True),
                        Limit_C(codes, func=lambda x: 2.70, y_unit="kN", lower=True),
                        Limit_C(codes, func=lambda x: -2.70, y_unit="kN", upper=True),
                    ]

                def calculation(self) -> CriterionResult:
                    channel = self.require_channel(
                        self.ctx.code("?{p}NECKUP00??FOXA")
                    ).convert_unit("kN")
                    value = channel.get_data()[np.argmax(np.abs(channel.get_data()))]
                    rating = self.limits.get_limit_min_rating(channel)
                    color = self.limits.get_limit_min_color(channel)
                    return CriterionResult(
                        channel=channel,
                        value=value,
                        rating=rating,
                        color=color,
                    )

            criterion_my_extension = sub(Criterion_My_extension)
            criterion_fz_tension = sub(Criterion_Fz_tension)
            criterion_fx_shear = sub(Criterion_Fx_shear)

        class Criterion_Chest(Criterion):
            report: EuroNCAP_Frontal_50kmh
            name = "Chest"
            max_rating = 4.0
            source = "§4.1.3"
            role = Role.AGGREGATE

            def calculation(self) -> CriterionResult:
                rating = self.min_of_children()
                rating += self.modifiers_sum()
                return CriterionResult(
                    channel=None,
                    value=rating,
                    rating=rating,
                    color=None,
                )

            class Criterion_SteeringWheelContact(Criterion):
                report: EuroNCAP_Frontal_50kmh
                name = "Modifier Chest Steering Wheel Contact"
                source = "§4.2.2"
                role = Role.MODIFIER
                steering_wheel_contact: Manual[
                    bool,
                    manual(
                        False,
                        source="video",
                        doc=(
                            "Chest contact with the steering wheel (driver only). −1 point."
                        ),
                    ),
                ]

                def calculation(self) -> CriterionResult:
                    is_driver = self.report.criterion_overall[
                        self.isomme
                    ].p_driver == self.ctx.field("p")
                    rating = -1 if is_driver and self.steering_wheel_contact else 0
                    return CriterionResult(
                        channel=None,
                        value=rating,
                        rating=rating,
                        color=None,
                    )

            Criterion_Chest_Deflection = Criterion_Chest_Deflection
            Criterion_Chest_VC = Criterion_Chest_VC
            Criterion_ShoulderBeltLoad = Criterion_ShoulderBeltLoad

            criterion_chest_deflection = sub(Criterion_Chest_Deflection)
            criterion_chest_vc = sub(Criterion_Chest_VC)
            criterion_SteeringWheelContact = sub(Criterion_SteeringWheelContact)
            criterion_shoulder_belt_load = sub(Criterion_ShoulderBeltLoad)

        class Criterion_Femur(Criterion):
            name = "Femur"
            max_rating = 4.0
            source = "§4.1.4"
            role = Role.AGGREGATE

            def calculation(self) -> CriterionResult:
                rating = Criterion.rating_of(self.criterion_femur_axial_force)
                rating += self.modifiers_sum()
                return CriterionResult(
                    channel=None,
                    value=rating,
                    rating=rating,
                    color=None,
                )

            Criterion_Femur_Axial_Force = Criterion_Femur_Axial_Force
            Criterion_Submarining = Criterion_Submarining

            criterion_femur_axial_force = sub(Criterion_Femur_Axial_Force)
            criterion_submarining = sub(Criterion_Submarining)

        criterion_head = sub(Criterion_Head)
        criterion_neck = sub(Criterion_Neck)
        criterion_chest = sub(Criterion_Chest)
        criterion_femur = sub(Criterion_Femur)

    class Criterion_Front_Passenger(Criterion):
        report: EuroNCAP_Frontal_50kmh
        name = "Front Passenger"
        max_rating, aggregation = 16.0, "sum"
        role = Role.AGGREGATE

        def calculation(self) -> CriterionResult:
            rating = value = self.sum_of_children()
            return CriterionResult(
                channel=None,
                value=value,
                rating=rating,
                color=None,
            )

        class Criterion_Head(Criterion):
            report: EuroNCAP_Frontal_50kmh
            name = "Head"
            max_rating = 4.0
            source = "§4.1.1"
            role = Role.AGGREGATE
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

                rating += self.modifiers_sum()
                return CriterionResult(
                    channel=None,
                    value=rating,
                    rating=rating,
                    color=None,
                )

            class Criterion_HazardousAirbagDeployment(Criterion):
                name = "Modifier for Hazardous Airbag Deployment"
                source = "§4.2.1"
                role = Role.MODIFIER
                hazardous_airbag_deployment: Manual[
                    bool,
                    manual(
                        False,
                        source="video",
                        doc=("Hazardous airbag deployment observed. −1 point."),
                    ),
                ]

                def calculation(self) -> CriterionResult:
                    value = self.hazardous_airbag_deployment
                    rating = -1 if self.hazardous_airbag_deployment else 0
                    return CriterionResult(
                        channel=None,
                        value=value,
                        rating=rating,
                        color=None,
                    )

            class Criterion_IncorrectAirbagDeployment(Criterion):
                name = "Modifier for Incorrect Airbag Deployment"
                source = "§4.2.1"
                role = Role.MODIFIER
                incorrect_airbag_deployment: Manual[
                    bool,
                    manual(
                        False,
                        source="video",
                        doc=("Incorrect airbag deployment observed. −1 point."),
                    ),
                ]

                def calculation(self) -> CriterionResult:
                    value = self.incorrect_airbag_deployment
                    rating = -1 if self.incorrect_airbag_deployment else 0
                    return CriterionResult(
                        channel=None,
                        value=value,
                        rating=rating,
                        color=None,
                    )

            criterion_hic_15 = sub(Criterion_HIC_15)
            criterion_head_a3ms = sub(Criterion_Head_a3ms)
            criterion_HazardousAirbagDeployment = sub(
                Criterion_HazardousAirbagDeployment
            )
            criterion_IncorrectAirbagDeployment = sub(
                Criterion_IncorrectAirbagDeployment
            )

        class Criterion_Neck(Criterion):
            name = "Neck"
            max_rating = 4.0
            source = "§4.1.2"
            role = Role.AGGREGATE

            def calculation(self) -> CriterionResult:
                rating = self.min_of_children()
                return CriterionResult(
                    channel=None,
                    value=rating,
                    rating=rating,
                    color=None,
                )

            class Criterion_My_extension(Criterion):
                name = "Neck My extension"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}NECKUP00??MOY?")
                    return [
                        Limit_G(codes, func=lambda x: -36.000, y_unit="Nm", lower=True),
                        Limit_A(codes, func=lambda x: -36.000, y_unit="Nm", upper=True),
                        Limit_M(codes, func=lambda x: -40.333, y_unit="Nm", upper=True),
                        Limit_W(codes, func=lambda x: -44.667, y_unit="Nm", upper=True),
                        Limit_P(codes, func=lambda x: -49.000, y_unit="Nm", upper=True),
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

            class Criterion_Fz_tension(Criterion):
                name = "Neck Fz tension"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}NECKUP00??FOZ?")
                    return [
                        Limit_G(codes, func=lambda x: 1.700, y_unit="kN", upper=True),
                        Limit_A(codes, func=lambda x: 1.700, y_unit="kN", lower=True),
                        Limit_M(codes, func=lambda x: 2.007, y_unit="kN", lower=True),
                        Limit_W(codes, func=lambda x: 2.313, y_unit="kN", lower=True),
                        Limit_P(codes, func=lambda x: 2.620, y_unit="kN", lower=True),
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

            class Criterion_Fx_shear(Criterion):
                name = "Neck Fx shear"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}NECKUP00??FOX?")
                    return [
                        Limit_G(codes, func=lambda x: 1.20, y_unit="kN", upper=True),
                        Limit_A(codes, func=lambda x: 1.20, y_unit="kN", lower=True),
                        Limit_M(codes, func=lambda x: 1.45, y_unit="kN", lower=True),
                        Limit_W(codes, func=lambda x: 1.70, y_unit="kN", lower=True),
                        Limit_P(codes, func=lambda x: 1.95, y_unit="kN", lower=True),
                        Limit_G(codes, func=lambda x: -1.20, y_unit="kN", lower=True),
                        Limit_A(codes, func=lambda x: -1.20, y_unit="kN", upper=True),
                        Limit_M(codes, func=lambda x: -1.45, y_unit="kN", upper=True),
                        Limit_W(codes, func=lambda x: -1.70, y_unit="kN", upper=True),
                        Limit_P(codes, func=lambda x: -1.95, y_unit="kN", upper=True),
                    ]

                def calculation(self) -> CriterionResult:
                    channel = self.require_channel(
                        self.ctx.code("?{p}NECKUP00??FOXA")
                    ).convert_unit("kN")
                    value = channel.get_data()[np.argmax(np.abs(channel.get_data()))]
                    rating = self.limits.get_limit_min_rating(channel)
                    color = self.limits.get_limit_min_color(channel)
                    return CriterionResult(
                        channel=channel,
                        value=value,
                        rating=rating,
                        color=color,
                    )

            criterion_my_extension = sub(Criterion_My_extension)
            criterion_fz_tension = sub(Criterion_Fz_tension)
            criterion_fx_shear = sub(Criterion_Fx_shear)

        class Criterion_Chest(Criterion):
            report: EuroNCAP_Frontal_50kmh
            name = "Chest"
            max_rating = 4.0
            source = "§4.1.3"
            role = Role.AGGREGATE

            def calculation(self) -> CriterionResult:
                rating = self.min_of_children()
                rating += self.modifiers_sum()
                return CriterionResult(
                    channel=None,
                    value=rating,
                    rating=rating,
                    color=None,
                )

            criterion_chest_deflection = sub(Criterion_Chest_Deflection)
            criterion_chest_vc = sub(Criterion_Chest_VC)
            criterion_shoulder_belt_load = sub(Criterion_ShoulderBeltLoad)

        class Criterion_Femur(Criterion):
            report: EuroNCAP_Frontal_50kmh
            name = "Femur"
            max_rating = 4.0
            source = "§4.1.4"
            role = Role.AGGREGATE

            def calculation(self) -> CriterionResult:
                rating = Criterion.rating_of(self.criterion_femur_axial_force)
                return CriterionResult(
                    channel=None,
                    value=rating,
                    rating=rating,
                    color=None,
                )

            criterion_femur_axial_force = sub(Criterion_Femur_Axial_Force)

        criterion_head = sub(Criterion_Head)
        criterion_neck = sub(Criterion_Neck)
        criterion_chest = sub(Criterion_Chest)
        criterion_femur = sub(Criterion_Femur)

    class Criterion_Rear_Passenger(Criterion):
        report: EuroNCAP_Frontal_50kmh
        name = "Rear Passenger"
        max_rating, aggregation = 16.0, "sum"
        role = Role.AGGREGATE

        def calculation(self) -> CriterionResult:
            rating = value = self.sum_of_children()
            return CriterionResult(
                channel=None,
                value=value,
                rating=rating,
                color=None,
            )

        class Criterion_Head(Criterion):
            report: EuroNCAP_Frontal_50kmh
            name = "Head"
            max_rating = 4.0
            source = "§4.1.1.3"
            role = Role.AGGREGATE
            hard_contact: Manual[
                bool,
                manual(
                    True,
                    source="video",
                    doc=(
                        "Was hard head contact seen on the high speed film? §4.1.1.3 has no "
                        "80 g rule for the rear passenger, so this input alone decides. "
                        "Without contact only the 3 ms resultant is scored."
                    ),
                ),
            ]

            def calculation(self) -> CriterionResult:
                # §4.1.1.3: without hard contact on the high speed film the score is
                # based on the 3 ms resultant alone; with hard contact HIC15 is scored
                # alongside it and the worse of the two counts.
                if self.hard_contact:
                    rating = self.min_of_children()
                else:
                    rating = Criterion.rating_of(self.criterion_head_a3ms)

                rating += self.modifiers_sum()
                return CriterionResult(
                    channel=None,
                    value=rating,
                    rating=rating,
                    color=None,
                )

            class Criterion_HazardousAirbagDeployment(Criterion):
                name = "Modifier for Hazardous Airbag Deployment"
                source = "§4.2.1"
                role = Role.MODIFIER
                hazardous_airbag_deployment: Manual[
                    bool,
                    manual(
                        False,
                        source="video",
                        doc=("Hazardous airbag deployment observed. −1 point."),
                    ),
                ]

                def calculation(self) -> CriterionResult:
                    value = self.hazardous_airbag_deployment
                    rating = -1 if self.hazardous_airbag_deployment else 0
                    return CriterionResult(
                        channel=None,
                        value=value,
                        rating=rating,
                        color=None,
                    )

            class Criterion_IncorrectAirbagDeployment(Criterion):
                name = "Modifier for Incorrect Airbag Deployment"
                source = "§4.2.1"
                role = Role.MODIFIER
                incorrect_airbag_deployment: Manual[
                    bool,
                    manual(
                        False,
                        source="video",
                        doc=("Incorrect airbag deployment observed. −1 point."),
                    ),
                ]

                def calculation(self) -> CriterionResult:
                    value = self.incorrect_airbag_deployment
                    rating = -1 if self.incorrect_airbag_deployment else 0
                    return CriterionResult(
                        channel=None,
                        value=value,
                        rating=rating,
                        color=None,
                    )

            class Criterion_ExceedingForwardExcursionLine(Criterion):
                name = "Modifier for Exceeding forward excursion line"
                source = "§4.2.1"
                role = Role.MODIFIER
                forward_excursion: Manual[
                    float,
                    manual(
                        0.0,
                        unit="mm",
                        source="video",
                        doc="Forward head excursion beyond the excursion line.",
                    ),
                ]
                simulation_contact_seat_H3: Manual[
                    bool,
                    manual(
                        False,
                        source="simulation",
                        doc="Hybrid-III simulation shows head contact with the front seat.",
                    ),
                ]
                simulation_hic_15_H3: Manual[
                    float,
                    manual(
                        0.0,
                        source="simulation",
                        doc="HIC15 from the Hybrid-III simulation.",
                    ),
                ]

                def calculation(self) -> CriterionResult:
                    if self.forward_excursion < 450:
                        rating = 0
                    else:
                        if self.forward_excursion < 550:
                            rating = -2
                        else:
                            rating = -4

                        if self.simulation_contact_seat_H3:
                            if self.simulation_hic_15_H3 < 700:
                                rating = 0
                        else:
                            rating = 0
                    return CriterionResult(
                        channel=None,
                        value=rating,
                        rating=rating,
                        color=None,
                    )

            criterion_hic_15 = sub(Criterion_HIC_15)
            criterion_head_a3ms = sub(Criterion_Head_a3ms)
            criterion_UnstableAirbagContact = sub(Criterion_UnstableAirbagContact)
            criterion_HazardousAirbagDeployment = sub(
                Criterion_HazardousAirbagDeployment
            )
            criterion_IncorrectAirbagDeployment = sub(
                Criterion_IncorrectAirbagDeployment
            )
            criterion_ExceedingForwardExcursionLine = sub(
                Criterion_ExceedingForwardExcursionLine
            )

        class Criterion_Neck(Criterion):
            name = "Neck"
            max_rating, aggregation = 4.0, "sum"
            source = "§4.1.2"
            role = Role.AGGREGATE

            def calculation(self) -> CriterionResult:
                rating = self.sum_of_children()
                return CriterionResult(
                    channel=None,
                    value=rating,
                    rating=rating,
                    color=None,
                )

            class Criterion_My_extension(Criterion):
                name = "Neck My extension"
                max_rating: float = 2.0
                validate_ignore = {
                    "max_rating": "shared 4 pt. limit block rescaled to the §4.1.2 rear-passenger budget"
                }

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}NECKUP00??MOY?")
                    return [
                        Limit_G(codes, func=lambda x: -36.000, y_unit="Nm", lower=True),
                        Limit_A(codes, func=lambda x: -36.000, y_unit="Nm", upper=True),
                        Limit_M(codes, func=lambda x: -40.333, y_unit="Nm", upper=True),
                        Limit_W(codes, func=lambda x: -44.667, y_unit="Nm", upper=True),
                        Limit_P(codes, func=lambda x: -49.000, y_unit="Nm", upper=True),
                    ]

                def calculation(self) -> CriterionResult:
                    channel = self.require_channel(
                        self.ctx.code("?{p}NECKUP00??MOYB")
                    ).convert_unit("Nm")
                    value = np.min(channel.get_data())
                    # Rescale the 4 pt. block onto the rear passenger's 2 pt. budget.
                    rating = (
                        self.limits.get_limit_min_rating(channel) * self.max_rating / 4
                    )
                    color = self.limits.get_limit_min_color(channel)
                    return CriterionResult(
                        channel=channel,
                        value=value,
                        rating=rating,
                        color=color,
                    )

            class Criterion_Fz_tension(Criterion):
                name = "Neck Fz tension"
                max_rating: float = 1.0
                validate_ignore = {
                    "max_rating": "shared 4 pt. limit block rescaled to the §4.1.2 rear-passenger budget"
                }

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}NECKUP00??FOZ?")
                    return [
                        Limit_G(codes, func=lambda x: 1.700, y_unit="kN", upper=True),
                        Limit_A(codes, func=lambda x: 1.700, y_unit="kN", lower=True),
                        Limit_M(codes, func=lambda x: 2.007, y_unit="kN", lower=True),
                        Limit_W(codes, func=lambda x: 2.313, y_unit="kN", lower=True),
                        Limit_P(codes, func=lambda x: 2.620, y_unit="kN", lower=True),
                    ]

                def calculation(self) -> CriterionResult:
                    channel = self.require_channel(
                        self.ctx.code("?{p}NECKUP00??FOZA")
                    ).convert_unit("kN")
                    value = np.max(channel.get_data())
                    # Rescale the 4 pt. block onto the rear passenger's 1 pt. budget.
                    rating = (
                        self.limits.get_limit_min_rating(channel) * self.max_rating / 4
                    )
                    color = self.limits.get_limit_min_color(channel)
                    return CriterionResult(
                        channel=channel,
                        value=value,
                        rating=rating,
                        color=color,
                    )

            class Criterion_Fx_shear(Criterion):
                name = "Neck Fx shear"
                max_rating: float = 1.0
                validate_ignore = {
                    "max_rating": "shared 4 pt. limit block rescaled to the §4.1.2 rear-passenger budget"
                }

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}NECKUP00??FOX?")
                    return [
                        Limit_G(codes, func=lambda x: 1.20, y_unit="kN", upper=True),
                        Limit_A(codes, func=lambda x: 1.20, y_unit="kN", lower=True),
                        Limit_M(codes, func=lambda x: 1.45, y_unit="kN", lower=True),
                        Limit_W(codes, func=lambda x: 1.70, y_unit="kN", lower=True),
                        Limit_P(codes, func=lambda x: 1.95, y_unit="kN", lower=True),
                        Limit_G(codes, func=lambda x: -1.20, y_unit="kN", lower=True),
                        Limit_A(codes, func=lambda x: -1.20, y_unit="kN", upper=True),
                        Limit_M(codes, func=lambda x: -1.45, y_unit="kN", upper=True),
                        Limit_W(codes, func=lambda x: -1.70, y_unit="kN", upper=True),
                        Limit_P(codes, func=lambda x: -1.95, y_unit="kN", upper=True),
                    ]

                def calculation(self) -> CriterionResult:
                    channel = self.require_channel(
                        self.ctx.code("?{p}NECKUP00??FOXA")
                    ).convert_unit("kN")
                    value = channel.get_data()[np.argmax(np.abs(channel.get_data()))]
                    # Rescale the 4 pt. block onto the rear passenger's 1 pt. budget.
                    rating = (
                        self.limits.get_limit_min_rating(channel) * self.max_rating / 4
                    )
                    color = self.limits.get_limit_min_color(channel)
                    return CriterionResult(
                        channel=channel,
                        value=value,
                        rating=rating,
                        color=color,
                    )

            criterion_my_extension = sub(Criterion_My_extension)
            criterion_fz_tension = sub(Criterion_Fz_tension)
            criterion_fx_shear = sub(Criterion_Fx_shear)

        class Criterion_Chest(Criterion):
            report: EuroNCAP_Frontal_50kmh
            name = "Chest"
            max_rating = 4.0
            source = "§4.1.3"
            role = Role.AGGREGATE

            def calculation(self) -> CriterionResult:
                rating = self.min_of_children()
                rating += self.modifiers_sum()
                return CriterionResult(
                    channel=None,
                    value=rating,
                    rating=rating,
                    color=None,
                )

            criterion_chest_deflection = sub(Criterion_Chest_Deflection)
            criterion_chest_vc = sub(Criterion_Chest_VC)
            criterion_shoulder_belt_load = sub(Criterion_ShoulderBeltLoad)

        class Criterion_Femur(Criterion):
            report: EuroNCAP_Frontal_50kmh
            name = "Femur"
            max_rating = 4.0
            source = "§4.1.4"
            role = Role.AGGREGATE

            def calculation(self) -> CriterionResult:
                rating = Criterion.rating_of(self.criterion_femur_axial_force)
                rating += self.modifiers_sum()
                return CriterionResult(
                    channel=None,
                    value=rating,
                    rating=rating,
                    color=None,
                )

            criterion_femur_axial_force = sub(Criterion_Femur_Axial_Force)
            criterion_submarining = sub(Criterion_Submarining)

        criterion_head = sub(Criterion_Head)
        criterion_neck = sub(Criterion_Neck)
        criterion_chest = sub(Criterion_Chest)
        criterion_femur = sub(Criterion_Femur)

    class Criterion_DoorOpeningDuringImpact(Criterion):
        name: str = "Door Opening During Impact"
        role = Role.MODIFIER
        number_of_door_openings_during_impact: Manual[
            int,
            manual(
                0,
                source="test report",
                doc=("How many doors opened during the impact. −1 point each."),
            ),
        ]

        def calculation(self) -> CriterionResult:
            value = self.number_of_door_openings_during_impact
            rating = -1 * self.number_of_door_openings_during_impact
            return CriterionResult(
                channel=None,
                value=value,
                rating=rating,
                color=None,
            )

    criterion_driver = sub(Criterion_Driver, at=from_input(P_DRIVER))
    criterion_front_passenger = sub(
        Criterion_Front_Passenger, at=from_input(P_FRONT_PASSENGER)
    )
    criterion_rear_passenger = sub(
        Criterion_Rear_Passenger, at=from_input(P_REAR_PASSENGER)
    )
    #: No `at=`: a vehicle-level criterion inherits the root context and needs no occupant.
    criterion_door_opening_during_impact = sub(Criterion_DoorOpeningDuringImpact)


class EuroNCAP_Frontal_50kmh(Report[Overall]):
    _name = (
        "Euro NCAP | Frontal-Impact against Rigid Wall with 100 % Overlap at 50 km/h"
    )
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
            self.Page_Driver_HIC15(self),
            self.Page_Driver_Neck_Load(self),
            self.Page_Driver_Neck_NIJ(self),
            self.Page_Driver_Chest_Deflection(self),
            self.Page_Driver_Femur_Axial_Force(self),
            self.Page_Front_Passenger_Result_Values_Chart(self),
            self.Page_Front_Passenger_Rating_Table(self),
            self.Page_Front_Passenger_Values_Table(self),
            self.Page_Front_Passenger_Belt(self),
            self.Page_Front_Passenger_Head_Acceleration(self),
            self.Page_Front_Passenger_HIC15(self),
            self.Page_Front_Passenger_Neck_Load(self),
            self.Page_Front_Passenger_Neck_NIJ(self),
            self.Page_Front_Passenger_Chest_Deflection(self),
            self.Page_Front_Passenger_Femur_Axial_Force(self),
            self.Page_Rear_Passenger_Result_Values_Chart(self),
            self.Page_Rear_Passenger_Rating_Table(self),
            self.Page_Rear_Passenger_Values_Table(self),
            self.Page_Rear_Passenger_Belt(self),
            self.Page_Rear_Passenger_Head_Acceleration(self),
            self.Page_Rear_Passenger_HIC15(self),
            self.Page_Rear_Passenger_Neck_Load(self),
            self.Page_Rear_Passenger_Chest_Deflection(self),
            self.Page_Rear_Passenger_Femur_Axial_Force(self),
            Page_OLC(self),
        )
        self._selected_pages = list(self._available_pages)

    class Page_Rating_Table(Page_Criterion_Rating_Table):
        report: EuroNCAP_Frontal_50kmh
        name = "Rating"
        title = "Rating"

        def __init__(self, report: EuroNCAP_Frontal_50kmh) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[isomme].criterion_driver,
                    self.report.criterion_overall[isomme].criterion_front_passenger,
                    self.report.criterion_overall[isomme].criterion_rear_passenger,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_door_opening_during_impact,
                    self.report.criterion_overall[isomme],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Driver_Result_Values_Chart(Page_Criterion_Values_Chart):
        report: EuroNCAP_Frontal_50kmh
        name = "Driver Result Values Chart"
        title = "Driver Result"

        def __init__(self, report: EuroNCAP_Frontal_50kmh) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_head.criterion_hic_15,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_head.criterion_head_a3ms,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_neck.criterion_my_extension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_neck.criterion_fz_tension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_neck.criterion_fx_shear,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_chest.criterion_shoulder_belt_load,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_chest.criterion_chest_deflection,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_chest.criterion_chest_vc,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_left,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_right,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Driver_Values_Table(Page_Criterion_Values_Table):
        report: EuroNCAP_Frontal_50kmh
        name = "Driver Values Table"
        title = "Driver Values"

        def __init__(self, report: EuroNCAP_Frontal_50kmh) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_head.criterion_hic_15,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_head.criterion_head_a3ms,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_neck.criterion_my_extension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_neck.criterion_fz_tension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_neck.criterion_fx_shear,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_chest.criterion_shoulder_belt_load,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_chest.criterion_chest_deflection,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_chest.criterion_chest_vc,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_left,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_right,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Driver_Rating_Table(Page_Criterion_Rating_Table):
        report: EuroNCAP_Frontal_50kmh
        name: str = "Driver Rating Table"
        title: str = "Driver Rating"

        def __init__(self, report: EuroNCAP_Frontal_50kmh) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_head,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_neck,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_chest,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_femur,
                    self.report.criterion_overall[isomme].criterion_driver,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Driver_Belt(Page_Plot_nxn):
        name: str = "Driver Belt"
        title: str = "Driver Belt"
        nrows: int = 3
        ncols: int = 2
        sharey: bool = False

        def __init__(self, report: Report[Any]) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}SEBE000[30]B1FO[X0]C"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}SEBE000[30]B2FO[X0]C"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}SEBE000[30]B3FO[X0]C"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}SEBE000[30]B4FO[X0]C"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}SEBE000[30]B5FO[X0]C"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}SEBE000[30]B6FO[X0]C"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class _Page_Head_Acceleration(Page_Plot_nxn):
        nrows: int = 2
        ncols: int = 2
        sharey: bool = True
        position_attribute: str

        def __init__(self, report: Report[Any]) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{getattr(self.report.criterion_overall[isomme], self.position_attribute)}HEAD??????AC{direction}A"
                    ]
                    for direction in "XYZR"
                ]
                for isomme in self.report.isomme_list
            }

    class _Page_HIC15(Page_Line_Table):
        nrows: int = 1
        ncols: int = 2
        position_attribute: str

        @staticmethod
        def _time_ms(channel: Any, label: str) -> float | None:
            value = channel.get_info(label)
            try:
                time_ms = float(value) * 1000
            except (TypeError, ValueError):
                return None
            return time_ms if np.isfinite(time_ms) else None

        def __init__(self, report: EuroNCAP_Frontal_50kmh) -> None:
            super().__init__(report)
            self.channels = {}
            self.hic_channel_patterns: dict[Isomme, tuple[str, str]] = {}
            for isomme in self.report.isomme_list:
                position = getattr(
                    self.report.criterion_overall[isomme], self.position_attribute
                )
                self.channels[isomme] = [[f"?{position}HEAD??????ACRA"]]
                self.hic_channel_patterns[isomme] = (
                    f"?{position}HICR0015??00RX",
                    f"?{position}HICRCG15??00RX",
                )

        def figure(self, figsize: tuple[float, float]) -> Figure:
            hic_data: list[tuple[Isomme, float, float | None, float | None]] = []
            for isomme in self.report.isomme_list:
                channel = isomme.get_channel(*self.hic_channel_patterns[isomme])
                if channel is None or len(channel.data) == 0:
                    hic_data.append((isomme, np.nan, None, None))
                    continue
                hic_data.append(
                    (
                        isomme,
                        float(channel.get_data()[0]),
                        self._time_ms(channel, ".Start time"),
                        self._time_ms(channel, ".End time"),
                    )
                )

            cell_texts: list[np.ndarray[Any, Any] | list[list[Any]]] = [
                [
                    [
                        f"{hic:.1f}" if np.isfinite(hic) else "n/a",
                        f"{start_ms:.2f}" if start_ms is not None else "n/a",
                        f"{end_ms:.2f}" if end_ms is not None else "n/a",
                    ]
                    for _, hic, start_ms, end_ms in hic_data
                ]
            ]
            col_labels: list[np.ndarray[Any, Any] | list[Any]] = [
                ["HIC15", "Start [ms]", "End [ms]"]
            ]
            row_labels: list[np.ndarray[Any, Any] | list[Any]] = [
                [isomme.test_number for isomme in self.report.isomme_list]
            ]
            plot = Plot_Line_Table(
                channels=self.channels,
                cell_texts=cell_texts,
                row_labels=row_labels,
                col_labels=col_labels,
                nrows=self.nrows,
                ncols=self.ncols,
                sharex=self.sharex,
                sharey=self.sharey,
                xlim=self.xlim,
                ylim=self.ylim,
                limits=self.report.limits,
                figsize=figsize,
            )

            resultant_ax = plot.fig.axes[0]
            hic_ax = resultant_ax.twinx()
            hic_ax.set_ylabel("HIC15 [-]")
            hic_ax.grid(False)
            hic_ax.patch.set_visible(False)  # pyright: ignore[reportAttributeAccessIssue]

            x_min, x_max = resultant_ax.get_xlim()
            finite_hic_values = []
            for idx, (isomme, hic, start_ms, end_ms) in enumerate(hic_data):
                if np.isfinite(hic):
                    finite_hic_values.append(hic)
                    if start_ms is not None and end_ms is not None:
                        hic_ax.plot(
                            [x_min, start_ms, start_ms, end_ms, end_ms, x_max],
                            [0, 0, hic, hic, 0, 0],
                            color=plot.colors[idx % len(plot.colors)],
                            linestyle="--",
                            linewidth=1.5,
                            label=f"{isomme.test_number} HIC15",
                        )

            hic_max = max(finite_hic_values, default=1.0)
            hic_ax.set_ylim(0, max(1.0, hic_max * 1.1))
            if hic_ax.lines:
                hic_ax.legend(loc="upper left")

            return plot.fig

    class Page_Driver_Head_Acceleration(_Page_Head_Acceleration):
        name: str = "Driver Head Acceleration"
        title: str = "Driver Head Acceleration"
        position_attribute = "p_driver"

    class Page_Driver_HIC15(_Page_HIC15):
        name: str = "Driver HIC15"
        title: str = "Driver HIC15"
        position_attribute = "p_driver"

    class Page_Driver_Neck_Load(Page_Plot_nxn):
        name: str = "Driver Neck Load"
        title: str = "Driver Neck Load"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = False

        def __init__(self, report: Report[Any]) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}NECKUP00??MOYB"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}NECKUP00??FOZA"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}NECKUP00??FOXA"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Driver_Neck_NIJ(Page_Plot_nxn):
        report: EuroNCAP_Frontal_50kmh
        name: str = "Driver Neck NIJ"
        title: str = "Driver Neck NIJ"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: EuroNCAP_Frontal_50kmh) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}NIJCIPCF??00YB"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}NIJCIPCE??00YB"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}NIJCIPTF??00YB"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}NIJCIPTE??00YB"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Driver_Chest_Deflection(Page_Plot_nxn):
        name: str = "Driver Chest Deflection"
        title: str = "Driver Chest Deflection"
        nrows: int = 1
        ncols: int = 2

        def __init__(self, report: Report[Any]) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}CHST000???DSXC"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}VCCR000???VEXC"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Driver_Femur_Axial_Force(Page_Plot_nxn):
        name: str = "Driver Femur Axial Force"
        title: str = "Driver Femur Axial Force"
        nrows: int = 1
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: Report[Any]) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}FEMRLE00??FOZB"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_driver}FEMRRI00??FOZB"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Front_Passenger_Result_Values_Chart(Page_Criterion_Values_Chart):
        report: EuroNCAP_Frontal_50kmh
        name = "Front Passenger Result Values Chart"
        title = "Front Passenger Result"

        def __init__(self, report: EuroNCAP_Frontal_50kmh) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_head.criterion_hic_15,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_head.criterion_head_a3ms,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_neck.criterion_my_extension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_neck.criterion_fz_tension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_neck.criterion_fx_shear,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_chest.criterion_shoulder_belt_load,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_chest.criterion_chest_deflection,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_chest.criterion_chest_vc,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_left,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_right,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Front_Passenger_Rating_Table(Page_Criterion_Rating_Table):
        report: EuroNCAP_Frontal_50kmh
        name: str = "Front Passenger Rating Table"
        title: str = "Front Passenger Rating"

        def __init__(self, report: EuroNCAP_Frontal_50kmh) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_head,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_neck,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_chest,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_femur,
                    self.report.criterion_overall[isomme].criterion_front_passenger,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Front_Passenger_Values_Table(Page_Criterion_Values_Table):
        report: EuroNCAP_Frontal_50kmh
        name: str = "Front Passenger Values Table"
        title: str = "Front Passenger Values"

        def __init__(self, report: EuroNCAP_Frontal_50kmh) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_head.criterion_hic_15,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_head.criterion_head_a3ms,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_neck.criterion_my_extension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_neck.criterion_fz_tension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_neck.criterion_fx_shear,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_chest.criterion_shoulder_belt_load,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_chest.criterion_chest_deflection,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_chest.criterion_chest_vc,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_left,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_front_passenger.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_right,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Front_Passenger_Belt(Page_Plot_nxn):
        report: EuroNCAP_Frontal_50kmh
        name: str = "Front Passenger Belt"
        title: str = "Front Passenger Belt"
        nrows: int = 3
        ncols: int = 2
        sharey: bool = False

        def __init__(self, report: EuroNCAP_Frontal_50kmh) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_front_passenger}SEBE000[30]B1FO[X0]C"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_front_passenger}SEBE000[30]B2FO[X0]C"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_front_passenger}SEBE000[30]B3FO[X0]C"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_front_passenger}SEBE000[30]B4FO[X0]C"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_front_passenger}SEBE000[30]B5FO[X0]C"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_front_passenger}SEBE000[30]B6FO[X0]C"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Front_Passenger_Head_Acceleration(_Page_Head_Acceleration):
        report: EuroNCAP_Frontal_50kmh
        name: str = "Front Passenger Head Acceleration"
        title: str = "Front Passenger Head Acceleration"
        position_attribute = "p_front_passenger"

    class Page_Front_Passenger_HIC15(_Page_HIC15):
        name: str = "Front Passenger HIC15"
        title: str = "Front Passenger HIC15"
        position_attribute = "p_front_passenger"

    class Page_Front_Passenger_Neck_Load(Page_Plot_nxn):
        report: EuroNCAP_Frontal_50kmh
        name: str = "Front Passenger Neck Load"
        title: str = "Front Passenger Neck Load"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = False

        def __init__(self, report: EuroNCAP_Frontal_50kmh) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_front_passenger}NECKUP00??MOYB"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_front_passenger}NECKUP00??FOZA"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_front_passenger}NECKUP00??FOXA"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Front_Passenger_Neck_NIJ(Page_Plot_nxn):
        report: EuroNCAP_Frontal_50kmh
        name: str = "Front Passenger Neck NIJ"
        title: str = "Front Passenger Neck NIJ"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: EuroNCAP_Frontal_50kmh) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_front_passenger}NIJCIPCF??00YB"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_front_passenger}NIJCIPCE??00YB"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_front_passenger}NIJCIPTF??00YB"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_front_passenger}NIJCIPTE??00YB"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Front_Passenger_Chest_Deflection(Page_Plot_nxn):
        report: EuroNCAP_Frontal_50kmh
        name: str = "Front Passenger Chest Deflection"
        title: str = "Front Passenger Chest Deflection"
        nrows: int = 1
        ncols: int = 1

        def __init__(self, report: EuroNCAP_Frontal_50kmh) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_front_passenger}CHST000???DSXC"
                    ]
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Front_Passenger_Femur_Axial_Force(Page_Plot_nxn):
        report: EuroNCAP_Frontal_50kmh
        name: str = "Front Passenger Femur Axial Force"
        title: str = "Front Passenger Femur Axial Force"
        nrows: int = 1
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: EuroNCAP_Frontal_50kmh) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_front_passenger}FEMRLE00??FOZB"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_front_passenger}FEMRRI00??FOZB"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Rear_Passenger_Result_Values_Chart(Page_Criterion_Values_Chart):
        report: EuroNCAP_Frontal_50kmh
        name = "Rear Passenger Result Values Chart"
        title = "Rear Passenger Result"

        def __init__(self, report: EuroNCAP_Frontal_50kmh) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_head.criterion_hic_15,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_head.criterion_head_a3ms,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_neck.criterion_my_extension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_neck.criterion_fz_tension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_neck.criterion_fx_shear,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_chest.criterion_shoulder_belt_load,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_chest.criterion_chest_deflection,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_chest.criterion_chest_vc,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_left,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_right,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Rear_Passenger_Rating_Table(Page_Criterion_Rating_Table):
        report: EuroNCAP_Frontal_50kmh
        name: str = "Rear Passenger Result Table"
        title: str = "Rear Passenger Result"

        def __init__(self, report: EuroNCAP_Frontal_50kmh) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_head,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_neck,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_chest,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_femur,
                    self.report.criterion_overall[isomme].criterion_rear_passenger,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Rear_Passenger_Values_Table(Page_Criterion_Values_Table):
        report: EuroNCAP_Frontal_50kmh
        name = "Rear Passenger Values Table"
        title = "Rear Passenger Values"

        def __init__(self, report: EuroNCAP_Frontal_50kmh) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_head.criterion_hic_15,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_head.criterion_head_a3ms,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_neck.criterion_my_extension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_neck.criterion_fz_tension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_neck.criterion_fx_shear,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_chest.criterion_shoulder_belt_load,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_chest.criterion_chest_deflection,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_chest.criterion_chest_vc,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_left,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_rear_passenger.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_right,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Rear_Passenger_Belt(Page_Plot_nxn):
        report: EuroNCAP_Frontal_50kmh
        name: str = "Rear Passenger Belt"
        title: str = "Rear Passenger Belt"
        nrows: int = 3
        ncols: int = 2
        sharey: bool = False

        def __init__(self, report: EuroNCAP_Frontal_50kmh) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_rear_passenger}SEBE000[30]B1FO[X0]C"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_rear_passenger}SEBE000[30]B2FO[X0]C"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_rear_passenger}SEBE000[30]B3FO[X0]C"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_rear_passenger}SEBE000[30]B4FO[X0]C"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_rear_passenger}SEBE000[30]B5FO[X0]C"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_rear_passenger}SEBE000[30]B6FO[X0]C"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Rear_Passenger_Head_Acceleration(_Page_Head_Acceleration):
        report: EuroNCAP_Frontal_50kmh
        name: str = "Rear Passenger Head Acceleration"
        title: str = "Rear Passenger Head Acceleration"
        position_attribute = "p_rear_passenger"

    class Page_Rear_Passenger_HIC15(_Page_HIC15):
        name: str = "Rear Passenger HIC15"
        title: str = "Rear Passenger HIC15"
        position_attribute = "p_rear_passenger"

    class Page_Rear_Passenger_Neck_Load(Page_Plot_nxn):
        report: EuroNCAP_Frontal_50kmh
        name: str = "Rear Passenger Neck Load"
        title: str = "Rear Passenger Neck Load"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = False

        def __init__(self, report: EuroNCAP_Frontal_50kmh) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_rear_passenger}NECKUP00??MOYB"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_rear_passenger}NECKUP00??FOZA"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_rear_passenger}NECKUP00??FOXA"
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Rear_Passenger_Chest_Deflection(Page_Plot_nxn):
        report: EuroNCAP_Frontal_50kmh
        name: str = "Rear Passenger Chest Deflection"
        title: str = "Rear Passenger Chest Deflection"
        nrows: int = 1
        ncols: int = 1

        def __init__(self, report: EuroNCAP_Frontal_50kmh) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_rear_passenger}CHST000???DSXC"
                    ]
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Rear_Passenger_Femur_Axial_Force(Page_Plot_nxn):
        report: EuroNCAP_Frontal_50kmh
        name: str = "Rear Passenger Femur Axial Force"
        title: str = "Rear Passenger Femur Axial Force"
        nrows: int = 1
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: EuroNCAP_Frontal_50kmh) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        f"?{self.report.criterion_overall[isomme].p_rear_passenger}FEMRLE00??FOZB"
                    ],
                    [
                        f"?{self.report.criterion_overall[isomme].p_rear_passenger}FEMRRI00??FOZB"
                    ],
                ]
                for isomme in self.report.isomme_list
            }
