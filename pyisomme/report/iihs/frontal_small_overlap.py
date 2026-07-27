from __future__ import annotations

from pyisomme.isomme import Isomme
from pyisomme.report.criterion import Criterion
from pyisomme.report.manual import Manual, manual
from pyisomme.report.page import Page_Cover, Page_Criterion_Values_Chart, Page_Criterion_Values_Table, \
    Page_Criterion_Rating_Table
from pyisomme.report.report import Report
from pyisomme.report.euro_ncap.frontal_mpdb import EuroNCAP_Frontal_MPDB
from pyisomme.unit import g0
from pyisomme.report.iihs.limits import Limit_G, Limit_A, Limit_M, Limit_P

import logging
import numpy as np
from typing import Any


logger = logging.getLogger(__name__)


class Overall(Criterion):
    name = "Overall"
    p_driver: Manual[int, manual(1, source="test report", doc=(
        "Channel-code position of the driver. Defaults to the "
        "'Driver position object 1' test-info field when the test carries it."))]

    def __init__(self, report: Report, isomme: Isomme) -> None:
        super().__init__(report, isomme)

        p_driver = isomme.get_test_info("Driver position object 1")
        if p_driver is not None:
            self.set_derived_input("p_driver", int(p_driver))

        self.criterion_driver = self.Criterion_Driver(report, isomme, p=self.p_driver)

    def sync_positions(self) -> None:
        """Honour a seating position set after construction (F15) — see ``Criterion.rebuild_child``."""
        if self.criterion_driver.p != self.p_driver:
            logger.info(f"{self}: rebuilding criterion_driver for position {self.p_driver}")
            self.rebuild_child("criterion_driver", p=self.p_driver)

    def calculation(self) -> None:
        self.sync_positions()

        self.criterion_driver.calculate()

        self.rating = self.criterion_driver.rating

    class Criterion_Driver(Criterion):
        name = "Driver"

        def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
            super().__init__(report, isomme)

            self.p = p

            self.criterion_head_neck = self.Criterion_Head_Neck(report, isomme, p=self.p)
            self.criterion_chest = self.Criterion_Chest(report, isomme, p=self.p)
            self.criterion_thigh_hip = self.Criterion_Thigh_Hip(report, isomme, p=self.p)
            self.criterion_leg_foot = self.Criterion_Leg_Foot(report, isomme, p=self.p)

        def calculation(self) -> None:
            self.criterion_head_neck.calculate()
            self.criterion_chest.calculate()
            self.criterion_thigh_hip.calculate()
            self.criterion_leg_foot.calculate()

            self.rating = self.criterion_head_neck.rating

        class Criterion_Head_Neck(Criterion):
            name = "Head & Neck"

            def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                super().__init__(report, isomme)

                self.p = p

                self.criterion_hic_15 = self.Criterion_HIC_15(report, isomme, p=self.p)
                self.criterion_nij = self.Criterion_NIJ(report, isomme, p=self.p)
                self.criterion_fz_tension = self.Criterion_Fz_Tension(report, isomme, p=self.p)
                self.criterion_fz_compression = self.Criterion_Fz_Compression(report, isomme, p=self.p)
                self.criterion_fz_tension_corridor = self.Criterion_Fz_Tension_Corridor(report, isomme, p=self.p)
                self.criterion_fz_compression_corridor = self.Criterion_Fz_Compression_Corridor(report, isomme, p=self.p)
                self.criterion_fx_shear_corridor = self.Criterion_Fx_Shear_Corridor(report, isomme, p=self.p)

            def calculation(self) -> None:
                self.criterion_hic_15.calculate()
                self.criterion_nij.calculate()
                self.criterion_fz_tension.calculate()
                self.criterion_fz_compression.calculate()
                self.criterion_fz_tension_corridor.calculate()
                self.criterion_fz_compression_corridor.calculate()
                self.criterion_fx_shear_corridor.calculate()

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

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_G([f"?{self.p}HICR??15??00RX"], func=lambda x: 560, y_unit=1, upper=True, rating=0),
                        Limit_A([f"?{self.p}HICR??15??00RX"], func=lambda x: 560, y_unit=1, lower=True, rating=-2),
                        Limit_M([f"?{self.p}HICR??15??00RX"], func=lambda x: 700, y_unit=1, lower=True, rating=-10),
                        Limit_P([f"?{self.p}HICR??15??00RX"], func=lambda x: 840, y_unit=1, lower=True, rating=-20),
                    ])

                def calculation(self) -> None:
                    self.channel = self.require_channel(f"?{self.p}HICR??15??00RX")
                    self.value = self.channel.get_data()[0]
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_NIJ(Criterion):
                name = "NIJ"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_G([f"?{self.p}NIJCIP????00Y?"], func=lambda x: 0.8, y_unit=1, upper=True, rating=0),
                        Limit_A([f"?{self.p}NIJCIP????00Y?"], func=lambda x: 0.8, y_unit=1, lower=True, rating=-2),
                        Limit_M([f"?{self.p}NIJCIP????00Y?"], func=lambda x: 1.0, y_unit=1, lower=True, rating=-10),
                        Limit_P([f"?{self.p}NIJCIP????00Y?"], func=lambda x: 1.2, y_unit=1, lower=True, rating=-20),
                    ])

                def calculation(self) -> None:
                    self.channel = self.require_channel(f"?{self.p}NIJCIP00??00YB")
                    self.value = np.max(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Fz_Tension(Criterion):
                name = "Neck Fz Tension"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_G([f"?{self.p}NECKUP00??FOZ?"], lambda x: 2.6, y_unit="kN", upper=True, rating=0),
                        Limit_A([f"?{self.p}NECKUP00??FOZ?"], lambda x: 2.6, y_unit="kN", lower=True, rating=-2),
                        Limit_M([f"?{self.p}NECKUP00??FOZ?"], lambda x: 3.3, y_unit="kN", lower=True, rating=-10),
                        Limit_P([f"?{self.p}NECKUP00??FOZ?"], lambda x: 4.0, y_unit="kN", lower=True, rating=-20),
                    ])

                def calculation(self) -> None:
                    self.channel = self.require_channel(f"?{self.p}NECKUP00??FOZB").convert_unit("kN")
                    self.value = np.max(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Fz_Compression(Criterion):
                name = "Neck Fz Compression"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_G([f"?{self.p}NECKUP00??FOZ?"], lambda x: -3.2, y_unit="kN", lower=True, rating=0),
                        Limit_A([f"?{self.p}NECKUP00??FOZ?"], lambda x: -3.2, y_unit="kN", upper=True, rating=-2),
                        Limit_M([f"?{self.p}NECKUP00??FOZ?"], lambda x: -4.0, y_unit="kN", upper=True, rating=-10),
                        Limit_P([f"?{self.p}NECKUP00??FOZ?"], lambda x: -4.8, y_unit="kN", upper=True, rating=-20),
                    ])

                def calculation(self) -> None:
                    self.channel = self.require_channel(f"?{self.p}NECKUP00??FOZB").convert_unit("kN")
                    self.value = np.min(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Fz_Tension_Corridor(Criterion):
                name = "Neck Fz Tension Corridor"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_G([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: np.interp(x, [0, 35, 45], [3.3, 2.9, 1.1]), x_unit="ms", y_unit="kN", upper=True, rating=0),
                        Limit_A([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: np.interp(x, [0, 35, 45], [3.3, 2.9, 1.1]), x_unit="ms", y_unit="kN", lower=True, rating=-2),
                    ])

                def calculation(self) -> None:
                    self.channel = self.require_channel(f"?{self.p}NECKUP00??FOZB").convert_unit("kN")
                    self.value = self.limits.get_limit_min_y(self.channel)
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Fz_Compression_Corridor(Criterion):
                name = "Neck Fx Compression Corridor"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_G([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: np.interp(x, [0, 30], [-4, -1.1]), x_unit="ms", y_unit="kN", lower=True, rating=0),
                        Limit_A([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: np.interp(x, [0, 30], [-4, -1.1]), x_unit="ms", y_unit="kN", upper=True, rating=-2),
                    ])

                def calculation(self) -> None:
                    self.channel = self.require_channel(f"?{self.p}NECKUP00??FOZB").convert_unit("kN")
                    self.value = self.limits.get_limit_min_y(self.channel)
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Fx_Shear_Corridor(Criterion):
                name = "Neck Fx Shear Corridor"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_G([f"?{self.p}NECKUP00??FOX?"], func=lambda x: np.interp(x, [0, 25, 35, 45], [-3.1, -1.5, -1.5, -1.1]), x_unit="ms", y_unit="kN", lower=True, rating=0),
                        Limit_A([f"?{self.p}NECKUP00??FOX?"], func=lambda x: np.interp(x, [0, 25, 35, 45], [-3.1, -1.5, -1.5, -1.1]), x_unit="ms", y_unit="kN", upper=True, rating=-2),

                        Limit_G([f"?{self.p}NECKUP00??FOX?"], func=lambda x: np.interp(x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1]), x_unit="ms", y_unit="kN", upper=True, rating=0),
                        Limit_A([f"?{self.p}NECKUP00??FOX?"], func=lambda x: np.interp(x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1]), x_unit="ms", y_unit="kN", lower=True, rating=-2),
                    ])

                def calculation(self) -> None:
                    self.channel = self.require_channel(f"?{self.p}NECKUP00??FOXB").convert_unit("kN")
                    self.value = self.limits.get_limit_min_y(self.channel)
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Chest(Criterion):
            name = "Chest"

            def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                super().__init__(report, isomme)

                self.p = p

                self.criterion_acceleration = self.Criterion_Acceleration(report, isomme, p)
                self.criterion_deflection = self.Criterion_Deflection(report, isomme, p)
                self.criterion_deflection_rate = self.Criterion_Deflection_Rate(report, isomme, p)
                self.criterion_vc = self.Criterion_VC(report, isomme, p)

            def calculation(self) -> None:
                self.criterion_acceleration.calculate()
                self.criterion_deflection.calculate()
                self.criterion_deflection_rate.calculate()
                self.criterion_vc.calculate()

                self.rating = np.max([
                    self.criterion_acceleration.rating,
                    self.criterion_deflection.rating,
                    self.criterion_deflection_rate.rating,
                    self.criterion_vc.rating,
                ])

            class Criterion_Acceleration(Criterion):
                name = "Thoracic Spine Acceleration (3ms)"  # TODO: nicht THSP?

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_G([f"?{self.p}CHST003C??ACR?"], func=lambda x: 60, y_unit=g0, upper=True, rating=0),
                        Limit_A([f"?{self.p}CHST003C??ACR?"], func=lambda x: 60, y_unit=g0, lower=True, rating=-2),
                        Limit_M([f"?{self.p}CHST003C??ACR?"], func=lambda x: 75, y_unit=g0, lower=True, rating=-10),
                        Limit_P([f"?{self.p}CHST003C??ACR?"], func=lambda x: 90, y_unit=g0, lower=True, rating=-20),
                    ])

                def calculation(self) -> None:
                    self.channel = self.require_channel(f"?{self.p}CHST003C??ACRX").convert_unit(g0)
                    self.value = self.channel.get_data()[0]
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Deflection(Criterion):
                name = "Sternum Deflection"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_G([f"1{self.p}CHST0000??DSX?"], func=lambda x: -50, y_unit="mm", lower=True, rating=0),
                        Limit_A([f"1{self.p}CHST0000??DSX?"], func=lambda x: -50, y_unit="mm", upper=True, rating=-2),
                        Limit_M([f"1{self.p}CHST0000??DSX?"], func=lambda x: -60, y_unit="mm", upper=True, rating=-10),
                        Limit_P([f"1{self.p}CHST0000??DSX?"], func=lambda x: -75, y_unit="mm", upper=True, rating=-20),
                    ])

                def calculation(self) -> None:
                    self.channel = self.require_channel(f"1{self.p}CHST0000??DSXC").convert_unit("mm")
                    self.value = np.min(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Deflection_Rate(Criterion):
                name = "Sternum Deflection Rate"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_G([f"1{self.p}CHST0000??VEX?"], func=lambda x: -6.6, y_unit="m/s", lower=True, rating=0),
                        Limit_A([f"1{self.p}CHST0000??VEX?"], func=lambda x: -6.6, y_unit="m/s", upper=True, rating=-2),
                        Limit_M([f"1{self.p}CHST0000??VEX?"], func=lambda x: -8.2, y_unit="m/s", upper=True, rating=-10),
                        Limit_P([f"1{self.p}CHST0000??VEX?"], func=lambda x: -9.8, y_unit="m/s", upper=True, rating=-20),
                    ])

                def calculation(self) -> None:
                    self.channel = self.require_channel(f"1{self.p}CHST0000??VEXC").convert_unit("m/s")
                    self.value = np.min(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_VC(Criterion):
                name = "Viscous Criterion"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_P([f"?{self.p}VCCR0000??VEX?"], func=lambda x: -1.2, y_unit="m/s", upper=True, rating=-20),
                        Limit_M([f"?{self.p}VCCR0000??VEX?"], func=lambda x: -1.2, y_unit="m/s", lower=True, rating=-10),
                        Limit_A([f"?{self.p}VCCR0000??VEX?"], func=lambda x: -1.0, y_unit="m/s", lower=True, rating=-2),
                        Limit_G([f"?{self.p}VCCR0000??VEX?"], func=lambda x: -0.8, y_unit="m/s", lower=True, rating=0),

                        Limit_G([f"?{self.p}VCCR0000??VEX?"], func=lambda x: 0.8, y_unit="m/s", upper=True, rating=0),
                        Limit_A([f"?{self.p}VCCR0000??VEX?"], func=lambda x: 0.8, y_unit="m/s", lower=True, rating=-2),
                        Limit_M([f"?{self.p}VCCR0000??VEX?"], func=lambda x: 1.0, y_unit="m/s", lower=True, rating=-10),
                        Limit_P([f"?{self.p}VCCR0000??VEX?"], func=lambda x: 1.2, y_unit="m/s", lower=True, rating=-20),
                    ])

                def calculation(self) -> None:
                    self.channel = self.require_channel(f"1{self.p}VCCR0000??VEXC").convert_unit("m/s")
                    self.value = self.channel.get_data()[np.argmax(np.abs(self.channel.get_data()))]
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Thigh_Hip(Criterion):
            name = "Tight & Hip"

            def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                super().__init__(report, isomme)

                self.p = p

                self.criterion_kth = self.Criterion_KTH(report, isomme, p)

            def calculation(self) -> None:
                self.criterion_kth.calculate()

                self.rating = self.criterion_kth.rating

            class Criterion_KTH(Criterion):
                name = "Knee Thigh Hip Injury Risk (KTH)"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_G([f"?{self.p}KTHC??????00??"], func=lambda x: np.interp(x, [5.22, 5.69], [113.5, 113.5], left=np.inf, right=-np.inf), y_unit="N*s", x_unit="kN", upper=True, rating=0),
                        Limit_A([f"?{self.p}KTHC??????00??"], func=lambda x: np.interp(x, [5.22, 5.69], [113.5, 113.5], left=np.inf, right=-np.inf), y_unit="N*s", x_unit="kN", lower=True, rating=-2),
                        Limit_M([f"?{self.p}KTHC??????00??"], func=lambda x: np.interp(x, [5.92, 7.69], [127.7, 127.7], left=np.inf, right=-np.inf), y_unit="N*s", x_unit="kN", lower=True, rating=6),
                        Limit_P([f"?{self.p}KTHC??????00??"], func=lambda x: np.interp(x, [6.38, 8.92], [137.1, 137.1], left=np.inf, right=-np.inf), y_unit="N*s", x_unit="kN", lower=True, rating=-10),
                    ])

                def calculation(self) -> None:
                    #TODO: rechts und links separat berechnen, da sonst integral zu groß wenn channel mit get_channel() berechnet wird (minum links rechts mit zeitversatz)
                    pass
                    # channel_femur_impulse = ...
                    # channel_femur_force = ...
                    # self.channel = Channel(code=channel_femur_impulse.code.set(physical_dimension="00"),
                    #                        data=...,
                    #                        unit="1",
                    #                        info=...)


        class Criterion_Leg_Foot(Criterion):
            name = "Leg & Foot"

            def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                super().__init__(report, isomme)

                self.p = p

                self.criterion_tibia_femur_displacement = self.Criterion_Tibia_Femur_Displacemnt(report, isomme, p=self.p)
                self.criterion_tibia_index = self.Criterion_Tibia_Index(report, isomme, p=self.p)
                self.criterion_tibia_axial_force = self.Criterion_Tibia_Axial_Force(report, isomme, p=self.p)
                self.criterion_foot_acceleration = self.Criterion_Foot_Acceleration(report, isomme, p=self.p)

            def calculation(self) -> None:
                self.criterion_tibia_femur_displacement.calculate()
                self.criterion_tibia_index.calculate()
                self.criterion_tibia_axial_force.calculate()
                self.criterion_foot_acceleration.calculate()

                self.rating = np.max([
                    self.criterion_tibia_femur_displacement.rating,
                    self.criterion_tibia_index.rating,
                    self.criterion_tibia_axial_force.rating,
                    self.criterion_foot_acceleration.rating,
                ])

            class Criterion_Tibia_Femur_Displacemnt(Criterion):
                name = "Tibia/Femur Displacement"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        #TODO
                    ])

                def calculation(self) -> None:
                    pass

            class Criterion_Tibia_Index(Criterion):
                name = "Tibia Index"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        # TODO
                    ])

                def calculation(self) -> None:
                    pass

            class Criterion_Tibia_Axial_Force(Criterion):
                name = "Tibia Axial Force"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([

                    ])
                    #TODO

                def calculation(self) -> None:
                    pass

            class Criterion_Foot_Acceleration(Criterion):
                name = "Foot Acceleration"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_G([f"?{self.p}FOOT0000??AC??", f"?{self.p}FOOTLE00??AC??", f"?{self.p}FOOTRI00??AC??"], func=lambda x: 150, y_unit=g0, upper=True, rating=0),
                        Limit_A([f"?{self.p}FOOT0000??AC??", f"?{self.p}FOOTLE00??AC??", f"?{self.p}FOOTRI00??AC??"], func=lambda x: 150, y_unit=g0, lower=True, rating=-1),
                        Limit_M([f"?{self.p}FOOT0000??AC??", f"?{self.p}FOOTLE00??AC??", f"?{self.p}FOOTRI00??AC??"], func=lambda x: 200, y_unit=g0, lower=True, rating=-2),
                        Limit_P([f"?{self.p}FOOT0000??AC??", f"?{self.p}FOOTLE00??AC??", f"?{self.p}FOOTRI00??AC??"], func=lambda x: 260, y_unit=g0, lower=True, rating=-4),
                    ])

                def calculation(self) -> None:
                    self.channel = self.require_channel(f"?{self.p}FOOT0000??ACRA").convert_unit(g0)
                    self.value = np.max(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

    class Criterion_Passenger(Criterion):
        class Criterion_Head_Neck(Criterion):
            pass
        class Criterion_Chest(Criterion):
            pass
        class Criterion_Femur(Criterion):
            pass
        class Criterion_Leg_Foot(Criterion):
            pass


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
            self.Page_Driver_Femur_Axial_Force(self),
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

    class Page_Driver_Femur_Axial_Force(EuroNCAP_Frontal_MPDB.Page_Driver_Femur_Axial_Force):
        pass
