from __future__ import annotations

from pyisomme.isomme import Isomme
from pyisomme.limit import Limit
from pyisomme.report.criterion import Criterion, Role, sub
from pyisomme.report.ctx import from_input
from pyisomme.report.manual import Manual, manual
from pyisomme.report.page import Page_Cover, Page_Criterion_Values_Chart, Page_Criterion_Values_Table, \
    Page_Criterion_Rating_Table, Page_Plot_nxn
from pyisomme.report.report import Report
from pyisomme.report.euro_ncap.frontal_mpdb import EuroNCAP_Frontal_MPDB
from pyisomme.unit import Unit, g0
from pyisomme.report.iihs.limits import Limit_G, Limit_A, Limit_M, Limit_P

import logging
import numpy as np
from typing import Any


logger = logging.getLogger(__name__)

P_DRIVER = manual("1", source="test report", doc=(
    "Channel-code position of the driver. Defaults to the "
    "'Driver position object 1' test-info field when the test carries it."))


class Overall(Criterion):
    name = "Overall"
    role = Role.AGGREGATE
    p_driver: Manual[str, P_DRIVER]

    def __init__(self, report: Report, isomme: Isomme) -> None:
        super().__init__(report, isomme)
        # Also at construction: the pages read `p_driver` when the report is built.
        self.prepare()

    def prepare(self) -> None:
        """Take the driver position from the test info before the occupant reads it."""
        p_driver = self.isomme.get_test_info("Driver position object 1")
        if p_driver is not None:
            self.set_derived_input("p_driver", str(p_driver).strip())

    def calculation(self) -> None:
        self.rating = self.criterion_driver.rating

    class Criterion_Driver(Criterion):
        name = "Driver"
        role = Role.AGGREGATE

        def calculation(self) -> None:
            self.rating = self.criterion_head_neck.rating

        class Criterion_Head_Neck(Criterion):
            name = "Head & Neck"
            role = Role.AGGREGATE

            def calculation(self) -> None:
                self.rating = np.max([
                    self.criterion_hic_15.rating,
                    self.criterion_nij.rating,
                    self.criterion_fz_tension.rating,
                    self.criterion_fz_compression.rating,
                    self.criterion_fz_tension_corridor.rating,
                    self.criterion_fz_compression_corridor.rating,
                    self.criterion_fx_shear_corridor.rating
                ])

            class Criterion_HIC_15(Criterion):
                name = "HIC 15"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}HICR??15??00RX")
                    return [
                        Limit_G(codes, func=lambda x: 560, y_unit=1, upper=True, rating=0),
                        Limit_A(codes, func=lambda x: 560, y_unit=1, lower=True, rating=-2),
                        Limit_M(codes, func=lambda x: 700, y_unit=1, lower=True, rating=-10),
                        Limit_P(codes, func=lambda x: 840, y_unit=1, lower=True, rating=-20),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(self.ctx.code("?{p}HICR??15??00RX"))
                    self.value = self.channel.get_data()[0]
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_NIJ(Criterion):
                name = "NIJ"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}NIJCIP????00Y?")
                    return [
                        Limit_G(codes, func=lambda x: 0.8, y_unit=1, upper=True, rating=0),
                        Limit_A(codes, func=lambda x: 0.8, y_unit=1, lower=True, rating=-2),
                        Limit_M(codes, func=lambda x: 1.0, y_unit=1, lower=True, rating=-10),
                        Limit_P(codes, func=lambda x: 1.2, y_unit=1, lower=True, rating=-20),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(self.ctx.code("?{p}NIJCIP00??00YB"))
                    self.value = np.max(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Fz_Tension(Criterion):
                name = "Neck Fz Tension"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}NECKUP00??FOZ?")
                    return [
                        Limit_G(codes, lambda x: 2.6, y_unit="kN", upper=True, rating=0),
                        Limit_A(codes, lambda x: 2.6, y_unit="kN", lower=True, rating=-2),
                        Limit_M(codes, lambda x: 3.3, y_unit="kN", lower=True, rating=-10),
                        Limit_P(codes, lambda x: 4.0, y_unit="kN", lower=True, rating=-20),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(self.ctx.code("?{p}NECKUP00??FOZB")).convert_unit("kN")
                    self.value = np.max(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Fz_Compression(Criterion):
                name = "Neck Fz Compression"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}NECKUP00??FOZ?")
                    return [
                        Limit_G(codes, lambda x: -3.2, y_unit="kN", lower=True, rating=0),
                        Limit_A(codes, lambda x: -3.2, y_unit="kN", upper=True, rating=-2),
                        Limit_M(codes, lambda x: -4.0, y_unit="kN", upper=True, rating=-10),
                        Limit_P(codes, lambda x: -4.8, y_unit="kN", upper=True, rating=-20),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(self.ctx.code("?{p}NECKUP00??FOZB")).convert_unit("kN")
                    self.value = np.min(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Fz_Tension_Corridor(Criterion):
                name = "Neck Fz Tension Corridor"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}NECKUP00??FOZ?")
                    return [
                        Limit_G(codes, func=lambda x: np.interp(x, [0, 35, 45], [3.3, 2.9, 1.1]), x_unit="ms", y_unit="kN", upper=True, rating=0),
                        Limit_A(codes, func=lambda x: np.interp(x, [0, 35, 45], [3.3, 2.9, 1.1]), x_unit="ms", y_unit="kN", lower=True, rating=-2),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(self.ctx.code("?{p}NECKUP00??FOZB")).convert_unit("kN")
                    self.value = self.limits.get_limit_min_y(self.channel)
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Fz_Compression_Corridor(Criterion):
                name = "Neck Fz Compression Corridor"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}NECKUP00??FOZ?")
                    return [
                        Limit_G(codes, func=lambda x: np.interp(x, [0, 30], [-4, -1.1]), x_unit="ms", y_unit="kN", lower=True, rating=0),
                        Limit_A(codes, func=lambda x: np.interp(x, [0, 30], [-4, -1.1]), x_unit="ms", y_unit="kN", upper=True, rating=-2),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(self.ctx.code("?{p}NECKUP00??FOZB")).convert_unit("kN")
                    self.value = self.limits.get_limit_min_y(self.channel)
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Fx_Shear_Corridor(Criterion):
                name = "Neck Fx Shear Corridor"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}NECKUP00??FOX?")
                    return [
                        Limit_G(codes, func=lambda x: np.interp(x, [0, 25, 35, 45], [-3.1, -1.5, -1.5, -1.1]), x_unit="ms", y_unit="kN", lower=True, rating=0),
                        Limit_A(codes, func=lambda x: np.interp(x, [0, 25, 35, 45], [-3.1, -1.5, -1.5, -1.1]), x_unit="ms", y_unit="kN", upper=True, rating=-2),

                        Limit_G(codes, func=lambda x: np.interp(x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1]), x_unit="ms", y_unit="kN", upper=True, rating=0),
                        Limit_A(codes, func=lambda x: np.interp(x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1]), x_unit="ms", y_unit="kN", lower=True, rating=-2),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(self.ctx.code("?{p}NECKUP00??FOXB")).convert_unit("kN")
                    self.value = self.limits.get_limit_min_y(self.channel)
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            criterion_hic_15 = sub(Criterion_HIC_15)
            criterion_nij = sub(Criterion_NIJ)
            criterion_fz_tension = sub(Criterion_Fz_Tension)
            criterion_fz_compression = sub(Criterion_Fz_Compression)
            criterion_fz_tension_corridor = sub(Criterion_Fz_Tension_Corridor)
            criterion_fz_compression_corridor = sub(Criterion_Fz_Compression_Corridor)
            criterion_fx_shear_corridor = sub(Criterion_Fx_Shear_Corridor)

        class Criterion_Chest(Criterion):
            name = "Chest"
            role = Role.AGGREGATE

            def calculation(self) -> None:
                self.rating = np.max([
                    self.criterion_acceleration.rating,
                    self.criterion_deflection.rating,
                    self.criterion_deflection_rate.rating,
                    self.criterion_vc.rating,
                ])

            class Criterion_Acceleration(Criterion):
                name = "Thoracic Spine Acceleration (3ms)"  # TODO: nicht THSP?

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}CHST003C??ACR?")
                    return [
                        Limit_G(codes, func=lambda x: 60, y_unit=Unit(g0), upper=True, rating=0),
                        Limit_A(codes, func=lambda x: 60, y_unit=Unit(g0), lower=True, rating=-2),
                        Limit_M(codes, func=lambda x: 75, y_unit=Unit(g0), lower=True, rating=-10),
                        Limit_P(codes, func=lambda x: 90, y_unit=Unit(g0), lower=True, rating=-20),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(self.ctx.code("?{p}CHST003C??ACRX")).convert_unit(Unit(g0))
                    self.value = self.channel.get_data()[0]
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Deflection(Criterion):
                name = "Sternum Deflection"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("1{p}CHST0000??DSX?")
                    return [
                        Limit_G(codes, func=lambda x: -50, y_unit="mm", lower=True, rating=0),
                        Limit_A(codes, func=lambda x: -50, y_unit="mm", upper=True, rating=-2),
                        Limit_M(codes, func=lambda x: -60, y_unit="mm", upper=True, rating=-10),
                        Limit_P(codes, func=lambda x: -75, y_unit="mm", upper=True, rating=-20),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(self.ctx.code("1{p}CHST0000??DSXC")).convert_unit("mm")
                    self.value = np.min(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Deflection_Rate(Criterion):
                name = "Sternum Deflection Rate"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("1{p}CHST0000??VEX?")
                    return [
                        Limit_G(codes, func=lambda x: -6.6, y_unit="m/s", lower=True, rating=0),
                        Limit_A(codes, func=lambda x: -6.6, y_unit="m/s", upper=True, rating=-2),
                        Limit_M(codes, func=lambda x: -8.2, y_unit="m/s", upper=True, rating=-10),
                        Limit_P(codes, func=lambda x: -9.8, y_unit="m/s", upper=True, rating=-20),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(self.ctx.code("1{p}CHST0000??VEXC")).convert_unit("m/s")
                    self.value = np.min(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_VC(Criterion):
                name = "Viscous Criterion"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}VCCR0000??VEX?")
                    return [
                        Limit_P(codes, func=lambda x: -1.2, y_unit="m/s", upper=True, rating=-20),
                        Limit_M(codes, func=lambda x: -1.2, y_unit="m/s", lower=True, rating=-10),
                        Limit_A(codes, func=lambda x: -1.0, y_unit="m/s", lower=True, rating=-2),
                        Limit_G(codes, func=lambda x: -0.8, y_unit="m/s", lower=True, rating=0),

                        Limit_G(codes, func=lambda x: 0.8, y_unit="m/s", upper=True, rating=0),
                        Limit_A(codes, func=lambda x: 0.8, y_unit="m/s", lower=True, rating=-2),
                        Limit_M(codes, func=lambda x: 1.0, y_unit="m/s", lower=True, rating=-10),
                        Limit_P(codes, func=lambda x: 1.2, y_unit="m/s", lower=True, rating=-20),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(self.ctx.code("1{p}VCCR0000??VEXC")).convert_unit("m/s")
                    self.value = self.channel.get_data()[np.argmax(np.abs(self.channel.get_data()))]
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            criterion_acceleration = sub(Criterion_Acceleration)
            criterion_deflection = sub(Criterion_Deflection)
            criterion_deflection_rate = sub(Criterion_Deflection_Rate)
            criterion_vc = sub(Criterion_VC)

        class Criterion_Thigh_Hip(Criterion):
            name = "Tight & Hip"
            role = Role.AGGREGATE

            def calculation(self) -> None:
                self.rating = self.criterion_kth.rating

            class Criterion_KTH(Criterion):
                name = "Knee Thigh Hip Injury Risk (KTH)"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}KTHC??????00??")
                    return [
                        Limit_G(codes, func=lambda x: np.interp(x, [5.22, 5.69], [113.5, 113.5], left=np.inf, right=-np.inf), y_unit="N*s", x_unit="kN", upper=True, rating=0),
                        Limit_A(codes, func=lambda x: np.interp(x, [5.22, 5.69], [113.5, 113.5], left=np.inf, right=-np.inf), y_unit="N*s", x_unit="kN", lower=True, rating=-2),
                        Limit_M(codes, func=lambda x: np.interp(x, [5.92, 7.69], [127.7, 127.7], left=np.inf, right=-np.inf), y_unit="N*s", x_unit="kN", lower=True, rating=6),
                        Limit_P(codes, func=lambda x: np.interp(x, [6.38, 8.92], [137.1, 137.1], left=np.inf, right=-np.inf), y_unit="N*s", x_unit="kN", lower=True, rating=-10),
                    ]

                def calculation(self) -> None:
                    #TODO: rechts und links separat berechnen, da sonst integral zu groß wenn channel mit get_channel() berechnet wird (minum links rechts mit zeitversatz)
                    pass
                    # channel_femur_impulse = ...
                    # channel_femur_force = ...
                    # self.channel = Channel(code=channel_femur_impulse.code.set(physical_dimension="00"),
                    #                        data=...,
                    #                        unit="1",
                    #                        info=...)

            criterion_kth = sub(Criterion_KTH)

        class Criterion_Leg_Foot(Criterion):
            name = "Leg & Foot"
            role = Role.AGGREGATE

            def calculation(self) -> None:
                self.rating = np.max([
                    self.criterion_tibia_femur_displacement.rating,
                    self.criterion_tibia_index.rating,
                    self.criterion_tibia_axial_force.rating,
                    self.criterion_foot_acceleration.rating,
                ])

            class Criterion_Tibia_Femur_Displacemnt(Criterion):
                name = "Tibia/Femur Displacement"

                def define_limits(self) -> list[Limit]:
                    return [
                        #TODO
                    ]

                def calculation(self) -> None:
                    pass

            class Criterion_Tibia_Index(Criterion):
                name = "Tibia Index"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}TIIN??TO??000?")
                    return [
                        Limit_G(codes, func=lambda x: 0.8, y_unit="1", upper=True, rating=0),
                        Limit_A(codes, func=lambda x: 0.8, y_unit="1", lower=True, rating=-1),
                        Limit_M(codes, func=lambda x: 1.0, y_unit="1", lower=True, rating=-2),
                        Limit_P(codes, func=lambda x: 1.2, y_unit="1", lower=True, rating=-4),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(self.ctx.code("?{p}TIIN00TO??000B"))
                    self.value = np.max(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Tibia_Axial_Force(Criterion):
                name = "Tibia Axial Force"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}TIBI??LO??FOZ?")
                    return [
                        Limit_G(codes, func=lambda x: -4, y_unit="kN", lower=True, rating=0),
                        Limit_A(codes, func=lambda x: -4, y_unit="kN", upper=True, rating=-1),
                        Limit_M(codes, func=lambda x: -6, y_unit="kN", upper=True, rating=-2),
                        Limit_P(codes, func=lambda x: -8, y_unit="kN", upper=True, rating=-4),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(self.ctx.code("?{p}TIBI00LO??FOZA")).convert_unit("kN")
                    self.value = np.min(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Foot_Acceleration(Criterion):
                name = "Foot Acceleration"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}FOOT0000??AC??", "?{p}FOOTLE00??AC??", "?{p}FOOTRI00??AC??")
                    return [
                        Limit_G(codes, func=lambda x: 150, y_unit=Unit(g0), upper=True, rating=0),
                        Limit_A(codes, func=lambda x: 150, y_unit=Unit(g0), lower=True, rating=-1),
                        Limit_M(codes, func=lambda x: 200, y_unit=Unit(g0), lower=True, rating=-2),
                        Limit_P(codes, func=lambda x: 260, y_unit=Unit(g0), lower=True, rating=-4),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(self.ctx.code("?{p}FOOT0000??ACRA")).convert_unit(Unit(g0))
                    self.value = np.max(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            criterion_tibia_femur_displacement = sub(Criterion_Tibia_Femur_Displacemnt)
            criterion_tibia_index = sub(Criterion_Tibia_Index)
            criterion_tibia_axial_force = sub(Criterion_Tibia_Axial_Force)
            criterion_foot_acceleration = sub(Criterion_Foot_Acceleration)

        criterion_head_neck = sub(Criterion_Head_Neck)
        criterion_chest = sub(Criterion_Chest)
        criterion_thigh_hip = sub(Criterion_Thigh_Hip)
        criterion_leg_foot = sub(Criterion_Leg_Foot)

    class Criterion_Passenger(Criterion):
        class Criterion_Head_Neck(Criterion):
            pass
        class Criterion_Chest(Criterion):
            pass
        class Criterion_Femur(Criterion):
            pass
        class Criterion_Leg_Foot(Criterion):
            pass

    criterion_driver = sub(Criterion_Driver, at=from_input(P_DRIVER), role=Role.AGGREGATE)


class IIHS_Frontal_Small_Overlap(Report[Overall]):
    name = "IIHS | Frontal Impact against Small Overlap Barrier with 25% Overlap at 64 km/h"
    protocol = "VII"
    protocols = {
        "VII": "Version VII (04.2024) [references/IIHS/small_overlap_rating_protocol.pdf]",
    }

    #: The report's criterion tree, defined at module level (see `Overall`).
    Criterion_Overall = Overall

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.pages = [
            Page_Cover(self),

            self.Page_Driver_Result_Values_Chart(self),
            self.Page_Driver_Rating_Table(self),
            self.Page_Driver_Values_Table(self),
            self.Page_Driver_Head_Acceleration(self),
            self.Page_Driver_Neck_NIJ(self),
            self.Page_Driver_Neck_Load(self),
            self.Page_Driver_Neck_Load_Corridor(self),
            self.Page_Driver_Femur_Axial_Force(self),
            self.Page_Driver_Tibia_Compression(self),
            self.Page_Driver_Tibia_Index_Total(self),
            self.Page_Driver_Foot_Acceleration(self),
        ]

    class Page_Driver_Result_Values_Chart(Page_Criterion_Values_Chart):
        report: IIHS_Frontal_Small_Overlap
        name = "Driver Result Values Chart"
        title = "Driver Result"

        def __init__(self, report: IIHS_Frontal_Small_Overlap) -> None:
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_hic_15,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_nij,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_fz_tension,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_fz_compression,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_fz_tension_corridor,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_fz_compression_corridor,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_fx_shear_corridor,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest.criterion_acceleration,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest.criterion_deflection,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest.criterion_deflection_rate,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest.criterion_vc,
                self.report.criterion_overall[isomme].criterion_driver.criterion_thigh_hip.criterion_kth,
                self.report.criterion_overall[isomme].criterion_driver.criterion_leg_foot.criterion_tibia_femur_displacement,
                self.report.criterion_overall[isomme].criterion_driver.criterion_leg_foot.criterion_tibia_index,
                self.report.criterion_overall[isomme].criterion_driver.criterion_leg_foot.criterion_tibia_axial_force,
                self.report.criterion_overall[isomme].criterion_driver.criterion_leg_foot.criterion_foot_acceleration,
            ] for isomme in self.report.isomme_list}

    class Page_Driver_Rating_Table(Page_Criterion_Rating_Table):
        report: IIHS_Frontal_Small_Overlap
        name = "Driver Rating Table"
        title = "Driver Rating"

        def __init__(self, report: IIHS_Frontal_Small_Overlap) -> None:
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest,
                self.report.criterion_overall[isomme].criterion_driver.criterion_thigh_hip,
                self.report.criterion_overall[isomme].criterion_driver.criterion_leg_foot,
                self.report.criterion_overall[isomme].criterion_driver,
            ] for isomme in self.report.isomme_list}

    class Page_Driver_Values_Table(Page_Criterion_Values_Table):
        report: IIHS_Frontal_Small_Overlap
        name = "Driver Values Table"
        title = "Driver Values"

        def __init__(self, report: IIHS_Frontal_Small_Overlap) -> None:
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_hic_15,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_nij,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_fz_tension,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_fz_compression,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_fz_tension_corridor,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_fz_compression_corridor,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_fx_shear_corridor,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest.criterion_acceleration,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest.criterion_deflection,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest.criterion_deflection_rate,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest.criterion_vc,
                self.report.criterion_overall[isomme].criterion_driver.criterion_thigh_hip.criterion_kth,
                self.report.criterion_overall[isomme].criterion_driver.criterion_leg_foot.criterion_tibia_femur_displacement,
                self.report.criterion_overall[isomme].criterion_driver.criterion_leg_foot.criterion_tibia_index,
                self.report.criterion_overall[isomme].criterion_driver.criterion_leg_foot.criterion_tibia_axial_force,
                self.report.criterion_overall[isomme].criterion_driver.criterion_leg_foot.criterion_foot_acceleration,
            ] for isomme in self.report.isomme_list}

    class Page_Driver_Head_Acceleration(EuroNCAP_Frontal_MPDB.Page_Driver_Head_Acceleration):
        pass

    class Page_Driver_Neck_NIJ(Page_Plot_nxn):
        report: IIHS_Frontal_Small_Overlap
        name: str = "Driver Neck NIJ"
        title: str = "Driver Neck NIJ"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: IIHS_Frontal_Small_Overlap) -> None:
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_driver}NIJCIPCF??00YB"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}NIJCIPCE??00YB"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}NIJCIPTF??00YB"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}NIJCIPTE??00YB"]] for isomme in self.report.isomme_list}

    class Page_Driver_Neck_Load(Page_Plot_nxn):
        name: str = "Driver Neck Load"
        title: str = "Driver Neck Load"
        nrows: int = 1
        ncols: int = 1
        sharey: bool = False

        def __init__(self, report: Report) -> None:
            super().__init__(report,
                             limits=report.criterion_overall[report.isomme_list[0]].criterion_driver.criterion_head_neck.criterion_fz_tension.limits +
                                    report.criterion_overall[report.isomme_list[0]].criterion_driver.criterion_head_neck.criterion_fz_compression.limits)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_driver}NECKUP00??FOZA"]] for isomme in self.report.isomme_list}

    class Page_Driver_Neck_Load_Corridor(Page_Plot_nxn):
        name: str = "Driver Neck Load Corridor"
        title: str = "Driver Neck Load Corridor"
        nrows: int = 1
        ncols: int = 2
        sharey: bool = False

        def __init__(self, report: Report) -> None:
            super().__init__(report, limits=report.criterion_overall[report.isomme_list[0]].criterion_driver.criterion_head_neck.criterion_fz_tension_corridor.limits +
                                            report.criterion_overall[report.isomme_list[0]].criterion_driver.criterion_head_neck.criterion_fz_compression_corridor.limits +
                                            report.criterion_overall[report.isomme_list[0]].criterion_driver.criterion_head_neck.criterion_fx_shear_corridor.limits)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_driver}NECKUP00??FOZA"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}NECKUP00??FOXA"]] for isomme in self.report.isomme_list}

    class Page_Driver_Femur_Axial_Force(EuroNCAP_Frontal_MPDB.Page_Driver_Femur_Axial_Force):
        pass

    class Page_Driver_Tibia_Index_Total(Page_Plot_nxn):
        name = "Driver Tibia Index (Total Moment)"
        title = "Driver Tibia Index (Total Moment)"
        nrows = 2
        ncols = 2
        sharey = True

        def __init__(self, report: Report) -> None:
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_driver}TIINLUTO??000B"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}TIINRUTO??000B"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}TIINLLTO??000B"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}TIINRLTO??000B"]] for isomme in self.report.isomme_list}

    class Page_Driver_Tibia_Compression(EuroNCAP_Frontal_MPDB.Page_Driver_Tibia_Compression):
        pass

    class Page_Driver_Foot_Acceleration(Page_Plot_nxn):
        name: str = "Driver Foot Acceleration"
        title: str = "Driver Foot Acceleration"
        nrows: int = 1
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: Report) -> None:
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_driver}FOOTLE00??ACRA"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}FOOTRI00??ACRA"]] for isomme in self.report.isomme_list}
