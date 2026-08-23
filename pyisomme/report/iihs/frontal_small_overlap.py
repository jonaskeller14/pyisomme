from __future__ import annotations

from typing import Any

from pyisomme.isomme import Isomme
from pyisomme.report.criterion import Criterion, Role, sub
from pyisomme.report.ctx import from_input
from pyisomme.report.iihs.frontal import Criterion_H350M_Injury
from pyisomme.report.iihs.limits import Limit_A, Limit_G, Limit_M, Limit_P
from pyisomme.report.iihs.protocols import PROTOCOL_SMALL_OVERLAP_VII
from pyisomme.report.manual import Manual, manual
from pyisomme.report.page import (
    Page_Cover,
    Page_Criterion_Rating_Table,
    Page_Criterion_Values_Chart,
    Page_Criterion_Values_Table,
    Page_Plot_nxn,
)
from pyisomme.report.report import Report

P_DRIVER = manual(
    "1",
    source="test report",
    doc=(
        "Channel-code position of the driver. Defaults to the "
        "'Driver position object 1' test-info field when available."
    ),
)


class Overall(Criterion):
    name = "Overall"
    role = Role.AGGREGATE
    source = "Weighting principles for overall rating / Table 3"
    aggregation = "sum"
    p_driver: Manual[str, P_DRIVER]

    def __init__(self, report: Report[Any], isomme: Isomme) -> None:
        super().__init__(report, isomme)
        self.prepare()

    def prepare(self) -> None:
        position = self.isomme.get_test_info("Driver position object 1")
        if position is not None:
            self.set_derived_input("p_driver", str(position).strip())

    class Criterion_Restraints_Kinematics(Criterion):
        name = "Restraints and dummy kinematics"
        demerits: Manual[
            int,
            manual(
                0,
                source="video and postcrash inspection",
                doc=(
                    "Sum the Version VII Table 1 demerits. Frontal-airbag interaction is 0/1/2; "
                    "lateral protection, steering-wheel motion, excursion and containment events "
                    "are added as listed."
                ),
            ),
        ]
        automatic_poor: Manual[
            bool,
            manual(
                False,
                source="video and postcrash inspection",
                doc="True for late/nondeployment, seat-attachment failure, or vehicle-door opening.",
            ),
        ]

        def calculation(self) -> None:
            self.value = 6.0 if self.automatic_poor else float(self.demerits)
            if self.value <= 1:
                self.rating, self.color = 0.0, Limit_G.color
            elif self.value <= 3:
                self.rating, self.color = -2.0, Limit_A.color
            elif self.value <= 5:
                self.rating, self.color = -6.0, Limit_M.color
            else:
                self.rating, self.color = -10.0, Limit_P.color

    class Criterion_Structure(Criterion):
        name = "Vehicle structure"
        intrusion_rating: Manual[
            int,
            manual(
                4,
                source="intrusion measurements",
                doc=(
                    "Initial Figure 15 structure category: 4=Good, 3=Acceptable, "
                    "2=Marginal, 1=Poor."
                ),
            ),
        ]
        qualitative_downgrades: Manual[
            int,
            manual(
                0,
                source="postcrash inspection",
                doc="Number of one-category downgrades for adverse deformation observations.",
            ),
        ]
        integrity_failure: Manual[
            bool,
            manual(
                False,
                source="postcrash inspection",
                doc="Significant fuel leak, electrical compromise, smoke, fire, or battery thermal event.",
            ),
        ]

        def calculation(self) -> None:
            if self.intrusion_rating not in (1, 2, 3, 4):
                raise ValueError("intrusion_rating must be 1 (Poor) through 4 (Good)")
            category = (
                1
                if self.integrity_failure
                else max(1, self.intrusion_rating - self.qualitative_downgrades)
            )
            self.value = category
            self.rating, self.color = {
                4: (0.0, Limit_G.color),
                3: (-2.0, Limit_A.color),
                2: (-6.0, Limit_M.color),
                1: (-10.0, Limit_P.color),
            }[category]

    def calculation(self) -> None:
        self.rating = self.sum_of_children()
        self.value = -self.rating
        if self.value <= 3:
            self.color = Limit_G.color
        elif self.value <= 9:
            self.color = Limit_A.color
        elif self.value <= 19:
            self.color = Limit_M.color
        else:
            self.color = Limit_P.color

    class Criterion_Driver(Criterion_H350M_Injury):
        name = "Driver"

    criterion_driver = sub(
        Criterion_Driver, at=from_input(P_DRIVER), role=Role.AGGREGATE
    )
    criterion_restraints_kinematics = sub(Criterion_Restraints_Kinematics)
    criterion_structure = sub(Criterion_Structure)


class IIHS_Frontal_Small_Overlap(Report[Overall]):
    _name = "IIHS | Frontal Impact against Small Overlap Barrier with 25% Overlap at 64 km/h"
    _protocol = PROTOCOL_SMALL_OVERLAP_VII
    _protocols = (PROTOCOL_SMALL_OVERLAP_VII,)
    Criterion_Overall = Overall

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._available_pages = (
            Page_Cover(self),
            self.Page_Overall_Rating(self),
            self.Page_Driver_Rating(self),
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
        )
        self._selected_pages = list(self._available_pages)

    class Page_Overall_Rating(Page_Criterion_Rating_Table):
        report: IIHS_Frontal_Small_Overlap
        name = "Overall Rating"
        title = "Overall Rating"

        def __init__(self, report: IIHS_Frontal_Small_Overlap) -> None:
            super().__init__(report)
            self.criteria = {
                isomme: [
                    report.overall(isomme),
                    report.overall(isomme).criterion_structure,
                    report.overall(isomme).criterion_driver.criterion_head_neck,
                    report.overall(isomme).criterion_driver.criterion_chest,
                    report.overall(isomme).criterion_driver.criterion_thigh_hip,
                    report.overall(isomme).criterion_driver.criterion_leg_foot,
                    report.overall(isomme).criterion_restraints_kinematics,
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Rating(Page_Criterion_Rating_Table):
        report: IIHS_Frontal_Small_Overlap
        name = "Driver Injury Ratings"
        title = "Driver Injury Ratings"

        def __init__(self, report: IIHS_Frontal_Small_Overlap) -> None:
            super().__init__(report)
            self.criteria = {
                isomme: [
                    report.overall(isomme).criterion_driver.criterion_head_neck,
                    report.overall(isomme).criterion_driver.criterion_chest,
                    report.overall(isomme).criterion_driver.criterion_thigh_hip,
                    report.overall(isomme).criterion_driver.criterion_leg_foot,
                    report.overall(isomme).criterion_driver,
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Values_Chart(Page_Criterion_Values_Chart):
        report: IIHS_Frontal_Small_Overlap
        name = "Driver Values Chart"
        title = "Driver Values"

        def __init__(self, report: IIHS_Frontal_Small_Overlap) -> None:
            super().__init__(report)
            self.criteria = {
                isomme: [
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_head_neck.criterion_hic_15,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_head_neck.criterion_nij,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_head_neck.criterion_neck_tension,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_head_neck.criterion_neck_compression,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_head_neck.criterion_tension_corridor,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_head_neck.criterion_compression_corridor,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_head_neck.criterion_shear_corridor,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_chest.criterion_acceleration,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_chest.criterion_deflection,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_chest.criterion_deflection_rate,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_chest.criterion_vc,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_leg_foot.criterion_tibia_femur_displacement,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_leg_foot.criterion_tibia_index,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_leg_foot.criterion_tibia_axial_force,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_leg_foot.criterion_foot_acceleration,
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Values_Table(Page_Criterion_Values_Table):
        report: IIHS_Frontal_Small_Overlap
        name = "Driver Values Table"
        title = "Driver Values"

        def __init__(self, report: IIHS_Frontal_Small_Overlap) -> None:
            super().__init__(report)
            self.criteria = {
                isomme: [
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_head_neck.criterion_hic_15,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_head_neck.criterion_nij,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_head_neck.criterion_neck_tension,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_head_neck.criterion_neck_compression,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_head_neck.criterion_tension_corridor,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_head_neck.criterion_compression_corridor,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_head_neck.criterion_shear_corridor,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_chest.criterion_acceleration,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_chest.criterion_deflection,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_chest.criterion_deflection_rate,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_chest.criterion_vc,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_thigh_hip.criterion_left,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_thigh_hip.criterion_right,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_leg_foot.criterion_tibia_femur_displacement,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_leg_foot.criterion_tibia_index,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_leg_foot.criterion_tibia_axial_force,
                    report.overall(
                        isomme
                    ).criterion_driver.criterion_leg_foot.criterion_foot_acceleration,
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Head_Acceleration(Page_Plot_nxn):
        report: IIHS_Frontal_Small_Overlap
        name = "Driver Head Acceleration"
        title = "Driver Head Acceleration"
        nrows = 2
        ncols = 2
        sharey = True

        def __init__(self, report: IIHS_Frontal_Small_Overlap) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{report.overall(isomme).p_driver}HEAD??????AC{axis}A"]
                    for axis in "XYZR"
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Neck_Nij(Page_Plot_nxn):
        report: IIHS_Frontal_Small_Overlap
        name = "Driver Neck NIJ"
        title = "Driver Neck NIJ"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: IIHS_Frontal_Small_Overlap) -> None:
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
        report: IIHS_Frontal_Small_Overlap
        name = "Driver Neck Axial Load"
        title = "Driver Neck Axial Load"

        def __init__(self, report: IIHS_Frontal_Small_Overlap) -> None:
            driver = report.overall(report.isomme_list[0]).criterion_driver
            super().__init__(
                report,
                limits=(
                    driver.criterion_head_neck.criterion_neck_tension.limits
                    + driver.criterion_head_neck.criterion_neck_compression.limits
                ),
            )
            self.channels = {
                isomme: [[f"?{report.overall(isomme).p_driver}NECKUP00??FOZB"]]
                for isomme in report.isomme_list
            }

    class Page_Driver_Neck_Load_Corridors(Page_Plot_nxn):
        report: IIHS_Frontal_Small_Overlap
        name = "Driver Neck Load Corridors"
        title = "Driver Neck Load Corridors"
        nrows = 1
        ncols = 2

        def __init__(self, report: IIHS_Frontal_Small_Overlap) -> None:
            head_neck = report.overall(
                report.isomme_list[0]
            ).criterion_driver.criterion_head_neck
            super().__init__(
                report,
                limits=(
                    head_neck.criterion_tension_corridor.limits
                    + head_neck.criterion_compression_corridor.limits
                    + head_neck.criterion_shear_corridor.limits
                ),
            )
            self.channels = {
                isomme: [
                    [f"?{report.overall(isomme).p_driver}NECKUP00??FOZB"],
                    [f"?{report.overall(isomme).p_driver}NECKUP00??FOXB"],
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Chest(Page_Plot_nxn):
        report: IIHS_Frontal_Small_Overlap
        name = "Driver Chest Injury Measures"
        title = "Driver Chest Injury Measures"
        nrows = 2
        ncols = 2

        def __init__(self, report: IIHS_Frontal_Small_Overlap) -> None:
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
        report: IIHS_Frontal_Small_Overlap
        name = "Driver Femur Axial Force"
        title = "Driver Femur Axial Force"
        nrows = 1
        ncols = 2
        sharey = True

        def __init__(self, report: IIHS_Frontal_Small_Overlap) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{report.overall(isomme).p_driver}FEMRLE00??FOZB"],
                    [f"?{report.overall(isomme).p_driver}FEMRRI00??FOZB"],
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Knee_Displacement(Page_Plot_nxn):
        report: IIHS_Frontal_Small_Overlap
        name = "Driver Tibia-Femur Displacement"
        title = "Driver Tibia-Femur Displacement"
        nrows = 1
        ncols = 2
        sharey = True

        def __init__(self, report: IIHS_Frontal_Small_Overlap) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{report.overall(isomme).p_driver}KNSLLE00??DSXC"],
                    [f"?{report.overall(isomme).p_driver}KNSLRI00??DSXC"],
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Tibia_Index(Page_Plot_nxn):
        report: IIHS_Frontal_Small_Overlap
        name = "Driver Tibia Index (Total Moment)"
        title = "Driver Tibia Index (Total Moment)"
        nrows = 2
        ncols = 2
        sharey = True

        def __init__(self, report: Report[Any]) -> None:
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
        report: IIHS_Frontal_Small_Overlap
        name = "Driver Tibia Axial Force"
        title = "Driver Tibia Axial Force"
        nrows = 1
        ncols = 2
        sharey = True

        def __init__(self, report: IIHS_Frontal_Small_Overlap) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{report.overall(isomme).p_driver}TIBILELO??FOZB"],
                    [f"?{report.overall(isomme).p_driver}TIBIRILO??FOZB"],
                ]
                for isomme in report.isomme_list
            }

    class Page_Driver_Foot_Acceleration(Page_Plot_nxn):
        report: IIHS_Frontal_Small_Overlap
        name = "Driver Foot Acceleration"
        title = "Driver Foot Acceleration"
        nrows: int = 1
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: IIHS_Frontal_Small_Overlap) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{report.overall(isomme).p_driver}FOOTLE00??ACRB"],
                    [f"?{report.overall(isomme).p_driver}FOOTRI00??ACRB"],
                ]
                for isomme in report.isomme_list
            }
