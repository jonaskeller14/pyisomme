from __future__ import annotations

from typing import Any, cast

import numpy as np
import pandas as pd

from pyisomme.channel import Channel
from pyisomme.isomme import Isomme
from pyisomme.limit import Limit
from pyisomme.report.criterion import Criterion, Role, sub
from pyisomme.report.ctx import from_input
from pyisomme.report.iihs.frontal import (
    Criterion_Foot_Acceleration as Criterion_Foot_Acceleration_H350M,
    Criterion_H350M_Injury,
    Criterion_Leg_Foot as Criterion_Leg_Foot_H350M,
    Criterion_Tibia_Axial_Force as Criterion_Tibia_Axial_Force_H350M,
    Criterion_Tibia_Femur_Displacement as Criterion_Tibia_Femur_Displacement_H350M,
    Criterion_Tibia_Index as Criterion_Tibia_Index_H350M,
)
from pyisomme.report.iihs.limits import (
    Limit_A,
    Limit_G,
    Limit_M,
    Limit_P,
)
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

P_DRIVER = manual(
    "1",
    source="test report",
    doc="Channel-code position of the H350M driver.",
)
P_REAR_PASSENGER = manual(
    "6",
    source="test report",
    doc="Channel-code position of the H35F rear occupant; derived from the driver side by default.",
)


class Overall(Criterion):
    name = "Overall"
    role = Role.AGGREGATE
    source = "Weighting principles for overall ratings / Table 9"
    aggregation = "sum"
    p_driver: Manual[str, P_DRIVER]
    p_rear_passenger: Manual[str, P_REAR_PASSENGER]

    def __init__(self, report: Report[Any], isomme: Isomme) -> None:
        super().__init__(report, isomme)
        self.prepare()

    def prepare(self) -> None:
        position = self.isomme.get_test_info("Driver position object 1")
        if position is not None:
            self.set_derived_input("p_driver", str(position).strip())
        self.set_derived_input("p_rear_passenger", "6" if self.p_driver == "1" else "4")

    class Criterion_Driver(Criterion_H350M_Injury):
        name = "Driver"
        aggregation = "sum"

        class Criterion_Leg_Foot(Criterion_Leg_Foot_H350M):
            class Criterion_Tibia_Femur_Displacement(Criterion_Tibia_Femur_Displacement_H350M):
                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}KNSL??00??DSX?")
                    return [
                        Limit_G(codes, lambda x: -12, y_unit="mm", lower=True, rating=0),
                        Limit_A(codes, lambda x: -12, y_unit="mm", upper=True, rating=-1),
                        Limit_M(codes, lambda x: -15, y_unit="mm", upper=True, rating=-4),
                        Limit_P(codes, lambda x: -18, y_unit="mm", upper=True, rating=-6),
                    ]

            class Criterion_Tibia_Index(Criterion_Tibia_Index_H350M):
                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}TIIN??TO??000?")
                    return [
                        Limit_G(codes, lambda x: 0.8, y_unit=1, upper=True, rating=0),
                        Limit_A(codes, lambda x: 1.0, y_unit=1, upper=True, rating=-1),
                        Limit_M(codes, lambda x: 1.2, y_unit=1, upper=True, rating=-4),
                        Limit_P(codes, lambda x: 1.2, y_unit=1, lower=True, rating=-6),
                    ]

            class Criterion_Tibia_Axial_Force(Criterion_Tibia_Axial_Force_H350M):
                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}TIBI??LO??FOZ?")
                    return [
                        Limit_G(codes, lambda x: -4, y_unit="kN", lower=True, rating=0),
                        Limit_A(codes, lambda x: -4, y_unit="kN", upper=True, rating=-1),
                        Limit_M(codes, lambda x: -6, y_unit="kN", upper=True, rating=-4),
                        Limit_P(codes, lambda x: -8, y_unit="kN", upper=True, rating=-6),
                    ]

            class Criterion_Foot_Acceleration(Criterion_Foot_Acceleration_H350M):
                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}FOOT??00??ACR?")
                    return [
                        Limit_G(codes, lambda x: 150, y_unit=Unit(g0), upper=True, rating=0),
                        Limit_A(codes, lambda x: 200, y_unit=Unit(g0), upper=True, rating=-1),
                        Limit_M(codes, lambda x: 260, y_unit=Unit(g0), upper=True, rating=-4),
                        Limit_P(codes, lambda x: 260, y_unit=Unit(g0), lower=True, rating=-6),
                    ]

            criterion_tibia_femur_displacement = sub(Criterion_Tibia_Femur_Displacement)
            criterion_tibia_index = sub(Criterion_Tibia_Index)
            criterion_tibia_axial_force = sub(Criterion_Tibia_Axial_Force)
            criterion_foot_acceleration = sub(Criterion_Foot_Acceleration)

        class Criterion_Restraints_Kinematics(Criterion):
            name = "Restraints and kinematics"
            demerits: Manual[int, manual(
                0,
                source="video and postcrash inspection",
                doc="Sum the H350M driver events in Table 3.",
            )]

            def calculation(self) -> None:
                self.value = float(self.demerits)
                if self.value <= 1:
                    self.rating, self.color = 0.0, Limit_G.color
                elif self.value <= 5:
                    self.rating, self.color = -1.0, Limit_A.color
                elif self.value <= 9:
                    self.rating, self.color = -4.0, Limit_M.color
                else:
                    self.rating, self.color = -6.0, Limit_P.color

        criterion_leg_foot = sub(Criterion_Leg_Foot)
        criterion_restraints_kinematics = sub(Criterion_Restraints_Kinematics)

        def calculation(self) -> None:
            self.rating = self.sum_of_children()
            self.value = -self.rating

    class Criterion_Rear_Passenger(Criterion):
        name = "Rear passenger"
        role = Role.AGGREGATE
        aggregation = "sum"

        class Criterion_Head_Neck(Criterion):
            name = "Head and neck"
            role = Role.AGGREGATE
            aggregation = "min"
            interior_contact: Manual[bool, manual(
                False,
                source="video",
                doc="A primary-loading contact with the vehicle interior makes HIC-15 and Nij applicable.",
            )]
            hard_contact_over_70g: Manual[bool, manual(
                False,
                source="video and head acceleration",
                doc="Contact produced a resultant head acceleration above 70 g; downgrade one level.",
            )]

            def injury_values_apply(self) -> bool:
                return self.interior_contact

            class Criterion_HIC_15(Criterion):
                name = "HIC 15 (contacts only)"
                validate_ignore = {
                    "limit_flags": "discrete demerits use successive upper bounds with interpolation disabled",
                }

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}HICR0015??00RX")
                    return [
                        Limit_G(codes, lambda x: 560, y_unit=1, upper=True, rating=0),
                        Limit_A(codes, lambda x: 700, y_unit=1, upper=True, rating=-2),
                        Limit_M(codes, lambda x: 840, y_unit=1, upper=True, rating=-10),
                        Limit_P(codes, lambda x: 840, y_unit=1, lower=True, rating=-20),
                    ]

                def calculation(self) -> None:
                    parent = cast(
                        "Overall.Criterion_Rear_Passenger.Criterion_Head_Neck | None",
                        self.parent,
                    )
                    if parent is not None and not parent.injury_values_apply():
                        self.value = np.nan
                        self.rating, self.color = 0.0, Limit_G.color
                        return
                    self.channel = self.require_channel(self.ctx.code("?{p}HICR0015??00RX"))
                    self.value = float(self.channel.get_data()[0])
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Nij(Criterion):
                name = "Nij (contacts only)"
                validate_ignore = {
                    "limit_flags": "discrete demerits use successive upper bounds with interpolation disabled",
                }

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}NIJCIP00??00Y?")
                    return [
                        Limit_G(codes, lambda x: 0.8, y_unit=1, upper=True, rating=0),
                        Limit_A(codes, lambda x: 1.0, y_unit=1, upper=True, rating=-2),
                        Limit_M(codes, lambda x: 1.2, y_unit=1, upper=True, rating=-10),
                        Limit_P(codes, lambda x: 1.2, y_unit=1, lower=True, rating=-20),
                    ]

                def calculation(self) -> None:
                    parent = cast(
                        "Overall.Criterion_Rear_Passenger.Criterion_Head_Neck | None",
                        self.parent,
                    )
                    if parent is not None and not parent.injury_values_apply():
                        self.value = np.nan
                        self.rating, self.color = 0.0, Limit_G.color
                        return
                    self.channel = self.require_channel(self.ctx.code("?{p}NIJCIP00??00YB"))
                    self.value = float(np.max(self.channel.get_data()))
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Neck_Tension(Criterion):
                name = "Neck axial tension"
                validate_ignore = {
                    "limit_flags": "discrete demerits use successive upper bounds with interpolation disabled",
                }

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}NECKUP00??FOZ?")
                    return [
                        Limit_G(codes, lambda x: 2.0, y_unit="kN", upper=True, rating=0),
                        Limit_A(codes, lambda x: 2.4, y_unit="kN", upper=True, rating=-2),
                        Limit_M(codes, lambda x: 2.8, y_unit="kN", upper=True, rating=-10),
                        Limit_P(codes, lambda x: 2.8, y_unit="kN", lower=True, rating=-20),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(self.ctx.code("?{p}NECKUP00??FOZB")).convert_unit("kN")
                    self.value = float(np.max(self.channel.get_data()))
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Neck_Compression(Criterion):
                name = "Neck compression"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}NECKUP00??FOZ?")
                    return [
                        Limit_G(codes, lambda x: -2.0, y_unit="kN", lower=True, rating=0),
                        Limit_A(codes, lambda x: -2.0, y_unit="kN", upper=True, rating=-2),
                        Limit_M(codes, lambda x: -2.5, y_unit="kN", upper=True, rating=-10),
                        Limit_P(codes, lambda x: -3.0, y_unit="kN", upper=True, rating=-20),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(self.ctx.code("?{p}NECKUP00??FOZB")).convert_unit("kN")
                    self.value = float(np.min(self.channel.get_data()))
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            criterion_hic_15 = sub(Criterion_HIC_15)
            criterion_nij = sub(Criterion_Nij)
            criterion_neck_tension = sub(Criterion_Neck_Tension)
            criterion_neck_compression = sub(Criterion_Neck_Compression)

            def calculation(self) -> None:
                self.rating = self.min_of_children()
                if self.hard_contact_over_70g:
                    self.rating = {
                        0.0: -2.0,
                        -2.0: -10.0,
                        -10.0: -20.0,
                        -20.0: -20.0,
                    }[self.rating]
                self.color = {
                    0.0: Limit_G.color,
                    -2.0: Limit_A.color,
                    -10.0: Limit_M.color,
                    -20.0: Limit_P.color,
                }[self.rating]

        class Criterion_Chest(Criterion):
            name = "Chest"
            role = Role.AGGREGATE
            aggregation = "min"

            class Criterion_Chest_Index(Criterion):
                name = "Chest Index"
                validate_ignore = {
                    "limit_flags": "discrete demerits use successive upper bounds with interpolation disabled",
                }
                dynamic_belt_position_mm: Manual[float, manual(
                    17.0,
                    unit="mm",
                    source="pressure mat",
                    doc=("Vertical shoulder-belt centerline above the sternum potentiometer at "
                         "maximum sternum deflection; Version III Appendix A automates this measurement."),
                )]

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}CHST0000??DSX?")
                    return [
                        Limit_G(codes, lambda x: 35, y_unit="mm", upper=True, rating=0),
                        Limit_A(codes, lambda x: 40, y_unit="mm", upper=True, rating=-2),
                        Limit_M(codes, lambda x: 45, y_unit="mm", upper=True, rating=-10),
                        Limit_P(codes, lambda x: 45, y_unit="mm", lower=True, rating=-20),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(self.ctx.code("?{p}CHST0000??DSXC")).convert_unit("mm")
                    deflection = abs(float(np.min(self.channel.get_data())))
                    if self.dynamic_belt_position_mm <= 17:
                        chest_index = deflection
                    else:
                        denominator = 1 - 0.005 * (self.dynamic_belt_position_mm - 17)
                        if denominator <= 0:
                            raise ValueError("dynamic belt position makes Chest Index denominator nonpositive")
                        chest_index = deflection / denominator
                    self.value = float(np.floor(chest_index))
                    self.channel = Channel(
                        self.channel.code,
                        pd.DataFrame([self.value]),
                        "mm",
                    )
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Shoulder_Belt_Tension(Criterion):
                name = "Shoulder belt tension"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}SEBE????B3FO[X0]?")
                    return [
                        Limit_G(codes, lambda x: 5.9, y_unit="kN", upper=True, rating=0),
                        Limit_M(codes, lambda x: 5.9, y_unit="kN", lower=True, rating=-10),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(self.ctx.code("?{p}SEBE????B3FO[X0]C")).convert_unit("kN")
                    self.value = float(np.max(self.channel.get_data()))
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            criterion_chest_index = sub(Criterion_Chest_Index)
            criterion_shoulder_belt_tension = sub(Criterion_Shoulder_Belt_Tension)

            def calculation(self) -> None:
                self.rating = self.min_of_children()
                self.color = {
                    0.0: Limit_G.color,
                    -2.0: Limit_A.color,
                    -10.0: Limit_M.color,
                    -20.0: Limit_P.color,
                }.get(self.rating)

        class Criterion_Thigh(Criterion):
            name = "Thigh"
            role = Role.AGGREGATE
            aggregation = "min"

            class Criterion_Femur_Compression(Criterion):
                name = "Femur axial compression"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}FEMR??00??FOZ?")
                    return [
                        Limit_G(codes, lambda x: -4.9, y_unit="kN", lower=True, rating=0),
                        Limit_A(codes, lambda x: -4.9, y_unit="kN", upper=True, rating=-2),
                        Limit_M(codes, lambda x: -6.2, y_unit="kN", upper=True, rating=-6),
                        Limit_P(codes, lambda x: -7.4, y_unit="kN", upper=True, rating=-10),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(
                        self.ctx.code("?{p}FEMR0000??FOZB")
                    ).convert_unit("kN")
                    self.value = abs(float(np.min(self.channel.get_data())))
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            criterion_femur_compression = sub(Criterion_Femur_Compression)

            def calculation(self) -> None:
                self.rating = self.min_of_children()
                self.color = {
                    0.0: Limit_G.color,
                    -2.0: Limit_A.color,
                    -6.0: Limit_M.color,
                    -10.0: Limit_P.color,
                }.get(self.rating)

        class Criterion_Restraints_Kinematics(Criterion):
            name = "Restraints and kinematics"
            demerits: Manual[int, manual(
                0,
                source="video, pressure mat, and postcrash inspection",
                doc="Sum the H35F rear-occupant events in Table 8.",
            )]

            def calculation(self) -> None:
                self.value = float(self.demerits)
                if self.value <= 1:
                    self.rating, self.color = 0.0, Limit_G.color
                elif self.value <= 5:
                    self.rating, self.color = -2.0, Limit_A.color
                elif self.value <= 9:
                    self.rating, self.color = -10.0, Limit_M.color
                else:
                    self.rating, self.color = -15.0, Limit_P.color

        criterion_head_neck = sub(Criterion_Head_Neck)
        criterion_chest = sub(Criterion_Chest)
        criterion_thigh = sub(Criterion_Thigh)
        criterion_restraints_kinematics = sub(Criterion_Restraints_Kinematics)

        def calculation(self) -> None:
            self.rating = self.sum_of_children()
            self.value = -self.rating

    class Criterion_Structure(Criterion):
        name = "Vehicle structure"
        intrusion_rating: Manual[int, manual(
            4,
            source="intrusion measurements",
            doc="Initial Figure 7 category: 4=Good, 3=Acceptable, 2=Marginal, 1=Poor.",
        )]
        qualitative_downgrades: Manual[int, manual(
            0,
            source="postcrash inspection",
            doc="Number of one-category downgrades for adverse deformation observations.",
        )]
        integrity_failure: Manual[bool, manual(
            False,
            source="postcrash inspection",
            doc="Significant fuel, electrical, smoke, fire, or battery thermal event.",
        )]

        def calculation(self) -> None:
            if self.intrusion_rating not in (1, 2, 3, 4):
                raise ValueError("intrusion_rating must be 1 (Poor) through 4 (Good)")
            category = 1 if self.integrity_failure else max(
                1, self.intrusion_rating - self.qualitative_downgrades
            )
            self.value = category
            self.rating, self.color = {
                4: (0.0, Limit_G.color),
                3: (-4.0, Limit_A.color),
                2: (-10.0, Limit_M.color),
                1: (-20.0, Limit_P.color),
            }[category]

    criterion_driver = sub(Criterion_Driver, at=from_input(P_DRIVER), role=Role.AGGREGATE)
    criterion_rear_passenger = sub(
        Criterion_Rear_Passenger,
        at=from_input(P_REAR_PASSENGER),
        role=Role.AGGREGATE,
    )
    criterion_structure = sub(Criterion_Structure)

    def calculation(self) -> None:
        self.rating = self.sum_of_children()
        self.value = -self.rating
        if self.value <= 5:
            self.color = Limit_G.color
        elif self.value <= 10:
            self.color = Limit_A.color
        elif self.value <= 24:
            self.color = Limit_M.color
        else:
            self.color = Limit_P.color


class IIHS_Frontal_Moderate_Overlap(Report[Overall]):
    name = "IIHS | Moderate Overlap Frontal Crashworthiness 2.0"
    protocol = "III"
    protocols = {
        "III": "Version III (02.2026) [references/IIHS/Moderate_2.0_rating_guidelines.pdf]",
        "II": ("Version II (05.2024) "
               "[references/IIHS/Moderate 2.0 Rating guidelines Phase 2_FINAL_May2024.pdf]"),
    }
    Criterion_Overall = Overall

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.pages = [
            Page_Cover(self),
            self.Page_Rating_Table(self),
            self.Page_Driver_Rating_Table(self),
            self.Page_Driver_Values_Chart(self),
            self.Page_Driver_Values_Table(self),
            self.Page_Driver_Head_Acceleration(self),
            self.Page_Driver_Neck_Nij(self),
            self.Page_Driver_Neck_Load(self),
            self.Page_Driver_Neck_Load_Corridors(self),
            self.Page_Driver_Chest(self),
            self.Page_Driver_Femur_Force(self),
            self.Page_Driver_Knee_Displacement(self),
            self.Page_Driver_Tibia_Index(self),
            self.Page_Driver_Tibia_Force(self),
            self.Page_Driver_Foot_Acceleration(self),
            self.Page_Rear_Passenger_Rating_Table(self),
            self.Page_Rear_Passenger_Values_Chart(self),
            self.Page_Rear_Passenger_Values_Table(self),
            self.Page_Rear_Passenger_Head_Acceleration(self),
            self.Page_Rear_Passenger_Neck_Nij(self),
            self.Page_Rear_Passenger_Neck_Load(self),
            self.Page_Rear_Passenger_Chest(self),
            self.Page_Rear_Passenger_Femur_Force(self),
        ]

    class Page_Rating_Table(Page_Criterion_Rating_Table):
        report: IIHS_Frontal_Moderate_Overlap
        name = "Rating"
        title = "Rating"

        def __init__(self, report: IIHS_Frontal_Moderate_Overlap) -> None:
            super().__init__(report)
            self.criteria = {
                isomme: [
                    report.overall(isomme),
                    report.overall(isomme).criterion_structure,
                    report.overall(isomme).criterion_driver.criterion_head_neck,
                    report.overall(isomme).criterion_driver.criterion_chest,
                    report.overall(isomme).criterion_driver.criterion_thigh_hip,
                    report.overall(isomme).criterion_driver.criterion_leg_foot,
                    report.overall(isomme).criterion_driver.criterion_restraints_kinematics,
                    report.overall(isomme).criterion_rear_passenger.criterion_head_neck,
                    report.overall(isomme).criterion_rear_passenger.criterion_chest,
                    report.overall(isomme).criterion_rear_passenger.criterion_thigh,
                    report.overall(isomme).criterion_rear_passenger.criterion_restraints_kinematics,
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Rating_Table(Page_Criterion_Rating_Table):
        report: IIHS_Frontal_Moderate_Overlap
        name = "Driver Rating Table"
        title = "Driver Rating"

        def __init__(self, report: IIHS_Frontal_Moderate_Overlap) -> None:
            super().__init__(report)
            self.criteria = {
                isomme: [
                    report.overall(isomme).criterion_driver.criterion_head_neck,
                    report.overall(isomme).criterion_driver.criterion_chest,
                    report.overall(isomme).criterion_driver.criterion_thigh_hip,
                    report.overall(isomme).criterion_driver.criterion_leg_foot,
                    report.overall(isomme).criterion_driver.criterion_restraints_kinematics,
                    report.overall(isomme).criterion_driver,
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Values_Chart(Page_Criterion_Values_Chart):
        report: IIHS_Frontal_Moderate_Overlap
        name = "Driver Result Values Chart"
        title = "Driver Result"

        def __init__(self, report: IIHS_Frontal_Moderate_Overlap) -> None:
            super().__init__(report)
            self.criteria = {
                isomme: [
                    report.overall(isomme).criterion_driver.criterion_head_neck.criterion_hic_15,
                    report.overall(isomme).criterion_driver.criterion_head_neck.criterion_nij,
                    report.overall(isomme).criterion_driver.criterion_head_neck.criterion_neck_tension,
                    report.overall(isomme).criterion_driver.criterion_head_neck.criterion_neck_compression,
                    report.overall(isomme).criterion_driver.criterion_head_neck.criterion_tension_corridor,
                    report.overall(isomme).criterion_driver.criterion_head_neck.criterion_compression_corridor,
                    report.overall(isomme).criterion_driver.criterion_head_neck.criterion_shear_corridor,
                    report.overall(isomme).criterion_driver.criterion_chest.criterion_acceleration,
                    report.overall(isomme).criterion_driver.criterion_chest.criterion_deflection,
                    report.overall(isomme).criterion_driver.criterion_chest.criterion_deflection_rate,
                    report.overall(isomme).criterion_driver.criterion_chest.criterion_vc,
                    report.overall(isomme).criterion_driver.criterion_leg_foot.criterion_tibia_femur_displacement,
                    report.overall(isomme).criterion_driver.criterion_leg_foot.criterion_tibia_index,
                    report.overall(isomme).criterion_driver.criterion_leg_foot.criterion_tibia_axial_force,
                    report.overall(isomme).criterion_driver.criterion_leg_foot.criterion_foot_acceleration,
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Values_Table(Page_Criterion_Values_Table):
        report: IIHS_Frontal_Moderate_Overlap
        name = "Driver Values Table"
        title = "Driver Values"

        def __init__(self, report: IIHS_Frontal_Moderate_Overlap) -> None:
            super().__init__(report)
            self.criteria = {
                isomme: [
                    report.overall(isomme).criterion_driver.criterion_head_neck.criterion_hic_15,
                    report.overall(isomme).criterion_driver.criterion_head_neck.criterion_nij,
                    report.overall(isomme).criterion_driver.criterion_head_neck.criterion_neck_tension,
                    report.overall(isomme).criterion_driver.criterion_head_neck.criterion_neck_compression,
                    report.overall(isomme).criterion_driver.criterion_head_neck.criterion_tension_corridor,
                    report.overall(isomme).criterion_driver.criterion_head_neck.criterion_compression_corridor,
                    report.overall(isomme).criterion_driver.criterion_head_neck.criterion_shear_corridor,
                    report.overall(isomme).criterion_driver.criterion_chest.criterion_acceleration,
                    report.overall(isomme).criterion_driver.criterion_chest.criterion_deflection,
                    report.overall(isomme).criterion_driver.criterion_chest.criterion_deflection_rate,
                    report.overall(isomme).criterion_driver.criterion_chest.criterion_vc,
                    report.overall(isomme).criterion_driver.criterion_thigh_hip.criterion_left,
                    report.overall(isomme).criterion_driver.criterion_thigh_hip.criterion_right,
                    report.overall(isomme).criterion_driver.criterion_leg_foot.criterion_tibia_femur_displacement,
                    report.overall(isomme).criterion_driver.criterion_leg_foot.criterion_tibia_index,
                    report.overall(isomme).criterion_driver.criterion_leg_foot.criterion_tibia_axial_force,
                    report.overall(isomme).criterion_driver.criterion_leg_foot.criterion_foot_acceleration,
                ]
                for isomme in report.isomme_list
            }

    class Page_Rear_Passenger_Rating_Table(Page_Criterion_Rating_Table):
        report: IIHS_Frontal_Moderate_Overlap
        name = "Rear Passenger Rating Table"
        title = "Rear Passenger Rating"

        def __init__(self, report: IIHS_Frontal_Moderate_Overlap) -> None:
            super().__init__(report)
            self.criteria = {
                isomme: [
                    report.overall(isomme).criterion_rear_passenger.criterion_head_neck,
                    report.overall(isomme).criterion_rear_passenger.criterion_chest,
                    report.overall(isomme).criterion_rear_passenger.criterion_thigh,
                    report.overall(isomme).criterion_rear_passenger.criterion_restraints_kinematics,
                    report.overall(isomme).criterion_rear_passenger,
                ]
                for isomme in report.isomme_list
            }

    class Page_Rear_Passenger_Values_Chart(Page_Criterion_Values_Chart):
        report: IIHS_Frontal_Moderate_Overlap
        name = "Rear Passenger Result Values Chart"
        title = "Rear Passenger Result"

        def __init__(self, report: IIHS_Frontal_Moderate_Overlap) -> None:
            super().__init__(report)
            self.criteria = {
                isomme: [
                    report.overall(isomme).criterion_rear_passenger.criterion_head_neck.criterion_neck_tension,
                    report.overall(isomme).criterion_rear_passenger.criterion_head_neck.criterion_neck_compression,
                    report.overall(isomme).criterion_rear_passenger.criterion_chest.criterion_chest_index,
                    report.overall(isomme).criterion_rear_passenger.criterion_chest.criterion_shoulder_belt_tension,
                    report.overall(isomme).criterion_rear_passenger.criterion_thigh.criterion_femur_compression,
                ]
                for isomme in report.isomme_list
            }

    class Page_Rear_Passenger_Values_Table(Page_Criterion_Values_Table):
        report: IIHS_Frontal_Moderate_Overlap
        name = "Rear Passenger Values Table"
        title = "Rear Passenger Values"

        def __init__(self, report: IIHS_Frontal_Moderate_Overlap) -> None:
            super().__init__(report)
            self.criteria = {
                isomme: [
                    report.overall(isomme).criterion_rear_passenger.criterion_head_neck.criterion_hic_15,
                    report.overall(isomme).criterion_rear_passenger.criterion_head_neck.criterion_nij,
                    report.overall(isomme).criterion_rear_passenger.criterion_head_neck.criterion_neck_tension,
                    report.overall(isomme).criterion_rear_passenger.criterion_head_neck.criterion_neck_compression,
                    report.overall(isomme).criterion_rear_passenger.criterion_chest.criterion_chest_index,
                    report.overall(isomme).criterion_rear_passenger.criterion_chest.criterion_shoulder_belt_tension,
                    report.overall(isomme).criterion_rear_passenger.criterion_thigh.criterion_femur_compression,
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Head_Acceleration(Page_Plot_nxn):
        report: IIHS_Frontal_Moderate_Overlap
        name = "Driver Head Acceleration"
        title = "Driver Head Acceleration"
        nrows, ncols, sharey = 2, 2, True

        def __init__(self, report: IIHS_Frontal_Moderate_Overlap) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [[f"?{report.overall(isomme).p_driver}HEAD??????AC{axis}A"] for axis in "XYZR"]
                for isomme in report.isomme_list
            }

    class Page_Driver_Neck_Nij(Page_Plot_nxn):
        report: IIHS_Frontal_Moderate_Overlap
        name = "Driver Neck NIJ"
        title = "Driver Neck NIJ"
        nrows, ncols, sharey = 2, 2, True

        def __init__(self, report: IIHS_Frontal_Moderate_Overlap) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{report.overall(isomme).p_driver}NIJCIPCF??00YB"],
                    [f"?{report.overall(isomme).p_driver}NIJCIPCE??00YB"],
                    [f"?{report.overall(isomme).p_driver}NIJCIPTF??00YB"],
                    [f"?{report.overall(isomme).p_driver}NIJCIPTE??00YB"],
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Neck_Load(Page_Plot_nxn):
        report: IIHS_Frontal_Moderate_Overlap
        name = "Driver Neck Axial Load"
        title = "Driver Neck Axial Load"

        def __init__(self, report: IIHS_Frontal_Moderate_Overlap) -> None:
            driver = report.overall(report.isomme_list[0]).criterion_driver
            super().__init__(
                report,
                limits=(driver.criterion_head_neck.criterion_neck_tension.limits
                        + driver.criterion_head_neck.criterion_neck_compression.limits),
            )
            self.channels = {
                isomme: [[f"?{report.overall(isomme).p_driver}NECKUP00??FOZB"]]
                for isomme in report.isomme_list
            }

    class Page_Driver_Neck_Load_Corridors(Page_Plot_nxn):
        report: IIHS_Frontal_Moderate_Overlap
        name = "Driver Neck Load Corridors"
        title = "Driver Neck Load Corridors"
        nrows, ncols = 1, 2

        def __init__(self, report: IIHS_Frontal_Moderate_Overlap) -> None:
            head_neck = report.overall(report.isomme_list[0]).criterion_driver.criterion_head_neck
            super().__init__(
                report,
                limits=(head_neck.criterion_tension_corridor.limits
                        + head_neck.criterion_compression_corridor.limits
                        + head_neck.criterion_shear_corridor.limits),
            )
            self.channels = {
                isomme: [
                    [f"?{report.overall(isomme).p_driver}NECKUP00??FOZB"],
                    [f"?{report.overall(isomme).p_driver}NECKUP00??FOXB"],
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Chest(Page_Plot_nxn):
        report: IIHS_Frontal_Moderate_Overlap
        name = "Driver Chest Injury Measures"
        title = "Driver Chest Injury Measures"
        nrows, ncols = 2, 2

        def __init__(self, report: IIHS_Frontal_Moderate_Overlap) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{report.overall(isomme).p_driver}CHST0000??ACRA"],
                    [f"?{report.overall(isomme).p_driver}CHST0000??DSXC"],
                    [f"?{report.overall(isomme).p_driver}CHST0000??VEXC"],
                    [f"?{report.overall(isomme).p_driver}VCCR0000??VEXC"],
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Femur_Force(Page_Plot_nxn):
        report: IIHS_Frontal_Moderate_Overlap
        name = "Driver Femur Axial Force"
        title = "Driver Femur Axial Force"
        nrows, ncols, sharey = 1, 2, True

        def __init__(self, report: IIHS_Frontal_Moderate_Overlap) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{report.overall(isomme).p_driver}FEMRLE00??FOZB"],
                    [f"?{report.overall(isomme).p_driver}FEMRRI00??FOZB"],
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Knee_Displacement(Page_Plot_nxn):
        report: IIHS_Frontal_Moderate_Overlap
        name = "Driver Tibia-Femur Displacement"
        title = "Driver Tibia-Femur Displacement"
        nrows, ncols, sharey = 1, 2, True

        def __init__(self, report: IIHS_Frontal_Moderate_Overlap) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{report.overall(isomme).p_driver}KNSLLE00??DSXC"],
                    [f"?{report.overall(isomme).p_driver}KNSLRI00??DSXC"],
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Tibia_Index(Page_Plot_nxn):
        report: IIHS_Frontal_Moderate_Overlap
        name = "Driver Tibia Index"
        title = "Driver Tibia Index"
        nrows, ncols, sharey = 2, 2, True

        def __init__(self, report: IIHS_Frontal_Moderate_Overlap) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{report.overall(isomme).p_driver}TIINLUTO??000B"],
                    [f"?{report.overall(isomme).p_driver}TIINRUTO??000B"],
                    [f"?{report.overall(isomme).p_driver}TIINLLTO??000B"],
                    [f"?{report.overall(isomme).p_driver}TIINRLTO??000B"],
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Tibia_Force(Page_Plot_nxn):
        report: IIHS_Frontal_Moderate_Overlap
        name = "Driver Tibia Axial Force"
        title = "Driver Tibia Axial Force"
        nrows, ncols, sharey = 1, 2, True

        def __init__(self, report: IIHS_Frontal_Moderate_Overlap) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{report.overall(isomme).p_driver}TIBILELO??FOZB"],
                    [f"?{report.overall(isomme).p_driver}TIBIRILO??FOZB"],
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Foot_Acceleration(Page_Plot_nxn):
        report: IIHS_Frontal_Moderate_Overlap
        name = "Driver Foot Acceleration"
        title = "Driver Foot Acceleration"
        nrows, ncols, sharey = 1, 2, True

        def __init__(self, report: IIHS_Frontal_Moderate_Overlap) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{report.overall(isomme).p_driver}FOOTLE00??ACRB"],
                    [f"?{report.overall(isomme).p_driver}FOOTRI00??ACRB"],
                ]
                for isomme in report.isomme_list
            }

    class Page_Rear_Passenger_Head_Acceleration(Page_Plot_nxn):
        report: IIHS_Frontal_Moderate_Overlap
        name = "Rear Passenger Head Acceleration"
        title = "Rear Passenger Head Acceleration"
        nrows, ncols, sharey = 2, 2, True

        def __init__(self, report: IIHS_Frontal_Moderate_Overlap) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{report.overall(isomme).p_rear_passenger}HEAD??????AC{axis}A"]
                    for axis in "XYZR"
                ]
                for isomme in report.isomme_list
            }

    class Page_Rear_Passenger_Neck_Nij(Page_Plot_nxn):
        report: IIHS_Frontal_Moderate_Overlap
        name = "Rear Passenger Neck NIJ"
        title = "Rear Passenger Neck NIJ"
        nrows, ncols, sharey = 2, 2, True

        def __init__(self, report: IIHS_Frontal_Moderate_Overlap) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{report.overall(isomme).p_rear_passenger}NIJCIPCF??00YB"],
                    [f"?{report.overall(isomme).p_rear_passenger}NIJCIPCE??00YB"],
                    [f"?{report.overall(isomme).p_rear_passenger}NIJCIPTF??00YB"],
                    [f"?{report.overall(isomme).p_rear_passenger}NIJCIPTE??00YB"],
                ]
                for isomme in report.isomme_list
            }

    class Page_Rear_Passenger_Neck_Load(Page_Plot_nxn):
        report: IIHS_Frontal_Moderate_Overlap
        name = "Rear Passenger Neck Axial Load"
        title = "Rear Passenger Neck Axial Load"

        def __init__(self, report: IIHS_Frontal_Moderate_Overlap) -> None:
            rear = report.overall(report.isomme_list[0]).criterion_rear_passenger
            super().__init__(
                report,
                limits=(rear.criterion_head_neck.criterion_neck_tension.limits
                        + rear.criterion_head_neck.criterion_neck_compression.limits),
            )
            self.channels = {
                isomme: [[f"?{report.overall(isomme).p_rear_passenger}NECKUP00??FOZB"]]
                for isomme in report.isomme_list
            }

    class Page_Rear_Passenger_Chest(Page_Plot_nxn):
        report: IIHS_Frontal_Moderate_Overlap
        name = "Rear Passenger Chest Measures"
        title = "Rear Passenger Chest Measures"
        nrows, ncols = 1, 2

        def __init__(self, report: IIHS_Frontal_Moderate_Overlap) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{report.overall(isomme).p_rear_passenger}CHST0000??DSXC"],
                    [f"?{report.overall(isomme).p_rear_passenger}SEBE????B3FO[X0]C"],
                ]
                for isomme in report.isomme_list
            }

    class Page_Rear_Passenger_Femur_Force(Page_Plot_nxn):
        report: IIHS_Frontal_Moderate_Overlap
        name = "Rear Passenger Femur Axial Force"
        title = "Rear Passenger Femur Axial Force"
        nrows, ncols, sharey = 1, 2, True

        def __init__(self, report: IIHS_Frontal_Moderate_Overlap) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{report.overall(isomme).p_rear_passenger}FEMRLE00??FOZB"],
                    [f"?{report.overall(isomme).p_rear_passenger}FEMRRI00??FOZB"],
                ]
                for isomme in report.isomme_list
            }
