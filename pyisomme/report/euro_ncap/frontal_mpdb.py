from pyisomme.report.page import Page_Cover, Page_OLC, Page_Plot_nxn, Page_Criterion_Values_Table, Page_Criterion_Rating_Table, Page_Criterion_Values_Chart
from pyisomme.report.report import Report
from pyisomme.limits import Limit
from pyisomme.calculate import calculate_olc
from pyisomme.report.euro_ncap.frontal_50kmh import EuroNCAP_Frontal_50kmh
from pyisomme.report.criterion import Criterion
from pyisomme.report.euro_ncap.limits import Limit_G, Limit_P, Limit_C, Limit_M, Limit_A, Limit_W
from pyisomme.unit import g0

import logging
import numpy as np


logger = logging.getLogger(__name__)


class EuroNCAP_Frontal_MPDB(Report):
    name = "Euro NCAP | Frontal-Impact against MPDB with 50 % Overlap at 50/50 km/h"
    protocol = "9.3"
    protocols = {
        "9.3": "Version 9.3 (05.12.2023) [references/Euro-NCAP/euro-ncap-assessment-protocol-aop-v93.pdf]"
    }

    def __init__(self, *args, **kwargs):
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

    class Criterion_Overall(Criterion):
        name: str = "Overall"
        p_driver: int = 1
        p_passenger: int = 3

        def __init__(self, report, isomme):
            super().__init__(report, isomme)

            p_driver = isomme.get_test_info("Driver position object 1")
            if p_driver is not None:
                self.p_driver = int(p_driver)
            self.p_passenger = 1 if self.p_driver != 1 else self.p_passenger

            self.criterion_driver = self.Criterion_Driver(report, isomme, p=self.p_driver)
            self.criterion_passenger = self.Criterion_Passenger(report, isomme, p=self.p_passenger)

            self.criterion_door_opening_during_impact = EuroNCAP_Frontal_50kmh.Criterion_Overall.Criterion_DoorOpeningDuringImpact(report, isomme)
            self.criterion_compatibility_modifier = self.Criterion_Compatibility_Modifier(report, isomme)

        def calculation(self):
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

            # Modifier
            self.criterion_door_opening_during_impact.calculate()
            self.criterion_compatibility_modifier.calculate()

            self.rating += np.sum([
                self.criterion_door_opening_during_impact.rating,
                self.criterion_compatibility_modifier.rating
            ])

            # Capping (-np.inf) leads to 0 points. More than 16 points should not be possible if sub-criteria defined correctly
            self.rating = np.interp(self.rating, [0, 16], [0, 16], left=0, right=np.nan)

        class Criterion_Driver(Criterion):
            name = "Driver"

            def __init__(self, report, isomme, p):
                super().__init__(report, isomme)

                self.p = p

                self.criterion_head_neck = self.Criterion_Head_Neck(report, isomme, p=self.p)
                self.criterion_chest_abdomen = self.Criterion_Chest_Abdomen(report, isomme, p=self.p)
                self.criterion_knee_femur_pelvis = self.Criterion_Knee_Femur_Pelvis(report, isomme, p=self.p)
                self.criterion_lowerleg_foot_ankle = self.Criterion_LowerLeg_Foot_Ankle(report, isomme, p=self.p)

            def calculation(self):
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

                steering_wheel_airbag_exists: bool = True

                def __init__(self, report, isomme, p: int):
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_head = self.Criterion_Head(report, isomme, p=self.p)
                    self.criterion_neck = self.Criterion_Neck(report, isomme, p=self.p)

                def calculation(self):
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
                    hard_contact: bool = True

                    def __init__(self, report, isomme, p: int):
                        super().__init__(report, isomme)

                        self.p = p

                        self.criterion_hic_15 = EuroNCAP_Frontal_50kmh.Criterion_Overall.Criterion_Driver.Criterion_Head.Criterion_HIC_15(report, isomme, p=self.p)
                        self.criterion_head_a3ms = EuroNCAP_Frontal_50kmh.Criterion_Overall.Criterion_Driver.Criterion_Head.Criterion_Head_a3ms(report, isomme, p=self.p)
                        self.criterion_damage = self.Criterion_DAMAGE(self.report, self.isomme, p=self.p)

                    def calculation(self):
                        if np.max(np.abs(self.isomme.get_channel(f"?{self.p}HEAD??00??ACRA").get_data(unit=g0))):
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
                        self.rating += self.criterion_damage.rating

                    class Criterion_DAMAGE(Criterion):
                        name = "Modifier for Brain Injury - DAMAGE"

                        def __init__(self, report, isomme, p: int):
                            super().__init__(report, isomme)

                            self.p = p

                            self.extend_limit_list([
                                Limit([f"?{self.p}HEADDAMA??AAR?"], func=lambda x: 0.42, y_unit="rad/s^2", rating=0.0, color="green", name="0 pt. Modifier", upper=True),
                                Limit([f"?{self.p}HEADDAMA??AAR?"], func=lambda x: 0.42, y_unit="rad/s^2", rating=-1., color="orange", name="-1 pt. Modifier", lower=True),
                                Limit([f"?{self.p}HEADDAMA??AAR?"], func=lambda x: 0.47, y_unit="rad/s^2", rating=-2., color="red", name="-2 pt. Modifier", lower=True),
                            ])

                        def calculation(self) -> None:
                            self.channel = self.isomme.get_channel(f"?{self.p}HEADDAMA??AARA")
                            self.value = np.max(self.channel.get_data())
                            self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                            self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_Neck(Criterion):
                    name = "Neck"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.criterion_my_extension = self.Criterion_My_Extension(report, isomme, p)
                        self.criterion_fz_tension = self.Criterion_Fz_Tension(report, isomme, p)
                        self.criterion_fx_shear = self.Criterion_Fx_Shear(report, isomme, p)

                    def calculation(self):
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

                        def __init__(self, report, isomme, p):
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

                        def calculation(self):
                            self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??MOYB")
                            self.value = np.min(self.channel.get_data(unit="Nm"))
                            self.rating = self.limits.get_limit_min_rating(self.channel)
                            self.color = self.limits.get_limit_min_color(self.channel)

                    class Criterion_Fz_Tension(Criterion):
                        name = "Neck Fz tension"

                        def __init__(self, report, isomme, p):
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

                        def calculation(self):
                            self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??FOZA").convert_unit("kN")
                            self.value = np.max(self.channel.get_data())
                            self.rating = self.limits.get_limit_min_rating(self.channel)
                            self.color = self.limits.get_limit_min_color(self.channel)

                    class Criterion_Fx_Shear(Criterion):
                        name = "Neck Fx shear"

                        def __init__(self, report, isomme, p):
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

                        def calculation(self):
                            self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??FOXA").convert_unit("kN")
                            self.value = self.channel.get_data()[np.argmax(np.abs(self.channel.get_data()))]
                            self.rating = self.limits.get_limit_min_rating(self.channel)
                            self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Chest_Abdomen(Criterion):
                name = "Chest and Abdomen"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_chest = self.Criterion_Chest(report, isomme, p)
                    self.criterion_abdomen = self.Criterion_Abdomen(report, isomme, p)

                def calculation(self):
                    self.criterion_chest.calculate()
                    self.criterion_abdomen.calculate()

                    self.rating = np.min([
                        self.criterion_chest.rating,
                        self.criterion_abdomen.rating
                    ])


                class Criterion_Chest(Criterion):
                    name = "Chest"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.criterion_chest_compression = self.Criterion_Chest_Compression(report, isomme, p=self.p)

                        self.criterion_shoulder_belt_load = EuroNCAP_Frontal_50kmh.Criterion_Overall.Criterion_Driver.Criterion_Chest.Criterion_ShoulderBeltLoad(report, isomme, p=self.p)

                    def calculation(self):
                        self.criterion_chest_compression.calculate()

                        self.rating = self.criterion_chest_compression.rating

                        # Modifier
                        self.criterion_shoulder_belt_load.calculate()
                        self.rating += self.criterion_shoulder_belt_load.rating

                    class Criterion_Chest_Compression(Criterion):
                        name = "Chest Compression"

                        def __init__(self, report, isomme, p):
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

                        def calculation(self):
                            self.channel = self.isomme.get_channel(f"?{self.p}CHST0000??DSXC").convert_unit("mm")
                            self.value = np.min(self.channel.get_data())
                            self.rating = self.limits.get_limit_min_rating(self.channel)
                            self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_Abdomen(Criterion):
                    name = "Abdomen"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.criterion_abdomen_compression = self.Criterion_Abdomen_Compression(report, isomme, p=self.p)

                    def calculation(self):
                        self.criterion_abdomen_compression.calculate()

                        self.rating = self.criterion_abdomen_compression.rating

                    class Criterion_Abdomen_Compression(Criterion):
                        name = "Abdomen Compression"

                        def __init__(self, report, isomme, p):
                            super().__init__(report, isomme)

                            self.p = p

                            self.extend_limit_list([
                                Limit_P([f"?{self.p}ABDO??????DSX?"], func=lambda x: -88, y_unit="mm", upper=True),
                                Limit_G([f"?{self.p}ABDO??????DSX?"], func=lambda x: -88, y_unit="mm", lower=True),
                            ])

                        def calculation(self):
                            self.channel = self.isomme.get_channel(f"?{self.p}ABDO0000??DSXC").convert_unit("mm")
                            self.value = np.min(self.channel.get_data())
                            self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                            self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Knee_Femur_Pelvis(Criterion):
                name = "Knee, Femur and Pelvis"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_pelvis = self.Criterion_Pelvis(report, isomme, p=self.p)
                    self.criterion_femur = self.Criterion_Femur(report, isomme, p=self.p)
                    self.criterion_knee = self.Criterion_Knee(report, isomme, p=self.p)

                    self.criterion_submarining = EuroNCAP_Frontal_50kmh.Criterion_Overall.Criterion_Driver.Criterion_Femur.Criterion_Submarining(report, isomme, p=self.p)

                def calculation(self):
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

                    self.rating += self.criterion_submarining.rating

                class Criterion_Pelvis(Criterion):
                    name = "Pelvis"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.criterion_acetabulum_force = self.Criterion_Acetabulum_Force(report, isomme, p=self.p)

                    def calculation(self):
                        self.criterion_acetabulum_force.calculate()

                        self.rating = self.criterion_acetabulum_force.rating

                    class Criterion_Acetabulum_Force(Criterion):
                        name = "Acetabulum Force"

                        def __init__(self, report, isomme, p):
                            super().__init__(report, isomme)

                            self.p = p

                            self.extend_limit_list([
                                Limit_P([f"?{self.p}ACTB??00??FOR?"], func=lambda x: -4.100, y_unit="kN", upper=True),
                                Limit_W([f"?{self.p}ACTB??00??FOR?"], func=lambda x: -3.827, y_unit="kN", upper=True),
                                Limit_M([f"?{self.p}ACTB??00??FOR?"], func=lambda x: -3.553, y_unit="kN", upper=True),
                                Limit_A([f"?{self.p}ACTB??00??FOR?"], func=lambda x: -3.280, y_unit="kN", upper=True),
                                Limit_G([f"?{self.p}ACTB??00??FOR?"], func=lambda x: -3.280, y_unit="kN", lower=True),
                            ])

                        def calculation(self):
                            self.channel = self.isomme.get_channel(f"?{self.p}ACTB0000??FORB").convert_unit("kN")
                            self.value = np.min(self.channel.get_data())
                            self.rating = self.limits.get_limit_min_rating(self.channel)
                            self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_Femur(Criterion):
                    name = "Femur"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.criterion_femur_compression = self.Criterion_Femur_Compression(report, isomme, p=self.p)

                    def calculation(self):
                        self.criterion_femur_compression.calculate()

                        self.rating = self.criterion_femur_compression.rating

                    class Criterion_Femur_Compression(Criterion):
                        name = "Femur Compression"

                        def __init__(self, report, isomme, p):
                            super().__init__(report, isomme)

                            self.p = p

                            self.extend_limit_list([
                                Limit_G([f"?{self.p}FEMR??00??FOZ?"], func=lambda x: -3.8000, y_unit="kN", x_unit="ms", lower=True),
                                Limit_A([f"?{self.p}FEMR??00??FOZ?"], func=lambda x: -3.8000, y_unit="kN", x_unit="ms", upper=True),
                                Limit_M([f"?{self.p}FEMR??00??FOZ?"], func=lambda x: np.interp(x, [0, 10], [-5.557, -5.053]), y_unit="kN", x_unit="ms", upper=True),
                                Limit_W([f"?{self.p}FEMR??00??FOZ?"], func=lambda x: np.interp(x, [0, 10], [-7.313, -6.307]), y_unit="kN", x_unit="ms", upper=True),
                                Limit_P([f"?{self.p}FEMR??00??FOZ?"], func=lambda x: np.interp(x, [0, 10], [-9.070, -7.560]), y_unit="kN", x_unit="ms", upper=True),
                            ])

                        def calculation(self):
                            self.channel = self.isomme.get_channel(f"?{self.p}FEMR0000??FOZB").convert_unit("kN")
                            self.value = self.limits.get_limit_min_y(self.channel)
                            self.rating = self.limits.get_limit_min_rating(self.channel)
                            self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_Knee(Criterion):
                    name = "Knee"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.criterion_knee_slider_compression = self.Criterion_Knee_Slider_Compression(report, isomme, p=self.p)

                    def calculation(self):
                        self.criterion_knee_slider_compression.calculate()

                        self.rating = self.criterion_knee_slider_compression.rating

                    class Criterion_Knee_Slider_Compression(Criterion):
                        name = "Knee Slider Compression"

                        def __init__(self, report, isomme, p):
                            super().__init__(report, isomme)

                            self.p = p

                            self.extend_limit_list([
                                Limit_P([f"?{self.p}KNSL??00??DSX?"], func=lambda x: -15.0, y_unit="mm", upper=True),
                                Limit_W([f"?{self.p}KNSL??00??DSX?"], func=lambda x: -12.0, y_unit="mm", upper=True),
                                Limit_M([f"?{self.p}KNSL??00??DSX?"], func=lambda x: -9.00, y_unit="mm", upper=True),
                                Limit_A([f"?{self.p}KNSL??00??DSX?"], func=lambda x: -6.00, y_unit="mm", upper=True),
                                Limit_G([f"?{self.p}KNSL??00??DSX?"], func=lambda x: -6.00, y_unit="mm", lower=True),
                            ])

                        def calculation(self):
                            self.channel = self.isomme.get_channel(f"?{self.p}KNSL0000??DSXC").convert_unit("mm")
                            self.value = np.min(self.channel.get_data())
                            self.rating = self.limits.get_limit_min_rating(self.channel)
                            self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_LowerLeg_Foot_Ankle(Criterion):
                name = "Lower Leg, Foot and Ankle"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_tibia_index = self.Criterion_Tibia_Index(report, isomme, p=self.p)
                    self.criterion_tibia_compression = self.Criterion_Tibia_Compression(report, isomme, p=self.p)
                    self.criterion_pedal_rearward_displacement = self.Criterion_Pedal_Rearward_Displacement(report, isomme, p=self.p)

                def calculation(self):
                    self.criterion_tibia_index.calculate()
                    self.criterion_tibia_compression.calculate()
                    self.criterion_pedal_rearward_displacement.calculate()

                    self.rating = np.min([
                        self.criterion_tibia_index.rating,
                        self.criterion_tibia_compression.rating,
                        self.criterion_pedal_rearward_displacement.rating,
                    ])

                class Criterion_Tibia_Index(Criterion):
                    name = "Tibia Index"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_G([f"?{self.p}TIIN??????000?"], func=lambda x: 0.4, y_unit="1", upper=True),
                            Limit_A([f"?{self.p}TIIN??????000?"], func=lambda x: 0.4, y_unit="1", lower=True),
                            Limit_M([f"?{self.p}TIIN??????000?"], func=lambda x: 0.7, y_unit="1", lower=True),
                            Limit_W([f"?{self.p}TIIN??????000?"], func=lambda x: 1.0, y_unit="1", lower=True),
                            Limit_P([f"?{self.p}TIIN??????000?"], func=lambda x: 1.3, y_unit="1", lower=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}TIIN0000??000B")
                        self.value = np.max(self.channel.get_data())
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_Tibia_Compression(Criterion):
                    name = "Tibia Compression"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_P([f"?{self.p}TIBI??????FOZ?"], func=lambda x: -8, y_unit="kN", upper=True),
                            Limit_W([f"?{self.p}TIBI??????FOZ?"], func=lambda x: -6, y_unit="kN", upper=True),
                            Limit_M([f"?{self.p}TIBI??????FOZ?"], func=lambda x: -4, y_unit="kN", upper=True),
                            Limit_A([f"?{self.p}TIBI??????FOZ?"], func=lambda x: -2, y_unit="kN", upper=True),
                            Limit_G([f"?{self.p}TIBI??????FOZ?"], func=lambda x: -2, y_unit="kN", lower=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}TIBI0000??FOZB").convert_unit("kN")
                        self.value = np.min(self.channel.get_data())
                        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=True)
                        self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_Pedal_Rearward_Displacement(Criterion):
                    name = "Pedal Rearward Displacement"
                    pedal_rearward_displacement: float = 0

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                    def calculation(self):
                        self.value = self.pedal_rearward_displacement
                        self.rating = np.interp(self.value, [100, 200], [4, 0], left=4)

        class Criterion_Passenger(Criterion):
            name = "Passenger"

            def __init__(self, report, isomme, p):
                super().__init__(report, isomme)

                self.p = p

                self.criterion_head_neck = self.Criterion_Head_Neck(report, isomme, p)
                self.criterion_chest = self.Criterion_Chest(report, isomme, p)
                self.criterion_knee_femur_pelvis = self.Criterion_Knee_Femur_Pelvis(report, isomme, p)
                self.criterion_lowerleg = self.Criterion_LowerLeg(report, isomme, p)

            def calculation(self):
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

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_head = self.Criterion_Head(report, isomme, p)
                    self.criterion_neck = self.Criterion_Neck(report, isomme, p)

                def calculation(self):
                    self.criterion_head.calculate()
                    self.criterion_neck.calculate()

                    self.rating = self.value = np.min([
                        self.criterion_head.rating,
                        self.criterion_neck.rating,
                    ])

                class Criterion_Head(Criterion):
                    name = "Head"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.criterion_hic_15 = EuroNCAP_Frontal_50kmh.Criterion_Overall.Criterion_Driver.Criterion_Head.Criterion_HIC_15(report, isomme, p=self.p)
                        self.criterion_head_a3ms = EuroNCAP_Frontal_50kmh.Criterion_Overall.Criterion_Driver.Criterion_Head.Criterion_Head_a3ms(report, isomme, p=self.p)

                    def calculation(self):
                        self.criterion_hic_15.calculate()
                        self.criterion_head_a3ms.calculate()

                        self.rating = np.value = np.min([
                            self.criterion_hic_15.rating,
                            self.criterion_head_a3ms.rating,
                        ])

                class Criterion_Neck(Criterion):
                    name = "Neck"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.criterion_fx_shear = self.Criterion_Fx_Shear(report, isomme, p)
                        self.criterion_fz_tension = self.Criterion_Fz_Tension(report, isomme, p)
                        self.criterion_my_extension = self.Criterion_My_Extension(report, isomme, p)

                    def calculation(self):
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

                        def __init__(self, report, isomme, p):
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

                        def calculation(self):
                            self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??FOXA").convert_unit("kN")
                            self.value = self.limits.get_limit_min_y(self.channel)
                            self.rating = self.limits.get_limit_min_rating(self.channel)
                            self.color = self.limits.get_limit_min_color(self.channel)

                    class Criterion_Fz_Tension(Criterion):
                        name = "Fz Tension"

                        def __init__(self, report, isomme, p):
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
                            self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??FOZA").convert_unit("kN")
                            self.value = self.limits.get_limit_min_y(self.channel)
                            self.rating = self.limits.get_limit_min_rating(self.channel)
                            self.color = self.limits.get_limit_min_color(self.channel)

                    class Criterion_My_Extension(Criterion):
                        name = "My Extension"

                        def __init__(self, report, isomme, p):
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
                            self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??MOYB").convert_unit("Nm")
                            self.value = np.min(self.channel.get_data())
                            self.rating = self.limits.get_limit_min_rating(self.channel)
                            self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Chest(Criterion):
                name = "Chest"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_chest_compression = self.Criterion_Chest_Compression(report, isomme, p)
                    self.criterion_chest_vc = EuroNCAP_Frontal_50kmh.Criterion_Overall.Criterion_Driver.Criterion_Chest.Criterion_Chest_VC(report, isomme, p)

                    self.criterion_shoulder_belt_load = EuroNCAP_Frontal_50kmh.Criterion_Overall.Criterion_Driver.Criterion_Chest.Criterion_ShoulderBeltLoad(report, isomme, p=self.p)

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

                    def __init__(self, report, isomme, p):
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

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}CHST0003??DSXC", f"?{self.p}CHST0000??DSXC").convert_unit("mm")
                        self.value = np.min(self.channel.get_data())
                        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=True)
                        self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Knee_Femur_Pelvis(Criterion):
                name = "Knee, Femur and Pelvis"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_femur_compression = self.report.Criterion_Overall.Criterion_Driver.Criterion_Knee_Femur_Pelvis.Criterion_Femur.Criterion_Femur_Compression(report, isomme, p)
                    self.criterion_knee_slider_compression = self.report.Criterion_Overall.Criterion_Driver.Criterion_Knee_Femur_Pelvis.Criterion_Knee.Criterion_Knee_Slider_Compression(report, isomme, p)

                def calculation(self):
                    self.criterion_femur_compression.calculate()
                    self.criterion_knee_slider_compression.calculate()

                    self.rating = self.value = np.min([
                        self.criterion_femur_compression.rating,
                        self.criterion_knee_slider_compression.rating,
                    ])

            class Criterion_LowerLeg(Criterion):
                name = "Lower Leg"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_tibia_index = self.report.Criterion_Overall.Criterion_Driver.Criterion_LowerLeg_Foot_Ankle.Criterion_Tibia_Index(report, isomme, p=self.p)
                    self.criterion_tibia_compression = self.report.Criterion_Overall.Criterion_Driver.Criterion_LowerLeg_Foot_Ankle.Criterion_Tibia_Compression(report, isomme, p=self.p)

                def calculation(self):
                    self.criterion_tibia_index.calculate()
                    self.criterion_tibia_compression.calculate()

                    self.rating = np.min([
                        self.criterion_tibia_index.rating,
                        self.criterion_tibia_compression.rating,
                    ])

        class Criterion_Compatibility_Modifier(Criterion):
            name = "Compatibility Modifier"

            def __init__(self, report, isomme):
                super().__init__(report, isomme)

                self.criterion_olc_modifier = self.Criterion_OLC_Modifier(report, isomme)
                # self.criterion_sd_modifier = self.Criterion_SD_Modifier(report, isomme)
                # self.criterion_bo_modifier = self.Criterion_BO_Modifier(report, isomme)

            def calculation(self):
                self.criterion_olc_modifier.calculate()
                # self.criterion_sd_modifier.calculate()
                # self.criterion_bo_modifier.calculate()

                self.value = np.sum([
                    self.criterion_olc_modifier.rating,
                    # self.criterion_sd_modifier.rating,
                    # self.criterion_bo_modifier.rating
                ])
                self.rating = np.interp(self.value, [-8, 0], [-8, 0])  # penalty will not exceed -8 pts.

            class Criterion_OLC_Modifier(Criterion):
                name = "Occupant Load Criterion (OLC) Modifier"

                def __init__(self, report, isomme):
                    super().__init__(report, isomme)

                    self.extend_limit_list([
                        Limit([f"M?MBAR0OLC??VEX?"], func=lambda x: 25, y_unit=g0, name="0 pt. Modifier", rating=0, upper=True),
                        Limit([f"M?MBAR0OLC??VEX?"], func=lambda x: 25, y_unit=g0, name="-2..0 pt. Modifier", rating=0, lower=True),
                        Limit([f"M?MBAR0OLC??VEX?"], func=lambda x: 40, y_unit=g0, name="-2 pt. Modifier", rating=-2, lower=True),
                    ])

                def calculation(self):
                    self.channel = calculate_olc(self.isomme.get_channel(f"M?MBAR0000??VEXA", f"M?MBARCG00??VEXA"))[0]
                    self.value = self.channel.get_data(unit=g0)[0]
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=True)

            class Criterion_SD_Modifier(Criterion):
                pass

            class Criterion_BO_Modifier(Criterion):
                pass

    class Page_Rating_Table(Page_Criterion_Rating_Table):
        name = "Rating"
        title = "Rating"

        def __init__(self, report):
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_driver,
                self.report.criterion_overall[isomme].criterion_passenger,
                self.report.criterion_overall[isomme].criterion_compatibility_modifier,
                self.report.criterion_overall[isomme].criterion_door_opening_during_impact,
                self.report.criterion_overall[isomme],
            ] for isomme in self.report.isomme_list}


    class Page_Driver_Result_Values_Chart(Page_Criterion_Values_Chart):
        name = "Driver Result Values Chart"
        title = "Driver Result"

        def __init__(self, report):
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
        name = "Driver Rating Table"
        title = "Driver Rating"

        def __init__(self, report):
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_neck,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest_abdomen,
                self.report.criterion_overall[isomme].criterion_driver.criterion_knee_femur_pelvis.criterion_knee,
                self.report.criterion_overall[isomme].criterion_driver.criterion_lowerleg_foot_ankle,
                self.report.criterion_overall[isomme].criterion_driver,
            ] for isomme in self.report.isomme_list}

    class Page_Driver_Values_Table(Page_Criterion_Values_Table):
        name = "Driver Values Table"
        title = "Driver Values"

        def __init__(self, report):
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
        name = "Driver Head DAMAGE"
        title = "Driver Head DAMAGE"
        nrows = 2
        ncols = 2
        sharey = True

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_driver}HEADDAMA??AAXA"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}HEADDAMA??AAYA"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}HEADDAMA??AAZA"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}HEADDAMA??AARA"]] for isomme in self.report.isomme_list}

    class Page_Driver_Neck_Load(EuroNCAP_Frontal_50kmh.Page_Driver_Neck_Load):
        pass

    class Page_Driver_Chest_Compression(Page_Plot_nxn):
        name = "Driver Chest Compression"
        title = "Driver Chest Compression"
        nrows = 2
        ncols = 2
        sharey = True

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_driver}CHSTLEUP??DSXC"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}CHSTRIUP??DSXC"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}CHSTLELO??DSXC"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}CHSTRILO??DSXC"]] for isomme in self.report.isomme_list}

    class Page_Driver_Abdomen_Compression(Page_Plot_nxn):
        name = "Driver Abdomen Compression"
        title = "Driver Abdomen Compression"
        nrows = 1
        ncols = 2

        def __init__(self, report):
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

        def __init__(self, report):
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

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_driver}TIINLEUP??000B"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}TIINRIUP??000B"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}TIINLELO??000B"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}TIINRILO??000B"]] for isomme in self.report.isomme_list}

    class Page_Driver_Knee_Slider_Compression(Page_Plot_nxn):
        name = "Driver Knee Slider Compression"
        title = "Driver Knee Slider Compression"
        nrows = 1
        ncols = 2
        sharey = True

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_driver}KNSLLE00??DSXC"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}KNSLRI00??DSXC"]]for isomme in self.report.isomme_list}

    class Page_Passenger_Result_Values_Chart(Page_Criterion_Values_Chart):
        name = "Passenger Result Values Chart"
        title = "Passenger Result"

        def __init__(self, report):
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
        name: str = "Passenger Rating Table"
        title: str = "Passenger Rating"
        table_content: dict

        def __init__(self, report):
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_passenger.criterion_head_neck,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_chest,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_knee_femur_pelvis,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_lowerleg,
                self.report.criterion_overall[isomme].criterion_passenger,
            ] for isomme in self.report.isomme_list}

    class Page_Passenger_Values_Table(Page_Criterion_Values_Table):
        name: str = "Passenger Values Table"
        title: str = "Passenger Values"

        def __init__(self, report):
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
        name: str = "Passenger Belt"
        title: str = "Passenger Belt"
        nrows: int = 3
        ncols: int = 2
        sharey: bool = False

        def __init__(self, report):
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

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_passenger}HEAD??????AC{xyzr}A"] for xyzr in "XYZR"] for isomme in self.report.isomme_list}

    class Page_Passenger_Neck_Load(Page_Plot_nxn):
        name: str = "Passenger Neck Load"
        title: str = "Passenger Neck Load"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = False

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_passenger}NECKUP00??MOYB"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}NECKUP00??FOZA"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}NECKUP00??FOXA"]] for isomme in self.report.isomme_list}

    class Page_Passenger_Chest_Deflection(Page_Plot_nxn):
        name: str = "Passenger Chest Deflection"
        title: str = "Passenger Chest Deflection"
        nrows: int = 1
        ncols: int = 2

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_passenger}CHST000???DSXC"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}VCCR000???VEXC"]] for isomme in self.report.isomme_list}

    class Page_Passenger_Femur_Axial_Force(Page_Plot_nxn):
        name: str = "Passenger Femur Axial Force"
        title: str = "Passenger Femur Axial Force"
        nrows: int = 1
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_passenger}FEMRLE00??FOZB"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}FEMRRI00??FOZB"]] for isomme in self.report.isomme_list}

    class Page_Passenger_Knee_Slider_Compression(Page_Plot_nxn):
        name = "Passenger Knee Slider Compression"
        title = "Passenger Knee Slider Compression"
        nrows = 1
        ncols = 2
        sharey = True

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_passenger}KNSLLE00??DSXC"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}KNSLRI00??DSXC"]]for isomme in self.report.isomme_list}

    class Page_Passenger_Tibia_Compression(Page_Plot_nxn):
        name = "Passenger Tibia Compression"
        title = "Passenger Tibia Compression"
        nrows = 2
        ncols = 2
        sharey = True

        def __init__(self, report):
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

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_passenger}TIINLEUP??000B"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}TIINRIUP??000B"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}TIINLELO??000B"],
                                      [f"?{self.report.criterion_overall[isomme].p_passenger}TIINRILO??000B"]] for isomme in self.report.isomme_list}

    class Page_OLC_Trolley(Page_Plot_nxn):
        name: str = "OLC Trolley"
        title: str = "Occupant Load Criterion (OLC) of Trolley"
        channels: dict
        nrows: int = 1
        ncols: int = 1

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[isomme.get_channel(f"M?MBAR0000??VEXA", f"M?MBARCG00??VEXA"),
                                       calculate_olc(isomme.get_channel(f"M?MBAR0000??VEXA", f"M?MBARCG00??VEXA"))[1]]] for isomme in self.report.isomme_list}
