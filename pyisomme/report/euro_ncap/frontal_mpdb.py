from __future__ import annotations

from pyisomme.isomme import Isomme
from pyisomme.report.page import Page_Cover, Page_OLC, Page_Plot_nxn, Page_Criterion_Values_Table, Page_Criterion_Rating_Table, Page_Criterion_Values_Chart
from pyisomme.report.report import Report
from pyisomme.limit import Limit
from pyisomme.calculate import calculate_olc
from pyisomme.report.euro_ncap.frontal_50kmh import EuroNCAP_Frontal_50kmh
from pyisomme.report.euro_ncap.frontal_50kmh import Criterion_UnstableAirbagContact
from pyisomme.report.euro_ncap.frontal_50kmh import Overall as Overall_Frontal_50kmh
from pyisomme.report.criterion import Criterion
from pyisomme.report.manual import Manual, manual
from pyisomme.report.euro_ncap.limits import Limit_G, Limit_P, Limit_C, Limit_M, Limit_A, Limit_W
from pyisomme.unit import Unit, g0

import logging
import numpy as np
from typing import Any


logger = logging.getLogger(__name__)


class Overall(Criterion):
    report: EuroNCAP_Frontal_MPDB
    name: str = "Overall"
    #: §3.4: the four body regions are scored on the worse of driver and passenger
    #: (16 points), and that sum is halved. The compatibility penalty of §3.3 and
    #: the door modifier then apply to this 8-point test score.
    max_rating = 8.
    source = "§3"
    p_driver: Manual[int, manual(1, source="test report", doc=(
        "Channel-code position of the driver. Defaults to the "
        "'Driver position object 1' test-info field when the test carries it."))]
    p_passenger: Manual[int, manual(3, source="test report", doc=(
        "Channel-code position of the front passenger. Derived from p_driver "
        "(1 for a right-hand-drive test) unless set explicitly."))]

    def __init__(self, report: Report, isomme: Isomme) -> None:
        super().__init__(report, isomme)

        p_driver = isomme.get_test_info("Driver position object 1")
        if p_driver is not None:
            self.set_derived_input("p_driver", int(p_driver))
        self.derive_positions()

        self.criterion_driver = self.Criterion_Driver(report, isomme, p=self.p_driver)
        self.criterion_passenger = self.Criterion_Passenger(report, isomme, p=self.p_passenger)

        self.criterion_door_opening_during_impact = Overall_Frontal_50kmh.Criterion_DoorOpeningDuringImpact(report, isomme)
        self.criterion_compatibility_modifier = self.Criterion_Compatibility_Modifier(report, isomme)

    def derive_positions(self) -> None:
        """Fill the passenger position from ``p_driver`` — see ``Criterion.set_derived_input``."""
        self.set_derived_input("p_passenger", 1 if self.p_driver != 1 else 3)

    def sync_positions(self) -> None:
        """Honour a seating position set after construction (F15) — see ``Criterion.rebuild_child``."""
        self.derive_positions()

        for attr, p in (("criterion_driver", self.p_driver),
                        ("criterion_passenger", self.p_passenger)):
            if getattr(self, attr).p != p:
                logger.info(f"{self}: rebuilding {attr} for position {p}")
                self.rebuild_child(attr, p=p)

    def calculation(self) -> None:
        self.sync_positions()

        logger.info("Calculate Driver")
        self.criterion_driver.calculate()
        logger.info("Calculate Passenger")
        self.criterion_passenger.calculate()

        self.rating = np.sum([
            np.min([
               self.criterion_driver.criterion_head_neck.rating,
               self.criterion_passenger.criterion_head_neck.rating,
            ]),
            np.min([
                self.criterion_driver.criterion_chest_abdomen.rating,
                self.criterion_passenger.criterion_chest.rating,
            ]),
            np.min([
                self.criterion_driver.criterion_knee_femur_pelvis.rating,
                self.criterion_passenger.criterion_knee_femur_pelvis.rating,
            ]),
            np.min([
                self.criterion_driver.criterion_lowerleg_foot_ankle.rating,
                self.criterion_passenger.criterion_lowerleg.rating,
            ])
        ])

        # Capping (-np.inf) leads to 0 points. More than 16 points should not be possible if sub-criteria defined correctly
        self.rating = float(np.interp(self.rating, [0, 16], [0, 16], left=0, right=np.nan))
        # §3.4: "This score is halved with a total achievable score of 8 points."
        # TODO(test): no golden fixture reaches this line with a number — the MPDB
        #   driver is nan in all three, so Overall is nan. Verified by hand only
        #   (4/4/4/4 on both occupants -> 8.0; -8 compatibility -> 0.0). Add a
        #   fixture-free regression test once Step 7's Ctx makes pinning a region's
        #   rating cheap.
        self.rating /= 2

        # Modifier — §3.3 applies the compatibility penalty to the test score, so
        # both modifiers land on the halved scale.
        self.criterion_door_opening_during_impact.calculate()
        self.criterion_compatibility_modifier.calculate()

        self.rating += np.sum([
            self.criterion_door_opening_during_impact.rating,
            self.criterion_compatibility_modifier.rating
        ])

        # A modifier must not drive the load case below zero.
        self.rating = float(np.max([0., self.rating]))

    class Criterion_Driver(Criterion):
        name = "Driver"
        max_rating, aggregation = 16., "sum"

        def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
            super().__init__(report, isomme)

            self.p = p

            self.criterion_head_neck = self.Criterion_Head_Neck(report, isomme, p=self.p)
            self.criterion_chest_abdomen = self.Criterion_Chest_Abdomen(report, isomme, p=self.p)
            self.criterion_knee_femur_pelvis = self.Criterion_Knee_Femur_Pelvis(report, isomme, p=self.p)
            self.criterion_lowerleg_foot_ankle = self.Criterion_LowerLeg_Foot_Ankle(report, isomme, p=self.p)

        def calculation(self) -> None:
            self.criterion_head_neck.calculate()
            self.criterion_chest_abdomen.calculate()
            self.criterion_knee_femur_pelvis.calculate()
            self.criterion_lowerleg_foot_ankle.calculate()

            self.rating = np.sum([
                self.criterion_head_neck.rating,
                self.criterion_chest_abdomen.rating,
                self.criterion_knee_femur_pelvis.rating,
                self.criterion_lowerleg_foot_ankle.rating,
            ])

        class Criterion_Head_Neck(Criterion):
            name = "Head & Neck"
            #: §3.4 groups head and neck into one 4-point body region.
            max_rating = 4.
            source = "§3.1.1"

            steering_wheel_airbag_exists: Manual[bool, manual(True, source="test report", doc=(
                "Is a steering-wheel airbag fitted? Without one the head & neck box scores 0."))]

            def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                super().__init__(report, isomme)

                self.p = p

                self.criterion_head = self.Criterion_Head(report, isomme, p=self.p)
                self.criterion_neck = self.Criterion_Neck(report, isomme, p=self.p)

            def calculation(self) -> None:
                if not self.steering_wheel_airbag_exists:
                    self.rating = 0
                else:
                    self.criterion_head.calculate()
                    self.criterion_neck.calculate()

                    self.rating = np.min([
                        self.criterion_head.rating,
                        self.criterion_neck.rating,
                    ])

            class Criterion_Head(Criterion):
                name = "Head"
                source = "§3.1.1"
                hard_contact: Manual[bool, manual(True, source="video", doc=(
                    "Was hard head contact observed? A head-acceleration peak above "
                    "80 g forces this to True regardless (Appendix A2: 'video OR curve')."))]

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_hic_15 = Overall_Frontal_50kmh.Criterion_Driver.Criterion_Head.Criterion_HIC_15(report, isomme, p=self.p)
                    self.criterion_head_a3ms = Overall_Frontal_50kmh.Criterion_Driver.Criterion_Head.Criterion_Head_a3ms(report, isomme, p=self.p)
                    self.criterion_damage = self.Criterion_DAMAGE(self.report, self.isomme, p=self.p)
                    self.criterion_UnstableAirbagContact = self.Criterion_UnstableAirbagContact(report, isomme, p=self.p)
                    self.criterion_HazardousAirbagDeployment = self.Criterion_HazardousAirbagDeployment(report, isomme, p=self.p)
                    self.criterion_IncorrectAirbagDeployment = self.Criterion_IncorrectAirbagDeployment(report, isomme, p=self.p)
                    self.criterion_DisplacementSteeringColumn = self.Criterion_DisplacementSteeringColumn(report, isomme, p=self.p)

                def calculation(self) -> None:
                    if np.max(np.abs(self.require_channel(f"?{self.p}HEAD??00??ACRA").get_data(unit=g0))) > 80:
                        logger.info(f"Hard Head contact assumed for p={self.p} in {self.isomme}")
                        self.hard_contact = True

                    if self.hard_contact:
                        self.criterion_hic_15.calculate()
                        self.criterion_head_a3ms.calculate()
                        self.rating = np.min([self.criterion_hic_15.rating,
                                              self.criterion_head_a3ms.rating])
                    else:
                        self.rating = 4

                    # Modifier
                    self.criterion_damage.calculate()
                    self.criterion_UnstableAirbagContact.calculate()
                    self.criterion_HazardousAirbagDeployment.calculate()
                    self.criterion_IncorrectAirbagDeployment.calculate()
                    self.criterion_DisplacementSteeringColumn.calculate()

                    self.rating += np.sum([self.criterion_damage.rating,
                                           self.criterion_UnstableAirbagContact.rating,
                                           self.criterion_HazardousAirbagDeployment.rating,
                                           self.criterion_IncorrectAirbagDeployment.rating,
                                           self.criterion_DisplacementSteeringColumn.rating])

                # §3.2.1.1 repeats §4.2.1 word for word; only the section differs.
                class Criterion_UnstableAirbagContact(Criterion_UnstableAirbagContact):  # noqa: F811 - shadows the import
                    source = "§3.2.1.1"

                class Criterion_HazardousAirbagDeployment(Overall_Frontal_50kmh.Criterion_Driver.Criterion_Head.Criterion_HazardousAirbagDeployment):
                    source = "§3.2.1.1"

                class Criterion_IncorrectAirbagDeployment(Overall_Frontal_50kmh.Criterion_Driver.Criterion_Head.Criterion_IncorrectAirbagDeployment):
                    source = "§3.2.1.1"

                class Criterion_DisplacementSteeringColumn(Overall_Frontal_50kmh.Criterion_Driver.Criterion_Head.Criterion_DisplacementSteeringColumn):
                    source = "§3.2.1.1"

                class Criterion_DAMAGE(Criterion):
                    name = "Modifier for Brain Injury - DAMAGE"
                    source = "§3.2.1.1"

                    def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit([f"?{self.p}HEADDAMA??AAR?"], func=lambda x: 0.42, y_unit="rad/s^2", rating=0.0, color="green", name="0 pt. Modifier", upper=True),
                            Limit([f"?{self.p}HEADDAMA??AAR?"], func=lambda x: 0.42, y_unit="rad/s^2", rating=-1., color="orange", name="-1 pt. Modifier", lower=True),
                            Limit([f"?{self.p}HEADDAMA??AAR?"], func=lambda x: 0.47, y_unit="rad/s^2", rating=-2., color="red", name="-2 pt. Modifier", lower=True),
                        ])

                    def calculation(self) -> None:
                        self.channel = self.require_channel(f"?{self.p}HEADDAMA??AARA")
                        self.value = np.max(self.channel.get_data())
                        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                        self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Neck(Criterion):
                name = "Neck"
                source = "§3.1.2"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_my_extension = self.Criterion_My_Extension(report, isomme, p)
                    self.criterion_fz_tension = self.Criterion_Fz_Tension(report, isomme, p)
                    self.criterion_fx_shear = self.Criterion_Fx_Shear(report, isomme, p)

                def calculation(self) -> None:
                    self.criterion_my_extension.calculate()
                    self.criterion_fz_tension.calculate()
                    self.criterion_fx_shear.calculate()

                    self.rating = np.min([
                        self.criterion_my_extension.rating,
                        self.criterion_fz_tension.rating,
                        self.criterion_fx_shear.rating,
                    ])

                class Criterion_My_Extension(Criterion):
                    name = "Neck My extension"

                    def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_G([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -42, y_unit="Nm", lower=True),
                            Limit_A([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -42, y_unit="Nm", upper=True),
                            Limit_M([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -47, y_unit="Nm", upper=True),
                            Limit_W([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -52, y_unit="Nm", upper=True),
                            Limit_P([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -57, y_unit="Nm"),
                            Limit_C([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -57, y_unit="Nm", upper=True),
                        ])

                    def calculation(self) -> None:
                        self.channel = self.require_channel(f"?{self.p}NECKUP00??MOYB")
                        self.value = np.min(self.channel.get_data(unit="Nm"))
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_Fz_Tension(Criterion):
                    name = "Neck Fz tension"

                    def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_G([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 2.7, y_unit="kN", x_unit="ms", upper=True),
                            Limit_A([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 2.7, y_unit="kN", x_unit="ms", lower=True),
                            Limit_M([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 2.9, y_unit="kN", x_unit="ms", lower=True),
                            Limit_W([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 3.1, y_unit="kN", x_unit="ms", lower=True),
                            Limit_P([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 3.3, y_unit="kN", x_unit="ms"),
                            Limit_C([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 3.3, y_unit="kN", x_unit="ms", lower=True),
                        ])

                    def calculation(self) -> None:
                        self.channel = self.require_channel(f"?{self.p}NECKUP00??FOZA").convert_unit("kN")
                        self.value = np.max(self.channel.get_data())
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_Fx_Shear(Criterion):
                    name = "Neck Fx shear"

                    def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_G([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.9, y_unit="kN", x_unit="ms", upper=True),
                            Limit_A([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.9, y_unit="kN", x_unit="ms", lower=True),
                            Limit_M([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 2.3, y_unit="kN", x_unit="ms", lower=True),
                            Limit_W([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 2.7, y_unit="kN", x_unit="ms", lower=True),
                            Limit_P([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 3.1, y_unit="kN", x_unit="ms"),
                            Limit_C([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 3.1, y_unit="kN", x_unit="ms", lower=True),

                            Limit_G([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.9, y_unit="kN", x_unit="ms", lower=True),
                            Limit_A([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.9, y_unit="kN", x_unit="ms", upper=True),
                            Limit_M([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -2.3, y_unit="kN", x_unit="ms", upper=True),
                            Limit_W([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -2.7, y_unit="kN", x_unit="ms", upper=True),
                            Limit_P([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -3.1, y_unit="kN", x_unit="ms"),
                            Limit_C([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -3.1, y_unit="kN", x_unit="ms", upper=True),
                        ])

                    def calculation(self) -> None:
                        self.channel = self.require_channel(f"?{self.p}NECKUP00??FOXA").convert_unit("kN")
                        self.value = self.channel.get_data()[np.argmax(np.abs(self.channel.get_data()))]
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Chest_Abdomen(Criterion):
            name = "Chest and Abdomen"
            #: §3.4 groups chest and abdomen into one 4-point body region.
            max_rating = 4.
            source = "§3.1.3"

            def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                super().__init__(report, isomme)

                self.p = p

                self.criterion_chest = self.Criterion_Chest(report, isomme, p)
                self.criterion_abdomen = self.Criterion_Abdomen(report, isomme, p)

            def calculation(self) -> None:
                self.criterion_chest.calculate()
                self.criterion_abdomen.calculate()

                self.rating = np.min([
                    self.criterion_chest.rating,
                    self.criterion_abdomen.rating
                ])


            class Criterion_Chest(Criterion):
                name = "Chest"
                source = "§3.1.3.1"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_chest_compression = self.Criterion_Chest_Compression(report, isomme, p=self.p)

                    self.criterion_shoulder_belt_load = Overall_Frontal_50kmh.Criterion_Driver.Criterion_Chest.Criterion_ShoulderBeltLoad(report, isomme, p=self.p)
                    self.criterion_SteeringWheelContact = self.Criterion_SteeringWheelContact(report, isomme, p=self.p)
                    self.criterion_DisplacementAPillar = self.Criterion_DisplacementAPillar(report, isomme, p=self.p)
                    self.criterion_CompartmentIntegrity = self.Criterion_CompartmentIntegrity(report, isomme, p=self.p)

                def calculation(self) -> None:
                    self.criterion_chest_compression.calculate()

                    self.rating = self.criterion_chest_compression.rating

                    # Modifier
                    self.criterion_shoulder_belt_load.calculate()
                    self.criterion_SteeringWheelContact.calculate()
                    self.criterion_DisplacementAPillar.calculate()
                    self.criterion_CompartmentIntegrity.calculate()

                    self.rating += np.sum([self.criterion_shoulder_belt_load.rating,
                                           self.criterion_SteeringWheelContact.rating,
                                           self.criterion_DisplacementAPillar.rating,
                                           self.criterion_CompartmentIntegrity.rating])

                # §3.2.1.2 repeats §4.2.2 word for word; only the section differs.
                class Criterion_SteeringWheelContact(Overall_Frontal_50kmh.Criterion_Driver.Criterion_Chest.Criterion_SteeringWheelContact):
                    source = "§3.2.1.2"

                class Criterion_DisplacementAPillar(Criterion):
                    report: EuroNCAP_Frontal_MPDB
                    name = "Modifier for Displacement of the A Pillar"
                    source = "§3.2.1.2"
                    displacement_a_pillar: Manual[float, manual(
                        0.0, unit="mm", source="measurement", doc=(
                            "Rearward displacement of the driver's front door pillar, "
                            "100 mm below the lowest level of the side window aperture. "
                            "No penalty up to 100 mm, −2 points above 200 mm, linear "
                            "in between (driver only)."))]

                    def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                        super().__init__(report, isomme)
                        self.p = p

                    def calculation(self) -> None:
                        if self.report.criterion_overall[self.isomme].p_driver != self.p:
                            self.rating = 0
                            return

                        self.value = self.displacement_a_pillar
                        self.rating = float(np.interp(self.value, [100, 200], [0, -2], left=0, right=-2))

                class Criterion_CompartmentIntegrity(Criterion):
                    report: EuroNCAP_Frontal_MPDB
                    name = "Modifier for Integrity of the Passenger Compartment"
                    source = "§3.2.1.2"
                    compartment_integrity_compromised: Manual[bool, manual(
                        False, source="test report", doc=(
                            "Structural integrity of the passenger compartment compromised "
                            "— door latch/hinge failure, door buckling, cross facia rail to "
                            "A pillar separation, or severe loss of door aperture strength. "
                            "−1 point (driver only)."))]

                    def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                        super().__init__(report, isomme)
                        self.p = p

                    def calculation(self) -> None:
                        is_driver = self.report.criterion_overall[self.isomme].p_driver == self.p
                        self.value = self.compartment_integrity_compromised
                        self.rating = -1 if is_driver and self.compartment_integrity_compromised else 0

                class Criterion_Chest_Compression(Criterion):
                    name = "Chest Compression"

                    def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_C([f"?{self.p}CHST??????DSX?"], func=lambda x: -60.000, y_unit="mm", upper=True),
                            Limit_P([f"?{self.p}CHST??????DSX?"], func=lambda x: -60.000, y_unit="mm"),
                            Limit_W([f"?{self.p}CHST??????DSX?"], func=lambda x: -51.667, y_unit="mm", upper=True),
                            Limit_M([f"?{self.p}CHST??????DSX?"], func=lambda x: -43.333, y_unit="mm", upper=True),
                            Limit_A([f"?{self.p}CHST??????DSX?"], func=lambda x: -35.000, y_unit="mm", upper=True),
                            Limit_G([f"?{self.p}CHST??????DSX?"], func=lambda x: -35.000, y_unit="mm", lower=True),
                        ])

                    def calculation(self) -> None:
                        # TODO(channel): §3.1.3.1 rates "max compression of all 4 ribs";
                        #   this reads the single aggregate channel. Confirm get_channel
                        #   synthesises the worst of the four THOR IR-TRACC channels, or
                        #   take the minimum over them here.
                        self.channel = self.require_channel(f"?{self.p}CHST0000??DSXC").convert_unit("mm")
                        self.value = np.min(self.channel.get_data())
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Abdomen(Criterion):
                name = "Abdomen"
                source = "§3.1.3.2"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_abdomen_compression = self.Criterion_Abdomen_Compression(report, isomme, p=self.p)

                def calculation(self) -> None:
                    self.criterion_abdomen_compression.calculate()

                    self.rating = self.criterion_abdomen_compression.rating

                class Criterion_Abdomen_Compression(Criterion):
                    name = "Abdomen Compression"

                    def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_P([f"?{self.p}ABDO??????DSX?"], func=lambda x: -88, y_unit="mm", upper=True),
                            Limit_G([f"?{self.p}ABDO??????DSX?"], func=lambda x: -88, y_unit="mm", lower=True),
                        ])

                    def calculation(self) -> None:
                        # TODO(channel): §3.1.3.2 rates "max compression (left or right)";
                        #   this reads the single aggregate channel. Same question as the
                        #   chest above.
                        self.channel = self.require_channel(f"?{self.p}ABDO0000??DSXC").convert_unit("mm")
                        self.value = np.min(self.channel.get_data())
                        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                        self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Knee_Femur_Pelvis(Criterion):
            name = "Knee, Femur and Pelvis"
            max_rating = 4.
            source = "§3.1.4"

            def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                super().__init__(report, isomme)

                self.p = p

                self.criterion_pelvis = self.Criterion_Pelvis(report, isomme, p=self.p)
                self.criterion_femur = self.Criterion_Femur(report, isomme, p=self.p)
                self.criterion_knee = self.Criterion_Knee(report, isomme, p=self.p)

                self.criterion_submarining = Overall_Frontal_50kmh.Criterion_Driver.Criterion_Femur.Criterion_Submarining(report, isomme, p=self.p)
                self.criterion_VariableContact = self.Criterion_VariableContact(report, isomme, p=self.p)
                self.criterion_ConcentratedLoading = self.Criterion_ConcentratedLoading(report, isomme, p=self.p)

            def calculation(self) -> None:
                self.criterion_pelvis.calculate()
                self.criterion_femur.calculate()
                self.criterion_knee.calculate()

                self.rating = np.min([
                    self.criterion_pelvis.rating,
                    self.criterion_femur.rating,
                    self.criterion_knee.rating
                ])

                # Modifier
                self.criterion_submarining.calculate()
                self.criterion_VariableContact.calculate()
                self.criterion_ConcentratedLoading.calculate()

                self.rating += np.sum([self.criterion_submarining.rating,
                                       self.criterion_VariableContact.rating,
                                       self.criterion_ConcentratedLoading.rating])

            class Criterion_VariableContact(Criterion):
                name = "Modifier for Variable Contact"
                source = "§3.2.1.4"
                variable_contact_left: Manual[bool, manual(False, source="knee mapping", doc=(
                    "Over the left knee's contact area, femur loads above 3.8 kN and/or "
                    "knee slider displacements above 6 mm would be expected. −1 point."))]
                variable_contact_right: Manual[bool, manual(False, source="knee mapping", doc=(
                    "Over the right knee's contact area, femur loads above 3.8 kN and/or "
                    "knee slider displacements above 6 mm would be expected. −1 point."))]

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)
                    self.p = p

                def calculation(self) -> None:
                    self.value = int(self.variable_contact_left) + int(self.variable_contact_right)
                    self.rating = -1. * self.value

            class Criterion_ConcentratedLoading(Criterion):
                name = "Modifier for Concentrated Loading"
                source = "§3.2.1.4"
                concentrated_loading_left: Manual[bool, manual(False, source="knee mapping", doc=(
                    "Structures in the left knee impact area could concentrate forces on "
                    "part of the knee. −1 point."))]
                concentrated_loading_right: Manual[bool, manual(False, source="knee mapping", doc=(
                    "Structures in the right knee impact area could concentrate forces on "
                    "part of the knee. −1 point."))]

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)
                    self.p = p

                def calculation(self) -> None:
                    self.value = int(self.concentrated_loading_left) + int(self.concentrated_loading_right)
                    self.rating = -1. * self.value

            class Criterion_Pelvis(Criterion):
                name = "Pelvis"
                source = "§3.1.4.1"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_acetabulum_force = self.Criterion_Acetabulum_Force(report, isomme, p=self.p)

                def calculation(self) -> None:
                    self.criterion_acetabulum_force.calculate()

                    self.rating = self.criterion_acetabulum_force.rating

                class Criterion_Acetabulum_Force(Criterion):
                    name = "Acetabulum Force"

                    def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_P([f"?{self.p}ACTB??00??FOR?"], func=lambda x: -4.100, y_unit="kN", upper=True),
                            Limit_W([f"?{self.p}ACTB??00??FOR?"], func=lambda x: -3.827, y_unit="kN", upper=True),
                            Limit_M([f"?{self.p}ACTB??00??FOR?"], func=lambda x: -3.553, y_unit="kN", upper=True),
                            Limit_A([f"?{self.p}ACTB??00??FOR?"], func=lambda x: -3.280, y_unit="kN", upper=True),
                            Limit_G([f"?{self.p}ACTB??00??FOR?"], func=lambda x: -3.280, y_unit="kN", lower=True),
                        ])

                    def calculation(self) -> None:
                        self.channel = self.require_channel(f"?{self.p}ACTB0000??FORB").convert_unit("kN")
                        self.value = np.min(self.channel.get_data())
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Femur(Criterion):
                name = "Femur"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_femur_compression = self.Criterion_Femur_Compression(report, isomme, p=self.p)

                def calculation(self) -> None:
                    self.criterion_femur_compression.calculate()

                    self.rating = self.criterion_femur_compression.rating

                class Criterion_Femur_Compression(Criterion):
                    name = "Femur Compression"

                    def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_G([f"?{self.p}FEMR??00??FOZ?"], func=lambda x: -3.8000, y_unit="kN", x_unit="ms", lower=True),
                            Limit_A([f"?{self.p}FEMR??00??FOZ?"], func=lambda x: -3.8000, y_unit="kN", x_unit="ms", upper=True),
                            Limit_M([f"?{self.p}FEMR??00??FOZ?"], func=lambda x: np.interp(x, [0, 10], [-5.557, -5.053]), y_unit="kN", x_unit="ms", upper=True),
                            Limit_W([f"?{self.p}FEMR??00??FOZ?"], func=lambda x: np.interp(x, [0, 10], [-7.313, -6.307]), y_unit="kN", x_unit="ms", upper=True),
                            Limit_P([f"?{self.p}FEMR??00??FOZ?"], func=lambda x: np.interp(x, [0, 10], [-9.070, -7.560]), y_unit="kN", x_unit="ms", upper=True),
                        ])

                    def calculation(self) -> None:
                        self.channel = self.require_channel(f"?{self.p}FEMR0000??FOZB").convert_unit("kN")
                        self.value = self.limits.get_limit_min_y(self.channel)
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Knee(Criterion):
                name = "Knee"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_knee_slider_compression = self.Criterion_Knee_Slider_Compression(report, isomme, p=self.p)

                def calculation(self) -> None:
                    self.criterion_knee_slider_compression.calculate()

                    self.rating = self.criterion_knee_slider_compression.rating

                class Criterion_Knee_Slider_Compression(Criterion):
                    name = "Knee Slider Compression"

                    def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_P([f"?{self.p}KNSL??00??DSX?"], func=lambda x: -15.0, y_unit="mm", upper=True),
                            Limit_W([f"?{self.p}KNSL??00??DSX?"], func=lambda x: -12.0, y_unit="mm", upper=True),
                            Limit_M([f"?{self.p}KNSL??00??DSX?"], func=lambda x: -9.00, y_unit="mm", upper=True),
                            Limit_A([f"?{self.p}KNSL??00??DSX?"], func=lambda x: -6.00, y_unit="mm", upper=True),
                            Limit_G([f"?{self.p}KNSL??00??DSX?"], func=lambda x: -6.00, y_unit="mm", lower=True),
                        ])

                    def calculation(self) -> None:
                        self.channel = self.require_channel(f"?{self.p}KNSL0000??DSXC").convert_unit("mm")
                        self.value = np.min(self.channel.get_data())
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_LowerLeg_Foot_Ankle(Criterion):
            name = "Lower Leg, Foot and Ankle"
            max_rating = 4.
            source = "§3.1.5"

            def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                super().__init__(report, isomme)

                self.p = p

                self.criterion_tibia_index = self.Criterion_Tibia_Index(report, isomme, p=self.p)
                self.criterion_tibia_compression = self.Criterion_Tibia_Compression(report, isomme, p=self.p)
                self.criterion_pedal_rearward_displacement = self.Criterion_Pedal_Rearward_Displacement(report, isomme, p=self.p)

                self.criterion_PedalUpwardDisplacement = self.Criterion_PedalUpwardDisplacement(report, isomme, p=self.p)
                self.criterion_FootwellRupture = self.Criterion_FootwellRupture(report, isomme, p=self.p)
                self.criterion_PedalBlocking = self.Criterion_PedalBlocking(report, isomme, p=self.p)

            def calculation(self) -> None:
                self.criterion_tibia_index.calculate()
                self.criterion_tibia_compression.calculate()
                self.criterion_pedal_rearward_displacement.calculate()

                self.rating = np.min([
                    self.criterion_tibia_index.rating,
                    self.criterion_tibia_compression.rating,
                    self.criterion_pedal_rearward_displacement.rating,
                ])

                # Modifier
                self.criterion_PedalUpwardDisplacement.calculate()
                self.criterion_FootwellRupture.calculate()
                self.criterion_PedalBlocking.calculate()

                self.rating += np.sum([self.criterion_PedalUpwardDisplacement.rating,
                                       self.criterion_FootwellRupture.rating,
                                       self.criterion_PedalBlocking.rating])

            class Criterion_PedalUpwardDisplacement(Criterion):
                name = "Modifier for Upward Displacement of the Worst Performing Pedal"
                source = "§3.2.1.5"
                pedal_upward_displacement: Manual[float, manual(
                    0.0, unit="mm", source="measurement", doc=(
                        "Upward static displacement of the worst performing pedal. No "
                        "penalty up to 90 % of the 80 mm EEVC limit, −1 point beyond "
                        "110 %, linear in between."))]

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)
                    self.p = p

                def calculation(self) -> None:
                    self.value = self.pedal_upward_displacement / 80
                    self.rating = float(np.interp(self.value, [0.9, 1.1], [0, -1], left=0, right=-1))

            class Criterion_FootwellRupture(Criterion):
                name = "Modifier for Footwell Rupture"
                source = "§3.2.1.6"
                footwell_rupture: Manual[bool, manual(False, source="test report", doc=(
                    "Significant rupture of the footwell area, usually separation of spot "
                    "welded seams. −1 point."))]

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)
                    self.p = p

                def calculation(self) -> None:
                    self.value = self.footwell_rupture
                    self.rating = -1 if self.footwell_rupture else 0

            class Criterion_PedalBlocking(Criterion):
                name = "Modifier for Pedal Blocking"
                source = "§3.2.1.6"
                blocked_pedal_rearward_displacement: Manual[float, manual(
                    0.0, unit="mm", source="measurement", doc=(
                        "Rearward displacement of a 'blocked' pedal relative to the pre-test "
                        "measurement. A pedal is blocked when its forward movement under a "
                        "200 N load is below 25 mm. Sliding scale 0 to −1 point between "
                        "50 mm and 175 mm."))]

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)
                    self.p = p

                def calculation(self) -> None:
                    self.value = self.blocked_pedal_rearward_displacement
                    self.rating = float(np.interp(self.value, [50, 175], [0, -1], left=0, right=-1))

            class Criterion_Tibia_Index(Criterion):
                name = "Tibia Index"
                source = "§3.1.5.1"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_G([f"?{self.p}TIIN??00??000?"], func=lambda x: 0.4, y_unit="1", upper=True),
                        Limit_A([f"?{self.p}TIIN??00??000?"], func=lambda x: 0.4, y_unit="1", lower=True),
                        Limit_M([f"?{self.p}TIIN??00??000?"], func=lambda x: 0.7, y_unit="1", lower=True),
                        Limit_W([f"?{self.p}TIIN??00??000?"], func=lambda x: 1.0, y_unit="1", lower=True),
                        Limit_P([f"?{self.p}TIIN??00??000?"], func=lambda x: 1.3, y_unit="1", lower=True),
                    ])

                def calculation(self) -> None:
                    self.channel = self.require_channel(f"?{self.p}TIIN0000??000B")
                    self.value = np.max(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Tibia_Compression(Criterion):
                name = "Tibia Compression"
                source = "§3.1.5.1"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_P([f"?{self.p}TIBI??????FOZ?"], func=lambda x: -8, y_unit="kN", upper=True),
                        Limit_W([f"?{self.p}TIBI??????FOZ?"], func=lambda x: -6, y_unit="kN", upper=True),
                        Limit_M([f"?{self.p}TIBI??????FOZ?"], func=lambda x: -4, y_unit="kN", upper=True),
                        Limit_A([f"?{self.p}TIBI??????FOZ?"], func=lambda x: -2, y_unit="kN", upper=True),
                        Limit_G([f"?{self.p}TIBI??????FOZ?"], func=lambda x: -2, y_unit="kN", lower=True),
                    ])

                def calculation(self) -> None:
                    self.channel = self.require_channel(f"?{self.p}TIBI0000??FOZB").convert_unit("kN")
                    self.value = np.min(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=True)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Pedal_Rearward_Displacement(Criterion):
                name = "Pedal Rearward Displacement"
                source = "§3.1.5.2"
                pedal_rearward_displacement: Manual[float, manual(
                    0, unit="mm", source="measurement",
                    doc="Rearward displacement of the pedal (4 points below 100 mm, 0 above 200 mm).")]

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                def calculation(self) -> None:
                    self.value = self.pedal_rearward_displacement
                    self.rating = float(np.interp(self.value, [100, 200], [4, 0], left=4))

    class Criterion_Passenger(Criterion):
        report: EuroNCAP_Frontal_MPDB
        name = "Passenger"
        max_rating, aggregation = 16., "sum"

        def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
            super().__init__(report, isomme)

            self.p = p

            self.criterion_head_neck = self.Criterion_Head_Neck(report, isomme, p)
            self.criterion_chest = self.Criterion_Chest(report, isomme, p)
            self.criterion_knee_femur_pelvis = self.Criterion_Knee_Femur_Pelvis(report, isomme, p)
            self.criterion_lowerleg = self.Criterion_LowerLeg(report, isomme, p)

        def calculation(self) -> None:
            self.criterion_head_neck.calculate()
            self.criterion_chest.calculate()
            self.criterion_knee_femur_pelvis.calculate()
            self.criterion_lowerleg.calculate()

            self.rating = np.sum([
                self.criterion_head_neck.rating,
                self.criterion_chest.rating,
                self.criterion_knee_femur_pelvis.rating,
                self.criterion_lowerleg.rating,
            ])

        class Criterion_Head_Neck(Criterion):
            name = "Head and Neck"
            max_rating = 4.
            source = "§3.1.6"

            def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                super().__init__(report, isomme)

                self.p = p

                self.criterion_head = self.Criterion_Head(report, isomme, p)
                self.criterion_neck = self.Criterion_Neck(report, isomme, p)

            def calculation(self) -> None:
                self.criterion_head.calculate()
                self.criterion_neck.calculate()

                self.rating = self.value = np.min([
                    self.criterion_head.rating,
                    self.criterion_neck.rating,
                ])

            class Criterion_Head(Criterion):
                name = "Head"
                source = "§3.1.6.1"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    # §3.1.1.1: "These criteria are always used for the passenger" —
                    # no hard-contact branch here, unlike the driver.
                    self.criterion_hic_15 = Overall_Frontal_50kmh.Criterion_Driver.Criterion_Head.Criterion_HIC_15(report, isomme, p=self.p)
                    self.criterion_head_a3ms = Overall_Frontal_50kmh.Criterion_Driver.Criterion_Head.Criterion_Head_a3ms(report, isomme, p=self.p)
                    self.criterion_UnstableAirbagContact = Overall.Criterion_Driver.Criterion_Head_Neck.Criterion_Head.Criterion_UnstableAirbagContact(report, isomme, p=self.p)
                    self.criterion_HazardousAirbagDeployment = Overall.Criterion_Driver.Criterion_Head_Neck.Criterion_Head.Criterion_HazardousAirbagDeployment(report, isomme, p=self.p)
                    self.criterion_IncorrectAirbagDeployment = Overall.Criterion_Driver.Criterion_Head_Neck.Criterion_Head.Criterion_IncorrectAirbagDeployment(report, isomme, p=self.p)

                def calculation(self) -> None:
                    self.criterion_hic_15.calculate()
                    self.criterion_head_a3ms.calculate()

                    self.rating = self.value = np.min([
                        self.criterion_hic_15.rating,
                        self.criterion_head_a3ms.rating,
                    ])

                    # Modifier — §3.2.2 gives the passenger the airbag modifiers but
                    # neither the steering column nor the compartment ones.
                    self.criterion_UnstableAirbagContact.calculate()
                    self.criterion_HazardousAirbagDeployment.calculate()
                    self.criterion_IncorrectAirbagDeployment.calculate()

                    self.rating += np.sum([self.criterion_UnstableAirbagContact.rating,
                                           self.criterion_HazardousAirbagDeployment.rating,
                                           self.criterion_IncorrectAirbagDeployment.rating])

            class Criterion_Neck(Criterion):
                name = "Neck"
                source = "§3.1.6.2"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_fx_shear = self.Criterion_Fx_Shear(report, isomme, p)
                    self.criterion_fz_tension = self.Criterion_Fz_Tension(report, isomme, p)
                    self.criterion_my_extension = self.Criterion_My_Extension(report, isomme, p)

                def calculation(self) -> None:
                    self.criterion_fx_shear.calculate()
                    self.criterion_fz_tension.calculate()
                    self.criterion_my_extension.calculate()

                    self.rating = self.value = np.min([
                        self.criterion_fx_shear.rating,
                        self.criterion_fz_tension.rating,
                        self.criterion_my_extension.rating,
                    ])

                class Criterion_Fx_Shear(Criterion):
                    name = "Neck Fx shear"

                    def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_G([f"?{self.p}NECKUP00??FOX?"], func=lambda x: np.interp(x, [0, 25, 35, 45], [1.9, 1.2, 1.2, 1.1]), y_unit="kN", x_unit="ms", upper=True),
                            Limit_A([f"?{self.p}NECKUP00??FOX?"], func=lambda x: np.interp(x, [0, 25, 35, 45], [1.9, 1.2, 1.2, 1.1]), y_unit="kN", x_unit="ms", lower=True),
                            Limit_M([f"?{self.p}NECKUP00??FOX?"], func=lambda x: np.interp(x, [0, 25, 35, 45], [2.3, 1.3, 1.3, 1.1]), y_unit="kN", x_unit="ms", lower=True),
                            Limit_W([f"?{self.p}NECKUP00??FOX?"], func=lambda x: np.interp(x, [0, 25, 35, 45], [2.7, 1.4, 1.4, 1.1]), y_unit="kN", x_unit="ms", lower=True),
                            Limit_P([f"?{self.p}NECKUP00??FOX?"], func=lambda x: np.interp(x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1]), y_unit="kN", x_unit="ms"),
                            Limit_C([f"?{self.p}NECKUP00??FOX?"], func=lambda x: np.interp(x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1]), y_unit="kN", x_unit="ms", lower=True),

                            Limit_G([f"?{self.p}NECKUP00??FOX?"], func=lambda x: np.interp(x, [0, 25, 35, 45], [-1.9, -1.2, -1.2, -1.1]), y_unit="kN", x_unit="ms", lower=True),
                            Limit_A([f"?{self.p}NECKUP00??FOX?"], func=lambda x: np.interp(x, [0, 25, 35, 45], [-1.9, -1.2, -1.2, -1.1]), y_unit="kN", x_unit="ms", upper=True),
                            Limit_M([f"?{self.p}NECKUP00??FOX?"], func=lambda x: np.interp(x, [0, 25, 35, 45], [-2.3, -1.3, -1.3, -1.1]), y_unit="kN", x_unit="ms", upper=True),
                            Limit_W([f"?{self.p}NECKUP00??FOX?"], func=lambda x: np.interp(x, [0, 25, 35, 45], [-2.7, -1.4, -1.4, -1.1]), y_unit="kN", x_unit="ms", upper=True),
                            Limit_P([f"?{self.p}NECKUP00??FOX?"], func=lambda x: np.interp(x, [0, 25, 35, 45], [-3.1, -1.5, -1.5, -1.1]), y_unit="kN", x_unit="ms"),
                            Limit_C([f"?{self.p}NECKUP00??FOX?"], func=lambda x: np.interp(x, [0, 25, 35, 45], [-3.1, -1.5, -1.5, -1.1]), y_unit="kN", x_unit="ms", upper=True),
                        ])

                    def calculation(self) -> None:
                        self.channel = self.require_channel(f"?{self.p}NECKUP00??FOXA").convert_unit("kN")
                        self.value = self.limits.get_limit_min_y(self.channel)
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_Fz_Tension(Criterion):
                    name = "Fz Tension"

                    def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_G([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: np.interp(x, [0, 35, 60], [2.7, 2.3, 1.1]), y_unit="kN", x_unit="ms", upper=True),
                            Limit_A([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: np.interp(x, [0, 35, 60], [2.7, 2.3, 1.1]), y_unit="kN", x_unit="ms", lower=True),
                            Limit_M([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: np.interp(x, [0, 35, 60], [2.9, 2.5, 1.1]), y_unit="kN", x_unit="ms", lower=True),
                            Limit_W([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: np.interp(x, [0, 35, 60], [3.1, 2.7, 1.1]), y_unit="kN", x_unit="ms", lower=True),
                            Limit_P([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: np.interp(x, [0, 35, 60], [3.3, 2.9, 1.1]), y_unit="kN", x_unit="ms"),
                            Limit_C([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: np.interp(x, [0, 35, 60], [3.3, 2.9, 1.1]), y_unit="kN", x_unit="ms", lower=True),
                        ])

                    def calculation(self) -> None:
                        self.channel = self.require_channel(f"?{self.p}NECKUP00??FOZA").convert_unit("kN")
                        self.value = self.limits.get_limit_min_y(self.channel)
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_My_Extension(Criterion):
                    name = "My Extension"

                    def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_G([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -42, y_unit="Nm", lower=True),
                            Limit_A([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -42, y_unit="Nm", upper=True),
                            Limit_M([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -47, y_unit="Nm", upper=True),
                            Limit_W([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -52, y_unit="Nm", upper=True),
                            Limit_P([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -57, y_unit="Nm"),
                            Limit_C([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -57, y_unit="Nm", upper=True),
                        ])

                    def calculation(self) -> None:
                        self.channel = self.require_channel(f"?{self.p}NECKUP00??MOYB").convert_unit("Nm")
                        self.value = np.min(self.channel.get_data())
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Chest(Criterion):
            name = "Chest"
            #: §3.4 groups chest and abdomen into one 4-point body region; only the
            #: chest is measured on the passenger (§3.1.7).
            max_rating = 4.
            source = "§3.1.7"

            def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                super().__init__(report, isomme)

                self.p = p

                self.criterion_chest_compression = self.Criterion_Chest_Compression(report, isomme, p)
                self.criterion_chest_vc = Overall_Frontal_50kmh.Criterion_Driver.Criterion_Chest.Criterion_Chest_VC(report, isomme, p)

                self.criterion_shoulder_belt_load = Overall_Frontal_50kmh.Criterion_Driver.Criterion_Chest.Criterion_ShoulderBeltLoad(report, isomme, p=self.p)

            def calculation(self) -> None:
                self.criterion_chest_compression.calculate()
                self.criterion_chest_vc.calculate()

                self.rating = self.value = np.min([
                    self.criterion_chest_compression.rating,
                    self.criterion_chest_vc.rating,
                ])

                # Modifier
                self.criterion_shoulder_belt_load.calculate()
                self.rating += self.criterion_shoulder_belt_load.rating

            class Criterion_Chest_Compression(Criterion):
                name = "Chest Compression"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_C([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -42.000, y_unit="mm", upper=True),
                        Limit_P([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -42.000, y_unit="mm"),
                        Limit_W([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -35.333, y_unit="mm", upper=True),
                        Limit_M([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -28.667, y_unit="mm", upper=True),
                        Limit_A([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -22.000, y_unit="mm", upper=True),
                        Limit_G([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -22.000, y_unit="mm", lower=True),
                    ])

                def calculation(self) -> None:
                    self.channel = self.require_channel(f"?{self.p}CHST0003??DSXC", f"?{self.p}CHST0000??DSXC").convert_unit("mm")
                    self.value = np.min(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=True)
                    self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Knee_Femur_Pelvis(Criterion):
            report: EuroNCAP_Frontal_MPDB
            name = "Knee, Femur and Pelvis"
            #: §3.4 groups pelvis and upper leg into one 4-point body region; §3.1.8
            #: has no acetabulum row for the passenger.
            max_rating = 4.
            source = "§3.1.8"

            def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                super().__init__(report, isomme)

                self.p = p

                self.criterion_femur_compression = Overall.Criterion_Driver.Criterion_Knee_Femur_Pelvis.Criterion_Femur.Criterion_Femur_Compression(report, isomme, p)
                self.criterion_knee_slider_compression = Overall.Criterion_Driver.Criterion_Knee_Femur_Pelvis.Criterion_Knee.Criterion_Knee_Slider_Compression(report, isomme, p)

                # §3.2.2: the passenger gets the two knee modifiers but not
                # submarining, which §3.2.1.3 scopes to the driver.
                self.criterion_VariableContact = Overall.Criterion_Driver.Criterion_Knee_Femur_Pelvis.Criterion_VariableContact(report, isomme, p=self.p)
                self.criterion_ConcentratedLoading = Overall.Criterion_Driver.Criterion_Knee_Femur_Pelvis.Criterion_ConcentratedLoading(report, isomme, p=self.p)

            def calculation(self) -> None:
                self.criterion_femur_compression.calculate()
                self.criterion_knee_slider_compression.calculate()

                self.rating = self.value = np.min([
                    self.criterion_femur_compression.rating,
                    self.criterion_knee_slider_compression.rating,
                ])

                # Modifier
                self.criterion_VariableContact.calculate()
                self.criterion_ConcentratedLoading.calculate()

                self.rating += np.sum([self.criterion_VariableContact.rating,
                                       self.criterion_ConcentratedLoading.rating])

        class Criterion_LowerLeg(Criterion):
            report: EuroNCAP_Frontal_MPDB
            name = "Lower Leg"
            #: §3.4 groups lower leg and foot into one 4-point body region; §3.1.9
            #: has no pedal row for the passenger.
            max_rating = 4.
            source = "§3.1.9"

            def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                super().__init__(report, isomme)

                self.p = p

                self.criterion_tibia_index = Overall.Criterion_Driver.Criterion_LowerLeg_Foot_Ankle.Criterion_Tibia_Index(report, isomme, p=self.p)
                self.criterion_tibia_compression = Overall.Criterion_Driver.Criterion_LowerLeg_Foot_Ankle.Criterion_Tibia_Compression(report, isomme, p=self.p)

            def calculation(self) -> None:
                self.criterion_tibia_index.calculate()
                self.criterion_tibia_compression.calculate()

                self.rating = np.min([
                    self.criterion_tibia_index.rating,
                    self.criterion_tibia_compression.rating,
                ])

    class Criterion_Compatibility_Modifier(Criterion):
        name = "Compatibility Modifier"
        source = "§3.3"

        def __init__(self, report: Report, isomme: Isomme) -> None:
            super().__init__(report, isomme)

            self.criterion_olc_modifier = self.Criterion_OLC_Modifier(report, isomme)
            # self.criterion_sd_modifier = self.Criterion_SD_Modifier(report, isomme)
            # self.criterion_bo_modifier = self.Criterion_BO_Modifier(report, isomme)

        def calculation(self) -> None:
            self.criterion_olc_modifier.calculate()
            # self.criterion_sd_modifier.calculate()
            # self.criterion_bo_modifier.calculate()

            self.value = np.sum([
                self.criterion_olc_modifier.rating,
                # self.criterion_sd_modifier.rating,
                # self.criterion_bo_modifier.rating
            ])
            self.rating = float(np.interp(self.value, [-8, 0], [-8, 0]))  # penalty will not exceed -8 pts.

        class Criterion_OLC_Modifier(Criterion):
            name = "Occupant Load Criterion (OLC) Modifier"

            def __init__(self, report: Report, isomme: Isomme) -> None:
                super().__init__(report, isomme)

                self.extend_limit_list([
                    Limit(["M?MBAR0OLC??VEX?"], func=lambda x: 25, y_unit=Unit(g0), name="0 pt. Modifier", rating=0, upper=True),
                    Limit(["M?MBAR0OLC??VEX?"], func=lambda x: 25, y_unit=Unit(g0), name="-2..0 pt. Modifier", rating=0, lower=True),
                    Limit(["M?MBAR0OLC??VEX?"], func=lambda x: 40, y_unit=Unit(g0), name="-2 pt. Modifier", rating=-2, lower=True),
                ])

            def calculation(self) -> None:
                self.channel = calculate_olc(self.require_channel("M?MBAR0000??VEXA", "M?MBARCG00??VEXA"))[0]
                self.value = self.channel.get_data(unit=g0)[0]
                self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=True)

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


class EuroNCAP_Frontal_MPDB(Report[Overall]):
    name = "Euro NCAP | Frontal-Impact against MPDB with 50 % Overlap at 50/50 km/h"
    protocol = "9.3"
    protocols = {
        "9.3": "Version 9.3 (05.12.2023) [references/Euro-NCAP/euro-ncap-assessment-protocol-aop-v93.pdf]"
    }

    #: The report's criterion tree, defined at module level (see `Overall`).
    Criterion_Overall = Overall

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.pages = [
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

            self.Page_OLC_Trolley(self)
        ]

    class Page_Rating_Table(Page_Criterion_Rating_Table):
        report: EuroNCAP_Frontal_MPDB
        name = "Rating"
        title = "Rating"

        def __init__(self, report: EuroNCAP_Frontal_MPDB) -> None:
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_driver,
                self.report.criterion_overall[isomme].criterion_passenger,
                self.report.criterion_overall[isomme].criterion_compatibility_modifier,
                self.report.criterion_overall[isomme].criterion_door_opening_during_impact,
                self.report.criterion_overall[isomme],
            ] for isomme in self.report.isomme_list}

    class Page_Driver_Result_Values_Chart(Page_Criterion_Values_Chart):
        report: EuroNCAP_Frontal_MPDB
        name = "Driver Result Values Chart"
        title = "Driver Result"

        def __init__(self, report: EuroNCAP_Frontal_MPDB) -> None:
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_head.criterion_hic_15,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_head.criterion_head_a3ms,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_head.criterion_damage,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_neck.criterion_my_extension,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_neck.criterion_fz_tension,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_neck.criterion_fx_shear,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest_abdomen.criterion_chest.criterion_shoulder_belt_load,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest_abdomen.criterion_chest.criterion_chest_compression,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest_abdomen.criterion_abdomen.criterion_abdomen_compression,
                self.report.criterion_overall[isomme].criterion_driver.criterion_knee_femur_pelvis.criterion_pelvis.criterion_acetabulum_force,
                self.report.criterion_overall[isomme].criterion_driver.criterion_knee_femur_pelvis.criterion_femur.criterion_femur_compression,
                self.report.criterion_overall[isomme].criterion_driver.criterion_knee_femur_pelvis.criterion_knee.criterion_knee_slider_compression,
                self.report.criterion_overall[isomme].criterion_driver.criterion_lowerleg_foot_ankle.criterion_tibia_index,
                self.report.criterion_overall[isomme].criterion_driver.criterion_lowerleg_foot_ankle.criterion_tibia_compression,
            ] for isomme in self.report.isomme_list}

    class Page_Driver_Rating_Table(Page_Criterion_Rating_Table):
        report: EuroNCAP_Frontal_MPDB
        name = "Driver Rating Table"
        title = "Driver Rating"

        def __init__(self, report: EuroNCAP_Frontal_MPDB) -> None:
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest_abdomen,
                self.report.criterion_overall[isomme].criterion_driver.criterion_knee_femur_pelvis.criterion_knee,
                self.report.criterion_overall[isomme].criterion_driver.criterion_lowerleg_foot_ankle,
                self.report.criterion_overall[isomme].criterion_driver,
            ] for isomme in self.report.isomme_list}

    class Page_Driver_Values_Table(Page_Criterion_Values_Table):
        report: EuroNCAP_Frontal_MPDB
        name = "Driver Values Table"
        title = "Driver Values"

        def __init__(self, report: EuroNCAP_Frontal_MPDB) -> None:
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_head.criterion_hic_15,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_head.criterion_head_a3ms,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_head.criterion_damage,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_neck.criterion_my_extension,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_neck.criterion_fz_tension,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck.criterion_neck.criterion_fx_shear,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest_abdomen.criterion_chest.criterion_shoulder_belt_load,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest_abdomen.criterion_chest.criterion_chest_compression,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest_abdomen.criterion_abdomen.criterion_abdomen_compression,
                self.report.criterion_overall[isomme].criterion_driver.criterion_knee_femur_pelvis.criterion_pelvis.criterion_acetabulum_force,
                self.report.criterion_overall[isomme].criterion_driver.criterion_knee_femur_pelvis.criterion_femur.criterion_femur_compression,
                self.report.criterion_overall[isomme].criterion_driver.criterion_knee_femur_pelvis.criterion_knee.criterion_knee_slider_compression,
                self.report.criterion_overall[isomme].criterion_driver.criterion_lowerleg_foot_ankle.criterion_tibia_index,
                self.report.criterion_overall[isomme].criterion_driver.criterion_lowerleg_foot_ankle.criterion_tibia_compression,
            ] for isomme in self.report.isomme_list}

    class Page_Driver_Belt(EuroNCAP_Frontal_50kmh.Page_Driver_Belt):
        pass

    class Page_Driver_Head_Acceleration(EuroNCAP_Frontal_50kmh.Page_Driver_Head_Acceleration):
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
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_driver}HEADDAMA??AAXA"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}HEADDAMA??AAYA"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}HEADDAMA??AAZA"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}HEADDAMA??AARA"]] for isomme in self.report.isomme_list}

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
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_driver}CHSTLEUP??DSXC"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}CHSTRIUP??DSXC"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}CHSTLELO??DSXC"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}CHSTRILO??DSXC"]] for isomme in self.report.isomme_list}

    class Page_Driver_Abdomen_Compression(Page_Plot_nxn):
        report: EuroNCAP_Frontal_MPDB
        name = "Driver Abdomen Compression"
        title = "Driver Abdomen Compression"
        nrows = 1
        ncols = 2

        def __init__(self, report: EuroNCAP_Frontal_MPDB) -> None:
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_driver}ABDOLE00??DSXC"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}ABDORI00??DSXC"]] for isomme in self.report.isomme_list}

    class Page_Driver_Femur_Axial_Force(EuroNCAP_Frontal_50kmh.Page_Driver_Femur_Axial_Force):
        pass

    class Page_Driver_Tibia_Compression(Page_Plot_nxn):
        name = "Driver Tibia Compression"
        title = "Driver Tibia Compression"
        nrows = 2
        ncols = 2
        sharey = True

        def __init__(self, report: Report) -> None:
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_driver}TIBILEUP??FOZB"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}TIBIRIUP??FOZB"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}TIBILELO??FOZB"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}TIBIRILO??FOZB"]] for isomme in self.report.isomme_list}

    class Page_Driver_Tibia_Index(Page_Plot_nxn):
        name = "Driver Tibia Index"
        title = "Driver Tibia Index"
        nrows = 2
        ncols = 2
        sharey = True

        def __init__(self, report: Report) -> None:
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_driver}TIINLU00??000B"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}TIINRU00??000B"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}TIINLL00??000B"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}TIINRL00??000B"]] for isomme in self.report.isomme_list}

    class Page_Driver_Knee_Slider_Compression(Page_Plot_nxn):
        name = "Driver Knee Slider Compression"
        title = "Driver Knee Slider Compression"
        nrows = 1
        ncols = 2
        sharey = True

        def __init__(self, report: Report) -> None:
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_driver}KNSLLE00??DSXC"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}KNSLRI00??DSXC"]]for isomme in self.report.isomme_list}

    class Page_Passenger_Result_Values_Chart(Page_Criterion_Values_Chart):
        report: EuroNCAP_Frontal_MPDB
        name = "Passenger Result Values Chart"
        title = "Passenger Result"

        def __init__(self, report: EuroNCAP_Frontal_MPDB) -> None:
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_passenger.criterion_head_neck.criterion_head.criterion_hic_15,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_head_neck.criterion_head.criterion_head_a3ms,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_head_neck.criterion_neck.criterion_fx_shear,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_head_neck.criterion_neck.criterion_fz_tension,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_head_neck.criterion_neck.criterion_my_extension,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_chest.criterion_shoulder_belt_load,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_chest.criterion_chest_compression,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_chest.criterion_chest_vc,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_knee_femur_pelvis.criterion_femur_compression,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_knee_femur_pelvis.criterion_knee_slider_compression,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_lowerleg.criterion_tibia_index,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_lowerleg.criterion_tibia_compression,
            ] for isomme in self.report.isomme_list}

    class Page_Passenger_Rating_Table(Page_Criterion_Rating_Table):
        report: EuroNCAP_Frontal_MPDB
        name: str = "Passenger Rating Table"
        title: str = "Passenger Rating"
        table_content: dict

        def __init__(self, report: EuroNCAP_Frontal_MPDB) -> None:
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_passenger.criterion_head_neck,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_chest,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_knee_femur_pelvis,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_lowerleg,
                self.report.criterion_overall[isomme].criterion_passenger,
            ] for isomme in self.report.isomme_list}

    class Page_Passenger_Values_Table(Page_Criterion_Values_Table):
        report: EuroNCAP_Frontal_MPDB
        name: str = "Passenger Values Table"
        title: str = "Passenger Values"

        def __init__(self, report: EuroNCAP_Frontal_MPDB) -> None:
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_passenger.criterion_head_neck.criterion_head.criterion_hic_15,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_head_neck.criterion_head.criterion_head_a3ms,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_head_neck.criterion_neck.criterion_fx_shear,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_head_neck.criterion_neck.criterion_fz_tension,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_head_neck.criterion_neck.criterion_my_extension,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_chest.criterion_shoulder_belt_load,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_chest.criterion_chest_compression,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_chest.criterion_chest_vc,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_knee_femur_pelvis.criterion_femur_compression,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_knee_femur_pelvis.criterion_knee_slider_compression,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_lowerleg.criterion_tibia_index,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_lowerleg.criterion_tibia_compression,
            ] for isomme in self.report.isomme_list}

    class Page_Passenger_Belt(Page_Plot_nxn):
        report: EuroNCAP_Frontal_MPDB
        name: str = "Passenger Belt"
        title: str = "Passenger Belt"
        nrows: int = 3
        ncols: int = 2
        sharey: bool = False

        def __init__(self, report: EuroNCAP_Frontal_MPDB) -> None:
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_passenger}SEBE000[30]B1FO[X0]C"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}SEBE000[30]B2FO[X0]C"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}SEBE000[30]B3FO[X0]C"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}SEBE000[30]B4FO[X0]C"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}SEBE000[30]B5FO[X0]C"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}SEBE000[30]B6FO[X0]C"]] for isomme in self.report.isomme_list}

    class Page_Passenger_Head_Acceleration(Page_Plot_nxn):
        name: str = "Passenger Head Acceleration"
        title: str = "Passenger Head Acceleration"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: Report) -> None:
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_passenger}HEAD??????AC{xyzr}A"] for xyzr in "XYZR"] for isomme in self.report.isomme_list}

    class Page_Passenger_Neck_Load(Page_Plot_nxn):
        name: str = "Passenger Neck Load"
        title: str = "Passenger Neck Load"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = False

        def __init__(self, report: Report) -> None:
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_passenger}NECKUP00??MOYB"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}NECKUP00??FOZA"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}NECKUP00??FOXA"]] for isomme in self.report.isomme_list}

    class Page_Passenger_Chest_Deflection(Page_Plot_nxn):
        name: str = "Passenger Chest Deflection"
        title: str = "Passenger Chest Deflection"
        nrows: int = 1
        ncols: int = 2

        def __init__(self, report: Report) -> None:
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_passenger}CHST000???DSXC"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}VCCR000???VEXC"]] for isomme in self.report.isomme_list}

    class Page_Passenger_Femur_Axial_Force(Page_Plot_nxn):
        name: str = "Passenger Femur Axial Force"
        title: str = "Passenger Femur Axial Force"
        nrows: int = 1
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: Report) -> None:
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_passenger}FEMRLE00??FOZB"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}FEMRRI00??FOZB"]] for isomme in self.report.isomme_list}

    class Page_Passenger_Knee_Slider_Compression(Page_Plot_nxn):
        name = "Passenger Knee Slider Compression"
        title = "Passenger Knee Slider Compression"
        nrows = 1
        ncols = 2
        sharey = True

        def __init__(self, report: Report) -> None:
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_passenger}KNSLLE00??DSXC"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}KNSLRI00??DSXC"]]for isomme in self.report.isomme_list}

    class Page_Passenger_Tibia_Compression(Page_Plot_nxn):
        name = "Passenger Tibia Compression"
        title = "Passenger Tibia Compression"
        nrows = 2
        ncols = 2
        sharey = True

        def __init__(self, report: Report) -> None:
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_passenger}TIBILEUP??FOZB"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}TIBIRIUP??FOZB"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}TIBILELO??FOZB"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}TIBIRILO??FOZB"]] for isomme in self.report.isomme_list}

    class Page_Passenger_Tibia_Index(Page_Plot_nxn):
        name = "Passenger Tibia Index"
        title = "Passenger Tibia Index"
        nrows = 2
        ncols = 2
        sharey = True

        def __init__(self, report: Report) -> None:
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_passenger}TIINLU00??000B"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}TIINRU00??000B"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}TIINLL00??000B"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}TIINRL00??000B"]] for isomme in self.report.isomme_list}

    class Page_OLC_Trolley(Page_Plot_nxn):
        name: str = "OLC Trolley"
        title: str = "Occupant Load Criterion (OLC) of Trolley"
        channels: dict
        nrows: int = 1
        ncols: int = 1

        def __init__(self, report: EuroNCAP_Frontal_MPDB) -> None:
            super().__init__(report)
            self.channels = {}
            for isomme in self.report.isomme_list:
                channel = isomme.get_channel("M?MBAR0000??VEXA", "M?MBARCG00??VEXA")
                if channel is None:
                    logger.info(f"No trolley velocity channel in {isomme}. OLC trolley plot left empty.")
                    self.channels[isomme] = [[]]
                    continue
                self.channels[isomme] = [[channel, calculate_olc(channel)[1]]]
