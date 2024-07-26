from pyisomme.unit import Unit, g0
from pyisomme.limits import Limit
from pyisomme.report.page import Page_Cover, Page_OLC, Page_Criterion_Rating_Table, Page_Plot_nxn, Page_Criterion_Values_Chart, Page_Criterion_Values_Table
from pyisomme.report.report import Report
from pyisomme.report.criterion import Criterion
from pyisomme.report.euro_ncap.limits import Limit_G, Limit_P, Limit_C, Limit_M, Limit_A, Limit_W

import logging
import numpy as np


logger = logging.getLogger(__name__)


class EuroNCAP_Frontal_50kmh(Report):
    name = "Euro NCAP | Frontal-Impact against Rigid Wall with 100 % Overlap at 50 km/h"
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
            self.Page_Driver_Neck_Load(self),
            self.Page_Driver_Neck_NIJ(self),
            self.Page_Driver_Chest_Deflection(self),
            self.Page_Driver_Femur_Axial_Force(self),

            self.Page_Front_Passenger_Result_Values_Chart(self),
            self.Page_Front_Passenger_Rating_Table(self),
            self.Page_Front_Passenger_Values_Table(self),
            self.Page_Front_Passenger_Belt(self),
            self.Page_Front_Passenger_Head_Acceleration(self),
            self.Page_Front_Passenger_Neck_Load(self),
            self.Page_Front_Passenger_Neck_NIJ(self),
            self.Page_Front_Passenger_Chest_Deflection(self),
            self.Page_Front_Passenger_Femur_Axial_Force(self),

            self.Page_Rear_Passenger_Result_Values_Chart(self),
            self.Page_Rear_Passenger_Rating_Table(self),
            self.Page_Rear_Passenger_Values_Table(self),
            self.Page_Rear_Passenger_Belt(self),
            self.Page_Rear_Passenger_Head_Acceleration(self),
            self.Page_Rear_Passenger_Neck_Load(self),
            self.Page_Rear_Passenger_Chest_Deflection(self),
            self.Page_Rear_Passenger_Femur_Axial_Force(self),

            Page_OLC(self),
        ]

    class Criterion_Overall(Criterion):
        name = "Overall"
        p_driver: int = 1
        p_front_passenger: int = 3
        p_rear_passenger: int = 6

        def __init__(self, report, isomme):
            super().__init__(report, isomme)

            p_driver = isomme.get_test_info("Driver position object 1")
            if p_driver is not None:
                self.p_driver = int(p_driver)
            self.p_front_passenger = 1 if self.p_driver != 1 else self.p_front_passenger
            self.p_rear_passenger = 4 if self.p_driver != 1 else self.p_rear_passenger

            self.criterion_driver = self.Criterion_Driver(report, isomme, p=self.p_driver)
            self.criterion_front_passenger = self.Criterion_Front_Passenger(report, isomme, p=self.p_front_passenger)
            self.criterion_rear_passenger = self.Criterion_Rear_Passenger(report, isomme, p=self.p_rear_passenger)
            self.criterion_door_opening_during_impact = self.Criterion_DoorOpeningDuringImpact(report, isomme)

        def calculation(self):
            logger.info("Calculate Driver")
            self.criterion_driver.calculate()
            logger.info("Calculate Front Passenger")
            self.criterion_front_passenger.calculate()
            logger.info("Calculate Rear Passenger")
            self.criterion_rear_passenger.calculate()

            self.rating = np.nanmean([
                self.criterion_driver.rating,
                self.criterion_front_passenger.rating,
                self.criterion_rear_passenger.rating,
            ]) / 2
            # Capping (-np.inf) leads to 0 points. More than 8 points should not be possible if sub-criteria defined correctly
            self.rating = np.interp(self.rating, [0, 8], [0, 8], left=0, right=np.nan)

            # Modifier
            self.criterion_door_opening_during_impact.calculate()
            self.rating += self.criterion_door_opening_during_impact.rating

        class Criterion_Driver(Criterion):
            name = "Driver"
            steering_wheel_airbag_exists: bool = True

            def __init__(self, report, isomme, p):
                super().__init__(report, isomme)

                self.p = p

                self.criterion_head = self.Criterion_Head(report, isomme, p=self.p)
                self.criterion_neck = self.Criterion_Neck(report, isomme, p=self.p)
                self.criterion_chest = self.Criterion_Chest(report, isomme, p=self.p)
                self.criterion_femur = self.Criterion_Femur(report, isomme, p=self.p)

            def calculation(self):
                self.criterion_head.calculate()
                self.criterion_neck.calculate()
                self.criterion_chest.calculate()
                self.criterion_femur.calculate()

                self.rating = self.value = np.sum([
                    self.criterion_head.rating,
                    self.criterion_neck.rating,
                    self.criterion_chest.rating,
                    self.criterion_femur.rating,
                ])

            class Criterion_Head(Criterion):
                name = "Head"
                hard_contact: bool = True

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_hic_15 = self.Criterion_HIC_15(report, isomme, p=self.p)
                    self.criterion_head_a3ms = self.Criterion_Head_a3ms(report, isomme, p=self.p)
                    self.criterion_UnstableAirbagSteeringWheelContact = self.Criterion_UnstableAirbagSteeringWheelContact(report, isomme, p=self.p)
                    self.criterion_HazardousAirbagDeployment = self.Criterion_HazardousAirbagDeployment(report, isomme, p=self.p)
                    self.criterion_IncorrectAirbagDeployment = self.Criterion_IncorrectAirbagDeployment(report, isomme, p=self.p)
                    self.criterion_DisplacementSteeringColumn = self.Criterion_DisplacementSteeringColumn(report, isomme, p=self.p)
                    self.criterion_ExceedingForwardExcursionLine = self.Criterion_ExceedingForwardExcursionLine(report, isomme, p=self.p)

                def calculation(self):
                    if self.report.criterion_overall[self.isomme].criterion_driver.steering_wheel_airbag_exists:
                        if np.max(np.abs(self.isomme.get_channel(f"?{self.p}HEAD??00??ACRA").get_data(unit=g0))) > 80:
                            logger.info(f"Hard Head contact assumed for p={self.p} in {self.isomme}")
                            self.hard_contact = True

                        if self.hard_contact:
                            self.criterion_hic_15.calculate()
                            self.criterion_head_a3ms.calculate()
                            self.rating = np.min([self.criterion_hic_15.rating,
                                                  self.criterion_head_a3ms.rating])
                        else:
                            self.rating = 4
                    else:
                        self.rating = 0

                    # Modifiers
                    self.criterion_UnstableAirbagSteeringWheelContact.calculate()
                    self.criterion_HazardousAirbagDeployment.calculate()
                    self.criterion_IncorrectAirbagDeployment.calculate()
                    self.criterion_DisplacementSteeringColumn.calculate()
                    self.criterion_ExceedingForwardExcursionLine.calculate()

                    self.rating += np.sum([self.criterion_UnstableAirbagSteeringWheelContact.rating,
                                           self.criterion_HazardousAirbagDeployment.rating,
                                           self.criterion_IncorrectAirbagDeployment.rating,
                                           self.criterion_DisplacementSteeringColumn.rating,
                                           self.criterion_ExceedingForwardExcursionLine.rating])

                class Criterion_HIC_15(Criterion):
                    name = "HIC 15"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_G([f"?{self.p}HICR0015??00RX", f"?{self.p}HICRCG15??00RX"], func=lambda x: 500.000, y_unit=1, upper=True),
                            Limit_A([f"?{self.p}HICR0015??00RX", f"?{self.p}HICRCG15??00RX"], func=lambda x: 500.000, y_unit=1, lower=True),
                            Limit_M([f"?{self.p}HICR0015??00RX", f"?{self.p}HICRCG15??00RX"], func=lambda x: 566.667, y_unit=1, lower=True),
                            Limit_W([f"?{self.p}HICR0015??00RX", f"?{self.p}HICRCG15??00RX"], func=lambda x: 633.333, y_unit=1, lower=True),
                            Limit_P([f"?{self.p}HICR0015??00RX", f"?{self.p}HICRCG15??00RX"], func=lambda x: 700.000, y_unit=1),
                            Limit_C([f"?{self.p}HICR0015??00RX", f"?{self.p}HICRCG15??00RX"], func=lambda x: 700.000, y_unit=1, lower=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}HICR0015??00RX", f"?{self.p}HICRCG15??00RX")
                        self.value = self.channel.get_data()[0]
                        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=True)
                        self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_Head_a3ms(Criterion):
                    name = "Head a3ms"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_G([f"?{self.p}HEAD003C??ACR?", f"?{self.p}HEADCG3C??ACR?"], func=lambda x: 72.000, y_unit=Unit(g0), upper=True),
                            Limit_A([f"?{self.p}HEAD003C??ACR?", f"?{self.p}HEADCG3C??ACR?"], func=lambda x: 72.000, y_unit=Unit(g0), lower=True),
                            Limit_M([f"?{self.p}HEAD003C??ACR?", f"?{self.p}HEADCG3C??ACR?"], func=lambda x: 74.667, y_unit=Unit(g0), lower=True),
                            Limit_W([f"?{self.p}HEAD003C??ACR?", f"?{self.p}HEADCG3C??ACR?"], func=lambda x: 77.333, y_unit=Unit(g0), lower=True),
                            Limit_P([f"?{self.p}HEAD003C??ACR?", f"?{self.p}HEADCG3C??ACR?"], func=lambda x: 80.000, y_unit=Unit(g0)),
                            Limit_C([f"?{self.p}HEAD003C??ACR?", f"?{self.p}HEADCG3C??ACR?"], func=lambda x: 80.000, y_unit=Unit(g0), lower=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}HEAD003C??ACRX", f"?{self.p}HEADCG3C??ACRX")
                        self.value = self.channel.get_data(unit=g0)[0]
                        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=True)
                        self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_UnstableAirbagSteeringWheelContact(Criterion):
                    name = "Modifier for Unstable airbag/steering wheel contact"
                    unstable_airbag_steering_wheel_contact: bool = False

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)
                        self.p = p

                    def calculation(self):
                        self.value = self.unstable_airbag_steering_wheel_contact
                        self.rating = -1 if self.unstable_airbag_steering_wheel_contact else 0

                class Criterion_HazardousAirbagDeployment(Criterion):
                    name = "Modifier for Hazardous Airbag Deployment"
                    hazardous_airbag_deployment: bool = False

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)
                        self.p = p

                    def calculation(self):
                        self.value = self.hazardous_airbag_deployment
                        self.rating = -1 if self.hazardous_airbag_deployment else 0

                class Criterion_IncorrectAirbagDeployment(Criterion):
                    name = "Modifier for Incorrect Airbag Deployment"
                    incorrect_airbag_deployment: bool = False

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)
                        self.p = p

                    def calculation(self):
                        self.value = self.incorrect_airbag_deployment
                        self.rating = -1 if self.incorrect_airbag_deployment else 0

                class Criterion_DisplacementSteeringColumn(Criterion):
                    name = "Modifier for Displacement of Steering Column"
                    displacement_steering_column_rearwards: float = 0.0  # in mm
                    displacement_steering_column_upwards: float = 0.0  # in mm
                    displacement_steering_column_lateral: float = 0.0  # in mm

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)
                        self.p = p

                    def calculation(self):
                        is_driver = self.report.criterion_overall[self.isomme].p_driver == self.p

                        if is_driver:
                            rearwards_percent = self.displacement_steering_column_rearwards / 100
                            upwards_percent = self.displacement_steering_column_upwards / 80
                            lateral_percent = self.displacement_steering_column_lateral / 100

                            self.value = np.max([rearwards_percent, upwards_percent, lateral_percent])
                            self.rating = np.interp(self.value, [0.9, 1.1], [0, -1], left=0, right=-1)
                        else:
                            self.rating = 0

                class Criterion_ExceedingForwardExcursionLine(Criterion):
                    name = "Modifier for Exceeding forward excursion line"
                    forward_excursion: float = 0.0  # in mm
                    simulation_contact_seat_H3: bool = False
                    simulation_hic_15_H3: float = 0.0

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)
                        self.p = p

                    def calculation(self):
                        self.rating = 0

            class Criterion_Neck(Criterion):
                name = "Neck"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)
                    self.p = p

                    self.criterion_my_extension = self.Criterion_My_extension(report, isomme, p)
                    self.criterion_fz_tension = self.Criterion_Fz_tension(report, isomme, p)
                    self.criterion_fx_shear = self.Criterion_Fx_shear(report, isomme, p)

                def calculation(self):
                    self.criterion_my_extension.calculate()
                    self.criterion_fz_tension.calculate()
                    self.criterion_fx_shear.calculate()

                    if not self.report.criterion_overall[self.isomme].criterion_driver.steering_wheel_airbag_exists:
                        self.rating = 0
                    else:
                        self.rating = np.min([
                            self.criterion_my_extension.rating,
                            self.criterion_fz_tension.rating,
                            self.criterion_fx_shear.rating,
                        ])

                class Criterion_My_extension(Criterion):
                    name = "Neck My extension"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_G([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -36.000, y_unit="Nm", lower=True),
                            Limit_A([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -36.000, y_unit="Nm", upper=True),
                            Limit_M([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -40.333, y_unit="Nm", upper=True),
                            Limit_W([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -44.667, y_unit="Nm", upper=True),
                            Limit_P([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -49.000, y_unit="Nm", upper=True),
                            Limit_C([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -57.000, y_unit="Nm", upper=True)
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??MOYB")
                        self.value = np.min(self.channel.get_data(unit="Nm"))
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_Fz_tension(Criterion):
                    name = "Neck Fz tension"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_G([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 1.700, y_unit="kN", upper=True),
                            Limit_A([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 1.700, y_unit="kN", lower=True),
                            Limit_M([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 2.007, y_unit="kN", lower=True),
                            Limit_W([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 2.313, y_unit="kN", lower=True),
                            Limit_P([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 2.620, y_unit="kN", lower=True),
                            Limit_C([f"?{self.p}NECKUP00??FOZA"], func=lambda x: 2.900, y_unit="kN", lower=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??FOZA").convert_unit("kN")
                        self.value = np.max(self.channel.get_data())
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_Fx_shear(Criterion):
                    name = "Neck Fx shear"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_G([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.20, y_unit="kN", upper=True),
                            Limit_A([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.20, y_unit="kN", lower=True),
                            Limit_M([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.45, y_unit="kN", lower=True),
                            Limit_W([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.70, y_unit="kN", lower=True),
                            Limit_P([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.95, y_unit="kN", lower=True),

                            Limit_G([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.20, y_unit="kN", lower=True),
                            Limit_A([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.20, y_unit="kN", upper=True),
                            Limit_M([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.45, y_unit="kN", upper=True),
                            Limit_W([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.70, y_unit="kN", upper=True),
                            Limit_P([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.95, y_unit="kN", upper=True),

                            Limit_C([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 2.70, y_unit="kN", lower=True),
                            Limit_C([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -2.70, y_unit="kN", upper=True)
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??FOXA").convert_unit("kN")
                        self.value = self.channel.get_data(unit="kN")[np.argmax(np.abs(self.channel.get_data()))]
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Chest(Criterion):
                name = "Chest"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_chest_deflection = self.Criterion_Chest_Deflection(report, isomme, p)
                    self.criterion_chest_vc = self.Criterion_Chest_VC(report, isomme, p)
                    self.criterion_SteeringWheelContact = self.Criterion_SteeringWheelContact(report, isomme, p)
                    self.criterion_shoulder_belt_load = self.Criterion_ShoulderBeltLoad(report, isomme, p)

                def calculation(self):
                    self.criterion_chest_deflection.calculate()
                    self.criterion_chest_vc.calculate()

                    self.rating = np.min([self.criterion_chest_deflection.rating,
                                          self.criterion_chest_vc.rating])

                    # Modifier
                    self.criterion_SteeringWheelContact.calculate()
                    self.criterion_shoulder_belt_load.calculate()
                    self.rating += np.sum([self.criterion_SteeringWheelContact.rating,
                                           self.criterion_shoulder_belt_load.rating])

                class Criterion_Chest_Deflection(Criterion):
                    name = "Chest Deflection"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_C([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -34.000, y_unit="mm", upper=True),
                            Limit_P([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -34.000, y_unit="mm"),
                            Limit_W([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -28.667, y_unit="mm", upper=True),
                            Limit_M([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -23.333, y_unit="mm", upper=True),
                            Limit_A([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -18.000, y_unit="mm", upper=True),
                            Limit_G([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -18.000, y_unit="mm", lower=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}CHST0003??DSXC", f"?{self.p}CHST0000??DSXC").convert_unit("mm")
                        self.value = np.min(self.channel.get_data())
                        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=True)
                        self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_Chest_VC(Criterion):
                    name = "Chest VC"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_G([f"?{self.p}VCCR000[03]??VEX?"], func=lambda x: 0.500, y_unit="m/s", upper=True),
                            Limit_A([f"?{self.p}VCCR000[03]??VEX?"], func=lambda x: 0.500, y_unit="m/s", lower=True),
                            Limit_M([f"?{self.p}VCCR000[03]??VEX?"], func=lambda x: 0.667, y_unit="m/s", lower=True),
                            Limit_W([f"?{self.p}VCCR000[03]??VEX?"], func=lambda x: 0.833, y_unit="m/s", lower=True),
                            Limit_P([f"?{self.p}VCCR000[03]??VEX?"], func=lambda x: 1.000, y_unit="m/s"),
                            Limit_C([f"?{self.p}VCCR000[03]??VEX?"], func=lambda x: 1.000, y_unit="m/s", lower=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}VCCR0003??VEXC", f"?{self.p}VCCR0000??VEXC").convert_unit("m/s")
                        self.value = np.min(self.channel.get_data())
                        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=True)
                        self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_SteeringWheelContact(Criterion):
                    name = "Modifier Chest Steering Wheel Contact"
                    steering_wheel_contact: bool = False

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                    def calculation(self):
                        is_driver = self.report.criterion_overall[self.isomme].p_driver == self.p
                        self.rating = -1 if is_driver and self.steering_wheel_contact else 0

                class Criterion_ShoulderBeltLoad(Criterion):
                    name = "Modifier Shoulder Belt Load"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit([f"?{self.p}SEBE????B3FO[X0]?"], name="0 pt. Modifier", func=lambda x: 6.0, y_unit="kN", upper=True, color="green", rating=0),
                            Limit([f"?{self.p}SEBE????B3FO[X0]?"], name="-2 pt. Modifier", func=lambda x: 6.0, y_unit="kN", lower=True, color="red", rating=-2)
                        ])

                    def calculation(self) -> None:
                        self.channel = self.isomme.get_channel(f"?{self.p}SEBE????B3FO[X0]D")
                        self.value = np.max(self.channel.get_data(unit="kN"))
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Femur(Criterion):
                name = "Femur"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_femur_axial_force = self.Criterion_Femur_Axial_Force(report, isomme, p=self.p)
                    self.criterion_submarining = self.Criterion_Submarining(report, isomme, p=self.p)

                def calculation(self):
                    self.criterion_femur_axial_force.calculate()
                    self.rating = self.criterion_femur_axial_force.rating

                    # Modifier
                    self.criterion_submarining.calculate()
                    self.rating += self.criterion_submarining.rating

                class Criterion_Femur_Axial_Force(Criterion):
                    name = "Femur Axial Force"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.criterion_femur_axial_force_left = self.Criterion_Femur_Axial_Force_Left(report, isomme, p=self.p)
                        self.criterion_femur_axial_force_right = self.Criterion_Femur_Axial_Force_Right(report, isomme, p=self.p)

                    def calculation(self):
                        self.criterion_femur_axial_force_left.calculate()
                        self.criterion_femur_axial_force_right.calculate()

                        self.value = np.min([self.criterion_femur_axial_force_left.value, self.criterion_femur_axial_force_right.value])
                        self.rating = np.min([self.criterion_femur_axial_force_left.rating, self.criterion_femur_axial_force_right.rating])

                    class Criterion_Femur_Axial_Force_Left(Criterion):
                        name = "Femur Axial Force Left"

                        def __init__(self, report, isomme, p):
                            super().__init__(report, isomme)

                            self.p = p

                            self.extend_limit_list([
                                Limit_G([f"?{self.p}FEMRLE00??FOZ?"], func=lambda x: -2.6, y_unit="kN", lower=True),
                                Limit_A([f"?{self.p}FEMRLE00??FOZ?"], func=lambda x: -2.6, y_unit="kN", upper=True),
                                Limit_M([f"?{self.p}FEMRLE00??FOZ?"], func=lambda x: -3.8, y_unit="kN", upper=True),
                                Limit_W([f"?{self.p}FEMRLE00??FOZ?"], func=lambda x: -5.0, y_unit="kN", upper=True),
                                Limit_P([f"?{self.p}FEMRLE00??FOZ?"], func=lambda x: -6.2, y_unit="kN", upper=True),
                            ])

                        def calculation(self):
                            self.channel = self.isomme.get_channel(f"?{self.p}FEMRLE00??FOZB")
                            self.value = np.min(self.channel.get_data(unit="kN"))
                            self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=True)
                            self.color = self.limits.get_limit_min_color(self.channel)

                    class Criterion_Femur_Axial_Force_Right(Criterion):
                        name = "Femur Axial Force Right"

                        def __init__(self, report, isomme, p):
                            super().__init__(report, isomme)

                            self.p = p

                            self.extend_limit_list([
                                Limit_G([f"?{self.p}FEMRRI00??FOZ?"], func=lambda x: -2.6, y_unit="kN", lower=True),
                                Limit_A([f"?{self.p}FEMRRI00??FOZ?"], func=lambda x: -2.6, y_unit="kN", upper=True),
                                Limit_M([f"?{self.p}FEMRRI00??FOZ?"], func=lambda x: -3.8, y_unit="kN", upper=True),
                                Limit_W([f"?{self.p}FEMRRI00??FOZ?"], func=lambda x: -5.0, y_unit="kN", upper=True),
                                Limit_P([f"?{self.p}FEMRRI00??FOZ?"], func=lambda x: -6.2, y_unit="kN", upper=True),
                            ])

                        def calculation(self):
                            self.channel = self.isomme.get_channel(f"?{self.p}FEMRRI00??FOZB")
                            self.value = np.min(self.channel.get_data(unit="kN"))
                            self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=True)
                            self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_Submarining(Criterion):
                    name = "Submarining"
                    submarining: bool = False

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                    def calculation(self):
                        self.value = self.submarining
                        self.rating = -4 if self.submarining else 0

        class Criterion_Front_Passenger(Criterion):
            name = "Front Passenger"

            def __init__(self, report, isomme, p):
                super().__init__(report, isomme)

                self.p = p

                self.criterion_head = self.Criterion_Head(report, isomme, p=self.p)
                self.criterion_neck = self.Criterion_Neck(report, isomme, p=self.p)
                self.criterion_chest = self.Criterion_Chest(report, isomme, p=self.p)
                self.criterion_femur = self.Criterion_Femur(report, isomme, p=self.p)

            def calculation(self):
                self.criterion_head.calculate()
                self.criterion_neck.calculate()
                self.criterion_chest.calculate()
                self.criterion_femur.calculate()

                self.rating = self.value = np.sum([
                    self.criterion_head.rating,
                    self.criterion_neck.rating,
                    self.criterion_chest.rating,
                    self.criterion_femur.rating,
                ])

            class Criterion_Head(Criterion):
                name = "Head"
                hard_contact: bool = True

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_hic_15 = self.report.Criterion_Overall.Criterion_Driver.Criterion_Head.Criterion_HIC_15(report, isomme, p=self.p)
                    self.criterion_head_a3ms = self.report.Criterion_Overall.Criterion_Driver.Criterion_Head.Criterion_Head_a3ms(report, isomme, p=self.p)
                    self.criterion_HazardousAirbagDeployment = self.Criterion_HazardousAirbagDeployment(report, isomme, p=self.p)
                    self.criterion_IncorrectAirbagDeployment = self.Criterion_IncorrectAirbagDeployment(report, isomme, p=self.p)
                    self.criterion_ExceedingForwardExcursionLine = self.Criterion_ExceedingForwardExcursionLine(report, isomme, p=self.p)

                def calculation(self):
                    if np.max(np.abs(self.isomme.get_channel(f"?{self.p}HEAD??00??ACRA").get_data(unit=g0))) > 80:
                        logger.info(f"Hard Head contact assumed for p={self.p} in {self.isomme}")
                        self.hard_contact = True

                    if self.hard_contact:
                        self.criterion_hic_15.calculate()
                        self.criterion_head_a3ms.calculate()
                        self.rating = np.min([self.criterion_hic_15.rating,
                                              self.criterion_head_a3ms.rating])
                    else:
                        self.rating = 4

                    # Modifiers
                    self.criterion_HazardousAirbagDeployment.calculate()
                    self.criterion_IncorrectAirbagDeployment.calculate()
                    self.criterion_ExceedingForwardExcursionLine.calculate()

                    self.rating += np.sum([self.criterion_HazardousAirbagDeployment.rating,
                                           self.criterion_IncorrectAirbagDeployment.rating,
                                           self.criterion_ExceedingForwardExcursionLine.rating])

                class Criterion_HazardousAirbagDeployment(Criterion):
                    name = "Modifier for Hazardous Airbag Deployment"
                    hazardous_airbag_deployment: bool = False

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)
                        self.p = p

                    def calculation(self):
                        self.value = self.hazardous_airbag_deployment
                        self.rating = -1 if self.hazardous_airbag_deployment else 0

                class Criterion_IncorrectAirbagDeployment(Criterion):
                    name = "Modifier for Incorrect Airbag Deployment"
                    incorrect_airbag_deployment: bool = False

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)
                        self.p = p

                    def calculation(self):
                        self.value = self.incorrect_airbag_deployment
                        self.rating = -1 if self.incorrect_airbag_deployment else 0

                class Criterion_ExceedingForwardExcursionLine(Criterion):
                    name = "Modifier for Exceeding forward excursion line"
                    forward_excursion: float = 0.0  # in mm
                    simulation_contact_seat_H3: bool = False
                    simulation_hic_15_H3: float = 0.0

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)
                        self.p = p

                    def calculation(self):
                        self.rating = 0

            class Criterion_Neck(Criterion):
                name = "Neck"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)
                    self.p = p

                    self.criterion_my_extension = self.Criterion_My_extension(report, isomme, p)
                    self.criterion_fz_tension = self.Criterion_Fz_tension(report, isomme, p)
                    self.criterion_fx_shear = self.Criterion_Fx_shear(report, isomme, p)

                def calculation(self):
                    self.criterion_my_extension.calculate()
                    self.criterion_fz_tension.calculate()
                    self.criterion_fx_shear.calculate()

                    self.rating = np.min([
                        self.criterion_my_extension.rating,
                        self.criterion_fz_tension.rating,
                        self.criterion_fx_shear.rating,
                    ])

                class Criterion_My_extension(Criterion):
                    name = "Neck My extension"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_G([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -36.000, y_unit="Nm", lower=True),
                            Limit_A([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -36.000, y_unit="Nm", upper=True),
                            Limit_M([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -40.333, y_unit="Nm", upper=True),
                            Limit_W([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -44.667, y_unit="Nm", upper=True),
                            Limit_P([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -49.000, y_unit="Nm", upper=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??MOYB")
                        self.value = np.min(self.channel.get_data(unit="Nm"))
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_Fz_tension(Criterion):
                    name = "Neck Fz tension"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_G([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 1.700, y_unit="kN", upper=True),
                            Limit_A([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 1.700, y_unit="kN", lower=True),
                            Limit_M([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 2.007, y_unit="kN", lower=True),
                            Limit_W([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 2.313, y_unit="kN", lower=True),
                            Limit_P([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 2.620, y_unit="kN", lower=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??FOZA").convert_unit("kN")
                        self.value = np.max(self.channel.get_data())
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_Fx_shear(Criterion):
                    name = "Neck Fx shear"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_G([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.20, y_unit="kN", upper=True),
                            Limit_A([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.20, y_unit="kN", lower=True),
                            Limit_M([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.45, y_unit="kN", lower=True),
                            Limit_W([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.70, y_unit="kN", lower=True),
                            Limit_P([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.95, y_unit="kN", lower=True),

                            Limit_G([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.20, y_unit="kN", lower=True),
                            Limit_A([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.20, y_unit="kN", upper=True),
                            Limit_M([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.45, y_unit="kN", upper=True),
                            Limit_W([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.70, y_unit="kN", upper=True),
                            Limit_P([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.95, y_unit="kN", upper=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??FOXA").convert_unit("kN")
                        self.value = self.channel.get_data(unit="kN")[np.argmax(np.abs(self.channel.get_data()))]
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Chest(Criterion):
                name = "Chest"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_chest_deflection = self.report.Criterion_Overall.Criterion_Driver.Criterion_Chest.Criterion_Chest_Deflection(report, isomme, p)
                    self.criterion_chest_vc = self.report.Criterion_Overall.Criterion_Driver.Criterion_Chest.Criterion_Chest_VC(report, isomme, p)
                    self.criterion_shoulder_belt_load = self.report.Criterion_Overall.Criterion_Driver.Criterion_Chest.Criterion_ShoulderBeltLoad(report, isomme, p)

                def calculation(self):
                    self.criterion_chest_deflection.calculate()
                    self.criterion_chest_vc.calculate()

                    self.rating = np.min([self.criterion_chest_deflection.rating,
                                          self.criterion_chest_vc.rating])

                    # Modifier
                    self.criterion_shoulder_belt_load.calculate()
                    self.rating += self.criterion_shoulder_belt_load.rating

            class Criterion_Femur(Criterion):
                name = "Femur"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_femur_axial_force = self.report.Criterion_Overall.Criterion_Driver.Criterion_Femur.Criterion_Femur_Axial_Force(report, isomme, p=self.p)

                def calculation(self):
                    self.criterion_femur_axial_force.calculate()
                    self.rating = self.criterion_femur_axial_force.rating

        class Criterion_Rear_Passenger(Criterion):
            name = "Rear Passenger"

            def __init__(self, report, isomme, p):
                super().__init__(report, isomme)

                self.p = p

                self.criterion_head = self.Criterion_Head(report, isomme, p=self.p)
                self.criterion_neck = self.Criterion_Neck(report, isomme, p=self.p)
                self.criterion_chest = self.Criterion_Chest(report, isomme, p=self.p)
                self.criterion_femur = self.Criterion_Femur(report, isomme, p=self.p)

            def calculation(self):
                self.criterion_head.calculate()
                self.criterion_neck.calculate()
                self.criterion_chest.calculate()
                self.criterion_femur.calculate()

                self.rating = self.value = np.sum([
                    self.criterion_head.rating,
                    self.criterion_neck.rating,
                    self.criterion_chest.rating,
                    self.criterion_femur.rating,
                ])

            class Criterion_Head(Criterion):
                name = "Head"
                hard_contact: bool = True

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_hic_15 = self.report.Criterion_Overall.Criterion_Driver.Criterion_Head.Criterion_HIC_15(report, isomme, p=self.p)
                    self.criterion_head_a3ms = self.report.Criterion_Overall.Criterion_Driver.Criterion_Head.Criterion_Head_a3ms(report, isomme, p=self.p)
                    self.criterion_HazardousAirbagDeployment = self.Criterion_HazardousAirbagDeployment(report, isomme, p=self.p)
                    self.criterion_IncorrectAirbagDeployment = self.Criterion_IncorrectAirbagDeployment(report, isomme, p=self.p)
                    self.criterion_ExceedingForwardExcursionLine = self.Criterion_ExceedingForwardExcursionLine(report, isomme, p=self.p)

                def calculation(self):
                    if self.hard_contact:
                        self.criterion_head_a3ms.calculate()
                        self.rating = self.criterion_head_a3ms.rating
                    else:
                        self.criterion_hic_15.calculate()
                        self.criterion_head_a3ms.calculate()
                        self.rating = np.min([self.criterion_hic_15.rating,
                                              self.criterion_head_a3ms.rating])

                    # Modifiers
                    self.criterion_HazardousAirbagDeployment.calculate()
                    self.criterion_IncorrectAirbagDeployment.calculate()
                    self.criterion_ExceedingForwardExcursionLine.calculate()

                    self.rating += np.sum([self.criterion_HazardousAirbagDeployment.rating,
                                           self.criterion_IncorrectAirbagDeployment.rating,
                                           self.criterion_ExceedingForwardExcursionLine.rating])

                class Criterion_HazardousAirbagDeployment(Criterion):
                    name = "Modifier for Hazardous Airbag Deployment"
                    hazardous_airbag_deployment: bool = False

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)
                        self.p = p

                    def calculation(self):
                        self.value = self.hazardous_airbag_deployment
                        self.rating = -1 if self.hazardous_airbag_deployment else 0

                class Criterion_IncorrectAirbagDeployment(Criterion):
                    name = "Modifier for Incorrect Airbag Deployment"
                    incorrect_airbag_deployment: bool = False

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)
                        self.p = p

                    def calculation(self):
                        self.value = self.incorrect_airbag_deployment
                        self.rating = -1 if self.incorrect_airbag_deployment else 0

                class Criterion_ExceedingForwardExcursionLine(Criterion):
                    name = "Modifier for Exceeding forward excursion line"
                    forward_excursion: float = 0.0  # in mm
                    simulation_contact_seat_H3: bool = False
                    simulation_hic_15_H3: float = 0.0

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)
                        self.p = p

                    def calculation(self):
                        if self.forward_excursion < 450:
                            self.rating = 0
                        else:
                            if self.forward_excursion < 550:
                                self.rating = -2
                            else:
                                self.rating = -4

                            if self.simulation_contact_seat_H3:
                                if self.simulation_hic_15_H3 < 700:
                                    self.rating = 0
                            else:
                                self.rating = 0

            class Criterion_Neck(Criterion):
                name = "Neck"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)
                    self.p = p

                    self.criterion_my_extension = self.Criterion_My_extension(report, isomme, p)
                    self.criterion_fz_tension = self.Criterion_Fz_tension(report, isomme, p)
                    self.criterion_fx_shear = self.Criterion_Fx_shear(report, isomme, p)

                def calculation(self):
                    self.criterion_my_extension.calculate()
                    self.criterion_fz_tension.calculate()
                    self.criterion_fx_shear.calculate()

                    self.rating = np.sum([
                        self.criterion_my_extension.rating,
                        self.criterion_fz_tension.rating,
                        self.criterion_fx_shear.rating,
                    ])

                class Criterion_My_extension(Criterion):
                    name = "Neck My extension"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_G([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -36.000, y_unit="Nm", lower=True),
                            Limit_A([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -36.000, y_unit="Nm", upper=True),
                            Limit_M([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -40.333, y_unit="Nm", upper=True),
                            Limit_W([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -44.667, y_unit="Nm", upper=True),
                            Limit_P([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -49.000, y_unit="Nm", upper=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??MOYB")
                        self.value = np.min(self.channel.get_data(unit="Nm"))
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        # Reduce max. rating for rear passenger
                        self.rating = np.min([2, self.rating])

                class Criterion_Fz_tension(Criterion):
                    name = "Neck Fz tension"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_G([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 1.700, y_unit="kN", upper=True),
                            Limit_A([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 1.700, y_unit="kN", lower=True),
                            Limit_M([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 2.007, y_unit="kN", lower=True),
                            Limit_W([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 2.313, y_unit="kN", lower=True),
                            Limit_P([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 2.620, y_unit="kN", lower=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??FOZA").convert_unit("kN")
                        self.value = np.max(self.channel.get_data())
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        # Reduce max. rating for rear passenger
                        self.rating = np.min([1, self.rating])

                class Criterion_Fx_shear(Criterion):
                    name = "Neck Fx shear"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_G([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.20, y_unit="kN", upper=True),
                            Limit_A([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.20, y_unit="kN", lower=True),
                            Limit_M([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.45, y_unit="kN", lower=True),
                            Limit_W([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.70, y_unit="kN", lower=True),
                            Limit_P([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.95, y_unit="kN", lower=True),

                            Limit_G([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.20, y_unit="kN", lower=True),
                            Limit_A([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.20, y_unit="kN", upper=True),
                            Limit_M([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.45, y_unit="kN", upper=True),
                            Limit_W([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.70, y_unit="kN", upper=True),
                            Limit_P([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.95, y_unit="kN", upper=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??FOXA").convert_unit("kN")
                        self.value = self.channel.get_data(unit="kN")[np.argmax(np.abs(self.channel.get_data()))]
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        # Reduce max. rating for rear passenger
                        self.rating = np.min([1, self.rating])

            class Criterion_Chest(Criterion):
                name = "Chest"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_chest_deflection = self.report.Criterion_Overall.Criterion_Driver.Criterion_Chest.Criterion_Chest_Deflection(report, isomme, p)
                    self.criterion_chest_vc = self.report.Criterion_Overall.Criterion_Driver.Criterion_Chest.Criterion_Chest_VC(report, isomme, p)
                    self.criterion_shoulder_belt_load = self.report.Criterion_Overall.Criterion_Driver.Criterion_Chest.Criterion_ShoulderBeltLoad(report, isomme, p)

                def calculation(self):
                    self.criterion_chest_deflection.calculate()
                    self.criterion_chest_vc.calculate()

                    self.rating = np.min([self.criterion_chest_deflection.rating,
                                          self.criterion_chest_vc.rating])

                    # Modifier
                    self.criterion_shoulder_belt_load.calculate()
                    self.rating += self.criterion_shoulder_belt_load.rating

            class Criterion_Femur(Criterion):
                name = "Femur"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_femur_axial_force = self.report.Criterion_Overall.Criterion_Driver.Criterion_Femur.Criterion_Femur_Axial_Force(report, isomme, p=self.p)
                    self.criterion_submarining = self.report.Criterion_Overall.Criterion_Driver.Criterion_Femur.Criterion_Submarining(report, isomme, p=self.p)

                def calculation(self):
                    self.criterion_femur_axial_force.calculate()
                    self.rating = self.criterion_femur_axial_force.rating

                    # Modifier
                    self.criterion_submarining.calculate()
                    self.rating += self.criterion_submarining.rating

        class Criterion_DoorOpeningDuringImpact(Criterion):
            name: str = "Door Opening During Impact"
            number_of_door_openings_during_impact: int = 0

            def calculation(self):
                self.value = self.number_of_door_openings_during_impact
                self.rating = -1 * self.number_of_door_openings_during_impact

    class Page_Rating_Table(Page_Criterion_Rating_Table):
        name = "Rating"
        title = "Rating"

        def __init__(self, report):
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_driver,
                self.report.criterion_overall[isomme].criterion_front_passenger,
                self.report.criterion_overall[isomme].criterion_rear_passenger,
                self.report.criterion_overall[isomme].criterion_door_opening_during_impact,
                self.report.criterion_overall[isomme],
            ] for isomme in self.report.isomme_list}

    class Page_Driver_Result_Values_Chart(Page_Criterion_Values_Chart):
        name = "Driver Result Values Chart"
        title = "Driver Result"

        def __init__(self, report):
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_driver.criterion_head.criterion_hic_15,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head.criterion_head_a3ms,
                self.report.criterion_overall[isomme].criterion_driver.criterion_neck.criterion_my_extension,
                self.report.criterion_overall[isomme].criterion_driver.criterion_neck.criterion_fz_tension,
                self.report.criterion_overall[isomme].criterion_driver.criterion_neck.criterion_fx_shear,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest.criterion_shoulder_belt_load,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest.criterion_chest_deflection,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest.criterion_chest_vc,
                self.report.criterion_overall[isomme].criterion_driver.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_left,
                self.report.criterion_overall[isomme].criterion_driver.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_right,
            ] for isomme in self.report.isomme_list}

    class Page_Driver_Values_Table(Page_Criterion_Values_Table):
        name = "Driver Values Table"
        title = "Driver Values"

        def __init__(self, report):
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_driver.criterion_head.criterion_hic_15,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head.criterion_head_a3ms,
                self.report.criterion_overall[isomme].criterion_driver.criterion_neck.criterion_my_extension,
                self.report.criterion_overall[isomme].criterion_driver.criterion_neck.criterion_fz_tension,
                self.report.criterion_overall[isomme].criterion_driver.criterion_neck.criterion_fx_shear,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest.criterion_shoulder_belt_load,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest.criterion_chest_deflection,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest.criterion_chest_vc,
                self.report.criterion_overall[isomme].criterion_driver.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_left,
                self.report.criterion_overall[isomme].criterion_driver.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_right,
            ] for isomme in self.report.isomme_list}

    class Page_Driver_Rating_Table(Page_Criterion_Rating_Table):
        name: str = "Driver Rating Table"
        title: str = "Driver Rating"

        def __init__(self, report):
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_driver.criterion_head,
                self.report.criterion_overall[isomme].criterion_driver.criterion_neck,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest,
                self.report.criterion_overall[isomme].criterion_driver.criterion_femur,
                self.report.criterion_overall[isomme].criterion_driver,
            ] for isomme in self.report.isomme_list}

    class Page_Driver_Belt(Page_Plot_nxn):
        name: str = "Driver Belt"
        title: str = "Driver Belt"
        nrows: int = 3
        ncols: int = 2
        sharey: bool = False

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_driver}SEBE000[30]B1FO[X0]C"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}SEBE000[30]B2FO[X0]C"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}SEBE000[30]B3FO[X0]C"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}SEBE000[30]B4FO[X0]C"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}SEBE000[30]B5FO[X0]C"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}SEBE000[30]B6FO[X0]C"]] for isomme in self.report.isomme_list}

    class Page_Driver_Head_Acceleration(Page_Plot_nxn):
        name: str = "Driver Head Acceleration"
        title: str = "Driver Head Acceleration"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_driver}HEAD??????AC{xyzr}A"] for xyzr in "XYZR"] for isomme in self.report.isomme_list}

    class Page_Driver_Neck_Load(Page_Plot_nxn):
        name: str = "Driver Neck Load"
        title: str = "Driver Neck Load"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = False

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_driver}NECKUP00??MOYB"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}NECKUP00??FOZA"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}NECKUP00??FOXA"]] for isomme in self.report.isomme_list}

    class Page_Driver_Neck_NIJ(Page_Plot_nxn):
        name: str = "Driver Neck NIJ"
        title: str = "Driver Neck NIJ"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_driver}NIJCIPCF??00YB"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}NIJCIPCE??00YB"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}NIJCIPTF??00YB"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}NIJCIPTE??00YB"]] for isomme in self.report.isomme_list}

    class Page_Driver_Chest_Deflection(Page_Plot_nxn):
        name: str = "Driver Chest Deflection"
        title: str = "Driver Chest Deflection"
        nrows: int = 1
        ncols: int = 2

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_driver}CHST000???DSXC"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}VCCR000???VEXC"]] for isomme in self.report.isomme_list}

    class Page_Driver_Femur_Axial_Force(Page_Plot_nxn):
        name: str = "Driver Femur Axial Force"
        title: str = "Driver Femur Axial Force"
        nrows: int = 1
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_driver}FEMRLE00??FOZB"],
                                      [f"?{self.report.criterion_overall[isomme].p_driver}FEMRRI00??FOZB"]] for isomme in self.report.isomme_list}

    class Page_Front_Passenger_Result_Values_Chart(Page_Criterion_Values_Chart):
        name = "Front Passenger Result Values Chart"
        title = "Front Passenger Result"

        def __init__(self, report):
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_head.criterion_hic_15,
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_head.criterion_head_a3ms,
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_neck.criterion_my_extension,
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_neck.criterion_fz_tension,
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_neck.criterion_fx_shear,
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_chest.criterion_shoulder_belt_load,
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_chest.criterion_chest_deflection,
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_chest.criterion_chest_vc,
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_left,
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_right,
            ] for isomme in self.report.isomme_list}

    class Page_Front_Passenger_Rating_Table(Page_Criterion_Rating_Table):
        name: str = "Front Passenger Rating Table"
        title: str = "Front Passenger Rating"
        table_content: dict

        def __init__(self, report):
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_head,
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_neck,
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_chest,
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_femur,
                self.report.criterion_overall[isomme].criterion_front_passenger,
            ] for isomme in self.report.isomme_list}

    class Page_Front_Passenger_Values_Table(Page_Criterion_Values_Table):
        name: str = "Front Passenger Values Table"
        title: str = "Front Passenger Values"

        def __init__(self, report):
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_head.criterion_hic_15,
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_head.criterion_head_a3ms,
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_neck.criterion_my_extension,
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_neck.criterion_fz_tension,
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_neck.criterion_fx_shear,
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_chest.criterion_shoulder_belt_load,
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_chest.criterion_chest_deflection,
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_chest.criterion_chest_vc,
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_left,
                self.report.criterion_overall[isomme].criterion_front_passenger.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_right,
            ] for isomme in self.report.isomme_list}

    class Page_Front_Passenger_Belt(Page_Plot_nxn):
        name: str = "Front Passenger Belt"
        title: str = "Front Passenger Belt"
        nrows: int = 3
        ncols: int = 2
        sharey: bool = False

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_front_passenger}SEBE000[30]B1FO[X0]C"],
                                      [f"?{self.report.criterion_overall[isomme].p_front_passenger}SEBE000[30]B2FO[X0]C"],
                                      [f"?{self.report.criterion_overall[isomme].p_front_passenger}SEBE000[30]B3FO[X0]C"],
                                      [f"?{self.report.criterion_overall[isomme].p_front_passenger}SEBE000[30]B4FO[X0]C"],
                                      [f"?{self.report.criterion_overall[isomme].p_front_passenger}SEBE000[30]B5FO[X0]C"],
                                      [f"?{self.report.criterion_overall[isomme].p_front_passenger}SEBE000[30]B6FO[X0]C"]] for isomme in self.report.isomme_list}

    class Page_Front_Passenger_Head_Acceleration(Page_Plot_nxn):
        name: str = "Front Passenger Head Acceleration"
        title: str = "Front Passenger Head Acceleration"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_front_passenger}HEAD??????AC{xyzr}A"] for xyzr in "XYZR"] for isomme in self.report.isomme_list}

    class Page_Front_Passenger_Neck_Load(Page_Plot_nxn):
        name: str = "Front Passenger Neck Load"
        title: str = "Front Passenger Neck Load"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = False

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_front_passenger}NECKUP00??MOYB"],
                                      [f"?{self.report.criterion_overall[isomme].p_front_passenger}NECKUP00??FOZA"],
                                      [f"?{self.report.criterion_overall[isomme].p_front_passenger}NECKUP00??FOXA"]] for isomme in self.report.isomme_list}

    class Page_Front_Passenger_Neck_NIJ(Page_Plot_nxn):
        name: str = "Front Passenger Neck NIJ"
        title: str = "Front Passenger Neck NIJ"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_front_passenger}NIJCIPCF??00YB"],
                                      [f"?{self.report.criterion_overall[isomme].p_front_passenger}NIJCIPCE??00YB"],
                                      [f"?{self.report.criterion_overall[isomme].p_front_passenger}NIJCIPTF??00YB"],
                                      [f"?{self.report.criterion_overall[isomme].p_front_passenger}NIJCIPTE??00YB"]] for isomme in self.report.isomme_list}

    class Page_Front_Passenger_Chest_Deflection(Page_Plot_nxn):
        name: str = "Front Passenger Chest Deflection"
        title: str = "Front Passenger Chest Deflection"
        nrows: int = 1
        ncols: int = 1

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_front_passenger}CHST000???DSXC"]] for isomme in self.report.isomme_list}

    class Page_Front_Passenger_Femur_Axial_Force(Page_Plot_nxn):
        name: str = "Front Passenger Femur Axial Force"
        title: str = "Front Passenger Femur Axial Force"
        nrows: int = 1
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_front_passenger}FEMRLE00??FOZB"], [f"?{self.report.criterion_overall[isomme].p_front_passenger}FEMRRI00??FOZB"]] for isomme in self.report.isomme_list}

    class Page_Rear_Passenger_Result_Values_Chart(Page_Criterion_Values_Chart):
        name = "Rear Passenger Result Values Chart"
        title = "Rear Passenger Result"

        def __init__(self, report):
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_head.criterion_hic_15,
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_head.criterion_head_a3ms,
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_neck.criterion_my_extension,
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_neck.criterion_fz_tension,
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_neck.criterion_fx_shear,
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_chest.criterion_shoulder_belt_load,
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_chest.criterion_chest_deflection,
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_chest.criterion_chest_vc,
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_left,
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_right,
            ] for isomme in self.report.isomme_list}

    class Page_Rear_Passenger_Rating_Table(Page_Criterion_Rating_Table):
        name: str = "Rear Passenger Result Table"
        title: str = "Rear Passenger Result"

        def __init__(self, report):
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_head,
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_neck,
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_chest,
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_femur,
                self.report.criterion_overall[isomme].criterion_rear_passenger,
            ] for isomme in self.report.isomme_list}

    class Page_Rear_Passenger_Values_Table(Page_Criterion_Values_Table):
        name = "Rear Passenger Values Table"
        title = "Rear Passenger Values"

        def __init__(self, report):
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_head.criterion_hic_15,
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_head.criterion_head_a3ms,
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_neck.criterion_my_extension,
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_neck.criterion_fz_tension,
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_neck.criterion_fx_shear,
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_chest.criterion_shoulder_belt_load,
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_chest.criterion_chest_deflection,
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_chest.criterion_chest_vc,
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_left,
                self.report.criterion_overall[isomme].criterion_rear_passenger.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_right,
            ] for isomme in self.report.isomme_list}

    class Page_Rear_Passenger_Belt(Page_Plot_nxn):
        name: str = "Rear Passenger Belt"
        title: str = "Rear Passenger Belt"
        nrows: int = 3
        ncols: int = 2
        sharey: bool = False

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_rear_passenger}SEBE000[30]B1FO[X0]C"],
                                      [f"?{self.report.criterion_overall[isomme].p_rear_passenger}SEBE000[30]B2FO[X0]C"],
                                      [f"?{self.report.criterion_overall[isomme].p_rear_passenger}SEBE000[30]B3FO[X0]C"],
                                      [f"?{self.report.criterion_overall[isomme].p_rear_passenger}SEBE000[30]B4FO[X0]C"],
                                      [f"?{self.report.criterion_overall[isomme].p_rear_passenger}SEBE000[30]B5FO[X0]C"],
                                      [f"?{self.report.criterion_overall[isomme].p_rear_passenger}SEBE000[30]B6FO[X0]C"]] for isomme in self.report.isomme_list}

    class Page_Rear_Passenger_Head_Acceleration(Page_Plot_nxn):
        name: str = "Rear Passenger Head Acceleration"
        title: str = "Rear Passenger Head Acceleration"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_rear_passenger}HEAD??????AC{xyzr}A"] for xyzr in "XYZR"] for isomme in self.report.isomme_list}

    class Page_Rear_Passenger_Neck_Load(Page_Plot_nxn):
        name: str = "Rear Passenger Neck Load"
        title: str = "Rear Passenger Neck Load"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = False

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_rear_passenger}NECKUP00??MOYB"],
                                      [f"?{self.report.criterion_overall[isomme].p_rear_passenger}NECKUP00??FOZA"],
                                      [f"?{self.report.criterion_overall[isomme].p_rear_passenger}NECKUP00??FOXA"]] for isomme in self.report.isomme_list}

    class Page_Rear_Passenger_Chest_Deflection(Page_Plot_nxn):
        name: str = "Rear Passenger Chest Deflection"
        title: str = "Rear Passenger Chest Deflection"
        nrows: int = 1
        ncols: int = 1

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_rear_passenger}CHST000???DSXC"]] for isomme in self.report.isomme_list}

    class Page_Rear_Passenger_Femur_Axial_Force(Page_Plot_nxn):
        name: str = "Rear Passenger Femur Axial Force"
        title: str = "Rear Passenger Femur Axial Force"
        nrows: int = 1
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p_rear_passenger}FEMRLE00??FOZB"],
                                      [f"?{self.report.criterion_overall[isomme].p_rear_passenger}FEMRRI00??FOZB"]] for isomme in self.report.isomme_list}
