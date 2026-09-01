from __future__ import annotations

from typing import Any

from pyisomme.isomme import Isomme
from pyisomme.report.criterion import Criterion, Role, sub
from pyisomme.report.criterion_result import CriterionResult
from pyisomme.report.ctx import from_input
from pyisomme.report.iihs.frontal import Criterion_H350M_Injury
from pyisomme.report.iihs.limits import Limit_A, Limit_G, Limit_M, Limit_P
from pyisomme.report.iihs.pages import driver_head_acceleration_spec_for
from pyisomme.report.iihs.protocols import PROTOCOL_SMALL_OVERLAP_VII
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

        def calculation(self) -> CriterionResult:
            value = 6.0 if self.automatic_poor else float(self.demerits)
            if value <= 1:
                rating, color = 0.0, Limit_G.color
            elif value <= 3:
                rating, color = -2.0, Limit_A.color
            elif value <= 5:
                rating, color = -6.0, Limit_M.color
            else:
                rating, color = -10.0, Limit_P.color
            return CriterionResult(
                channel=None,
                value=value,
                rating=rating,
                color=color,
            )

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

        def calculation(self) -> CriterionResult:
            if self.intrusion_rating not in (1, 2, 3, 4):
                raise ValueError("intrusion_rating must be 1 (Poor) through 4 (Good)")
            category = (
                1
                if self.integrity_failure
                else max(1, self.intrusion_rating - self.qualitative_downgrades)
            )
            value = category
            rating, color = {
                4: (0.0, Limit_G.color),
                3: (-2.0, Limit_A.color),
                2: (-6.0, Limit_M.color),
                1: (-10.0, Limit_P.color),
            }[category]
            return CriterionResult(
                channel=None,
                value=value,
                rating=rating,
                color=color,
            )

    def calculation(self) -> CriterionResult:
        rating = self.sum_of_children()
        value = -rating
        if value <= 3:
            color = Limit_G.color
        elif value <= 9:
            color = Limit_A.color
        elif value <= 19:
            color = Limit_M.color
        else:
            color = Limit_P.color
        return CriterionResult(
            channel=None,
            value=value,
            rating=rating,
            color=color,
        )

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
            CoverPage(self),
            ReportStatusPage(self, spec=report_status_spec_for(self)),
            ManualInputsPage(self, spec=manual_inputs_spec_for(self)),
            CriterionTablePage(
                            self,
                            name='Overall Rating',
                            title='Overall Rating',
                            spec=rating_table_spec_for(self).with_criteria(lambda report: {isomme: [report.overall(isomme), report.overall(isomme).criterion_structure, report.overall(isomme).criterion_driver.criterion_head_neck, report.overall(isomme).criterion_driver.criterion_chest, report.overall(isomme).criterion_driver.criterion_thigh_hip, report.overall(isomme).criterion_driver.criterion_leg_foot, report.overall(isomme).criterion_restraints_kinematics] for isomme in report.isomme_list}),
                        ),
            CriterionTablePage(
                            self,
                            name='Driver Injury Ratings',
                            title='Driver Injury Ratings',
                            spec=rating_table_spec_for(self).with_criteria(lambda report: {isomme: [report.overall(isomme).criterion_driver.criterion_head_neck, report.overall(isomme).criterion_driver.criterion_chest, report.overall(isomme).criterion_driver.criterion_thigh_hip, report.overall(isomme).criterion_driver.criterion_leg_foot, report.overall(isomme).criterion_driver] for isomme in report.isomme_list}),
                        ),
            CriterionValuesChartPage(
                            self,
                            spec=criterion_values_chart_spec_for(
                                self, name='Driver Values Chart', title='Driver Values'
                            ).with_criteria(lambda report: {isomme: [report.overall(isomme).criterion_driver.criterion_head_neck.criterion_hic_15, report.overall(isomme).criterion_driver.criterion_head_neck.criterion_nij, report.overall(isomme).criterion_driver.criterion_head_neck.criterion_neck_tension, report.overall(isomme).criterion_driver.criterion_head_neck.criterion_neck_compression, report.overall(isomme).criterion_driver.criterion_head_neck.criterion_tension_corridor, report.overall(isomme).criterion_driver.criterion_head_neck.criterion_compression_corridor, report.overall(isomme).criterion_driver.criterion_head_neck.criterion_shear_corridor, report.overall(isomme).criterion_driver.criterion_chest.criterion_acceleration, report.overall(isomme).criterion_driver.criterion_chest.criterion_deflection, report.overall(isomme).criterion_driver.criterion_chest.criterion_deflection_rate, report.overall(isomme).criterion_driver.criterion_chest.criterion_vc, report.overall(isomme).criterion_driver.criterion_leg_foot.criterion_tibia_femur_displacement, report.overall(isomme).criterion_driver.criterion_leg_foot.criterion_tibia_index, report.overall(isomme).criterion_driver.criterion_leg_foot.criterion_tibia_axial_force, report.overall(isomme).criterion_driver.criterion_leg_foot.criterion_foot_acceleration] for isomme in report.isomme_list}),
                        ),
            CriterionTablePage(
                            self,
                            name='Driver Values Table',
                            title='Driver Values',
                            spec=values_table_spec_for(self).with_criteria(lambda report: {isomme: [report.overall(isomme).criterion_driver.criterion_head_neck.criterion_hic_15, report.overall(isomme).criterion_driver.criterion_head_neck.criterion_nij, report.overall(isomme).criterion_driver.criterion_head_neck.criterion_neck_tension, report.overall(isomme).criterion_driver.criterion_head_neck.criterion_neck_compression, report.overall(isomme).criterion_driver.criterion_head_neck.criterion_tension_corridor, report.overall(isomme).criterion_driver.criterion_head_neck.criterion_compression_corridor, report.overall(isomme).criterion_driver.criterion_head_neck.criterion_shear_corridor, report.overall(isomme).criterion_driver.criterion_chest.criterion_acceleration, report.overall(isomme).criterion_driver.criterion_chest.criterion_deflection, report.overall(isomme).criterion_driver.criterion_chest.criterion_deflection_rate, report.overall(isomme).criterion_driver.criterion_chest.criterion_vc, report.overall(isomme).criterion_driver.criterion_thigh_hip.criterion_left, report.overall(isomme).criterion_driver.criterion_thigh_hip.criterion_right, report.overall(isomme).criterion_driver.criterion_leg_foot.criterion_tibia_femur_displacement, report.overall(isomme).criterion_driver.criterion_leg_foot.criterion_tibia_index, report.overall(isomme).criterion_driver.criterion_leg_foot.criterion_tibia_axial_force, report.overall(isomme).criterion_driver.criterion_leg_foot.criterion_foot_acceleration] for isomme in report.isomme_list}),
                        ),
            ChannelPlotPage(self, spec=driver_head_acceleration_spec_for(self)),
            HICPage(
                self,
                spec=hic_spec_for(
                    self,
                    name="Driver HIC15",
                    title="Driver HIC15",
                    timespan=15,
                ).with_position(
                    lambda report, isomme: report.overall(isomme).p_driver
                ).with_criterion(
                    lambda report, isomme: report.overall(
                        isomme
                    ).criterion_driver.criterion_head_neck.criterion_hic_15
                ),
            ),
            ChannelPlotPage(
                            self,
                            spec=channel_plot_spec_for(
                                self, name='Driver Neck NIJ', title='Driver Neck NIJ', nrows=2, ncols=2, sharey=True
                            ).with_channels(lambda report: {isomme: [[f'?{report.overall(isomme).p_driver}NIJCIPCF??00YB'], [f'?{report.overall(isomme).p_driver}NIJCIPCE??00YB'], [f'?{report.overall(isomme).p_driver}NIJCIPTF??00YB'], [f'?{report.overall(isomme).p_driver}NIJCIPTE??00YB']] for isomme in report.isomme_list}),
                        ),
            ChannelPlotPage(
                            self,
                            spec=channel_plot_spec_for(
                                self, name='Driver Neck Axial Load', title='Driver Neck Axial Load'
                            ).with_limits(lambda report: {
                                isomme: (
                                    report.overall(isomme).criterion_driver.criterion_head_neck.criterion_neck_tension.limits
                                    + report.overall(isomme).criterion_driver.criterion_head_neck.criterion_neck_compression.limits
                                )
                                for isomme in report.isomme_list
                            }).with_channels(lambda report: {isomme: [[f'?{report.overall(isomme).p_driver}NECKUP00??FOZB']] for isomme in report.isomme_list}),
                        ),
            ChannelPlotPage(
                            self,
                            spec=channel_plot_spec_for(
                                self, name='Driver Neck Load Corridors', title='Driver Neck Load Corridors', nrows=1, ncols=2
                            ).with_limits(lambda report: {
                                isomme: (
                                    report.overall(isomme).criterion_driver.criterion_head_neck.criterion_tension_corridor.limits
                                    + report.overall(isomme).criterion_driver.criterion_head_neck.criterion_compression_corridor.limits
                                    + report.overall(isomme).criterion_driver.criterion_head_neck.criterion_shear_corridor.limits
                                )
                                for isomme in report.isomme_list
                            }).with_channels(lambda report: {isomme: [[f'?{report.overall(isomme).p_driver}NECKUP00??FOZB'], [f'?{report.overall(isomme).p_driver}NECKUP00??FOXB']] for isomme in report.isomme_list}),
                        ),
            ChannelPlotPage(
                            self,
                            spec=channel_plot_spec_for(
                                self, name='Driver Chest Injury Measures', title='Driver Chest Injury Measures', nrows=2, ncols=2
                            ).with_channels(lambda report: {isomme: [[f'?{report.overall(isomme).p_driver}CHST0000??ACRA'], [f'?{report.overall(isomme).p_driver}CHST0000??DSXC'], [f'?{report.overall(isomme).p_driver}CHST0000??VEXC'], [f'?{report.overall(isomme).p_driver}VCCR0000??VEXC']] for isomme in report.isomme_list}),
                        ),
            ChannelPlotPage(
                            self,
                            spec=channel_plot_spec_for(
                                self, name='Driver Femur Axial Force', title='Driver Femur Axial Force', nrows=1, ncols=2, sharey=True
                            ).with_channels(lambda report: {isomme: [[f'?{report.overall(isomme).p_driver}FEMRLE00??FOZB'], [f'?{report.overall(isomme).p_driver}FEMRRI00??FOZB']] for isomme in report.isomme_list}),
                        ),
            ChannelPlotPage(
                            self,
                            spec=channel_plot_spec_for(
                                self, name='Driver Tibia-Femur Displacement', title='Driver Tibia-Femur Displacement', nrows=1, ncols=2, sharey=True
                            ).with_channels(lambda report: {isomme: [[f'?{report.overall(isomme).p_driver}KNSLLE00??DSXC'], [f'?{report.overall(isomme).p_driver}KNSLRI00??DSXC']] for isomme in report.isomme_list}),
                        ),
            ChannelPlotPage(
                            self,
                            spec=channel_plot_spec_for(
                                self, name='Driver Tibia Index (Total Moment)', title='Driver Tibia Index (Total Moment)', nrows=2, ncols=2, sharey=True
                            ).with_channels(lambda report: {isomme: [[f'?{report.overall(isomme).p_driver}TIINLUTO??000B'], [f'?{report.overall(isomme).p_driver}TIINRUTO??000B'], [f'?{report.overall(isomme).p_driver}TIINLLTO??000B'], [f'?{report.overall(isomme).p_driver}TIINRLTO??000B']] for isomme in report.isomme_list}),
                        ),
            ChannelPlotPage(
                            self,
                            spec=channel_plot_spec_for(
                                self, name='Driver Tibia Axial Force', title='Driver Tibia Axial Force', nrows=1, ncols=2, sharey=True
                            ).with_channels(lambda report: {isomme: [[f'?{report.overall(isomme).p_driver}TIBILELO??FOZB'], [f'?{report.overall(isomme).p_driver}TIBIRILO??FOZB']] for isomme in report.isomme_list}),
                        ),
            ChannelPlotPage(
                            self,
                            spec=channel_plot_spec_for(
                                self, name='Driver Foot Acceleration', title='Driver Foot Acceleration', nrows=1, ncols=2, sharey=True
                            ).with_channels(lambda report: {isomme: [[f'?{report.overall(isomme).p_driver}FOOTLE00??ACRB'], [f'?{report.overall(isomme).p_driver}FOOTRI00??ACRB']] for isomme in report.isomme_list}),
                        ),
        )
        self._selected_pages = list(self._available_pages)
