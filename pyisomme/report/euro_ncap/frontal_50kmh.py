from pyisomme.calculate import *
from pyisomme.limits import Limit
from pyisomme.report.page import Page_Cover, Page_OLC, Page_Result_Table, Page_Plot_nxn
from pyisomme.report.report import Report
from pyisomme.report.criterion import Criterion
from pyisomme.report.euro_ncap.limits import Limit_4Points, Limit_3Points, Limit_2Points, Limit_1Points, Limit_0Points, Limit_Capping

from astropy.constants import g0
import logging


logger = logging.getLogger(__name__)


class EuroNCAP_Frontal_50kmh(Report):
    name = "Euro NCAP | Frontal-Impact against Rigid Wall with 100 % Overlap at 50 km/h"

    def __init__(self, isomme_list, title: str = "Report"):
        super().__init__(isomme_list, title)

        self.pages = [
            Page_Cover(self),
            self.Page_Driver_Result_Table(self),
            self.Page_Driver_Result_Values_Table(self),
            self.Page_Driver_Head_Acceleration(self),
            self.Page_Driver_Neck_Load(self),
            self.Page_Driver_Chest_Deflection(self),
            self.Page_Driver_Femur_Axial_Force(self),

            self.Page_Front_Passenger_Result_Table(self),
            self.Page_Front_Passenger_Head_Acceleration(self),
            self.Page_Front_Passenger_Neck_Load(self),
            self.Page_Front_Passenger_Chest_Deflection(self),
            self.Page_Front_Passenger_Femur_Axial_Force(self),

            self.Page_Rear_Passenger_Result_Table(self),
            self.Page_Rear_Passenger_Head_Acceleration(self),
            self.Page_Rear_Passenger_Neck_Load(self),
            self.Page_Rear_Passenger_Chest_Deflection(self),
            self.Page_Rear_Passenger_Femur_Axial_Force(self),

            Page_OLC(self),
        ]

    class Criterion_Master(Criterion):
        name = "Master"
        p_driver: int = 1
        p_front_passenger: int = 3
        p_rear_passenger: int = 6

        def __init__(self, report, isomme):
            super().__init__(report, isomme)

            p_driver = isomme.get_test_info("Driver position object 1")
            if p_driver is not None:
                self.p_driver = p_driver
            self.p_front_passenger = 1 if p_driver != 1 else self.p_front_passenger
            self.p_rear_passenger = 4 if p_driver != 1 else self.p_rear_passenger

            self.criterion_driver = self.Criterion_Driver(report, isomme, p=self.p_driver)
            self.criterion_front_passenger = self.Criterion_Front_Passenger(report, isomme, p=self.p_front_passenger)
            self.criterion_rear_passenger = self.Criterion_Rear_Passenger(report, isomme, p=self.p_rear_passenger)
            self.criterion_DoorOpeningDuringImpact = self.Criterion_DoorOpeningDuringImpact(report, isomme)

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
            self.rating += self.criterion_DoorOpeningDuringImpact.rating

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
                    if self.report.criterion_master[self.isomme].criterion_driver.steering_wheel_airbag_exists:
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
                            Limit_4Points([f"?{self.p}HICR0015??00RX"], func=lambda x: 500, y_unit=1, upper=True),
                            Limit_3Points([f"?{self.p}HICR0015??00RX"], func=lambda x: 550, y_unit=1, upper=True),
                            Limit_2Points([f"?{self.p}HICR0015??00RX"], func=lambda x: 600, y_unit=1, upper=True),
                            Limit_1Points([f"?{self.p}HICR0015??00RX"], func=lambda x: 650, y_unit=1, upper=True),
                            Limit_0Points([f"?{self.p}HICR0015??00RX"], func=lambda x: 700, y_unit=1, upper=True),
                            Limit_Capping([f"?{self.p}HICR0015??00RX"], func=lambda x: 700, y_unit=1, lower=True),
                        ])

                    def calculation(self):
                        self.channel = calculate_hic(self.isomme.get_channel(f"?{self.p}HEAD??00??ACRA"), 15)
                        self.value = self.channel.get_data()[0]
                        self.rating = np.interp(self.value, [500, 700], [4, 0], left=4, right=-np.inf)

                class Criterion_Head_a3ms(Criterion):
                    name = "Head a3ms"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_4Points([f"?{self.p}HEAD003C??ACRA"], func=lambda x: 72, y_unit=Unit(g0), upper=True),
                            Limit_3Points([f"?{self.p}HEAD003C??ACRA"], func=lambda x: 74, y_unit=Unit(g0), upper=True),
                            Limit_2Points([f"?{self.p}HEAD003C??ACRA"], func=lambda x: 76, y_unit=Unit(g0), upper=True),
                            Limit_1Points([f"?{self.p}HEAD003C??ACRA"], func=lambda x: 78, y_unit=Unit(g0), upper=True),
                            Limit_0Points([f"?{self.p}HEAD003C??ACRA"], func=lambda x: 80, y_unit=Unit(g0), upper=True),
                            Limit_Capping([f"?{self.p}HEAD003C??ACRA"], func=lambda x: 80, y_unit=Unit(g0), lower=True),
                        ])

                    def calculation(self):
                        self.channel = calculate_xms(self.isomme.get_channel(f"?{self.p}HEAD0000??ACRA", f"?{self.p}HEADCG00??ACRA"), 3, method="C")
                        self.value = self.channel.get_data(unit=g0)[0]
                        self.rating = np.interp(self.value, [72, 80], [4, 0], left=4, right=-np.inf)

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
                        is_driver = self.report.criterion_master[self.isomme].p_driver == self.p

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

                    if not self.report.criterion_master[self.isomme].criterion_driver.steering_wheel_airbag_exists:
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
                            Limit_4Points([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -36.00, y_unit="Nm", lower=True),
                            Limit_3Points([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -39.25, y_unit="Nm", lower=True),
                            Limit_2Points([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -42.50, y_unit="Nm", lower=True),
                            Limit_1Points([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -45.75, y_unit="Nm", lower=True),
                            Limit_0Points([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -49.00, y_unit="Nm", lower=True, upper=True),
                            Limit_Capping([f"?{self.p}NECKUP00??MOYB"], func=lambda x: -57.00, y_unit="Nm", upper=True)
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??MOYB")
                        self.value = np.min(self.channel.get_data(unit="Nm"))
                        self.rating = self.limits.get_limit_min_value(self.channel)

                class Criterion_Fz_tension(Criterion):
                    name = "Neck Fz tension"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_4Points([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 1.70, y_unit="kN", upper=True),
                            Limit_3Points([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 1.93, y_unit="kN", upper=True),
                            Limit_2Points([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 2.16, y_unit="kN", upper=True),
                            Limit_1Points([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 2.39, y_unit="kN", upper=True),
                            Limit_0Points([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 2.62, y_unit="kN", upper=True, lower=True),
                            Limit_Capping([f"?{self.p}NECKUP00??FOZA"], func=lambda x: 2.90, y_unit="kN", lower=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??FOZA").convert_unit("kN")
                        self.value = np.max(self.channel.get_data())
                        self.rating = self.limits.get_limit_min_value(self.channel)

                class Criterion_Fx_shear(Criterion):
                    name = "Neck Fx shear"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_4Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.2000, y_unit="kN", upper=True),
                            Limit_3Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.3875, y_unit="kN", upper=True),
                            Limit_2Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.5750, y_unit="kN", upper=True),
                            Limit_1Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.7625, y_unit="kN", upper=True),
                            Limit_0Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.9500, y_unit="kN", upper=True, lower=True),

                            Limit_4Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.2000, y_unit="kN", lower=True),
                            Limit_3Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.3875, y_unit="kN", lower=True),
                            Limit_2Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.5750, y_unit="kN", lower=True),
                            Limit_1Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.7625, y_unit="kN", lower=True),
                            Limit_0Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.9500, y_unit="kN", lower=True, upper=True),

                            Limit_Capping([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 2.7000, y_unit="kN", lower=True),
                            Limit_Capping([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -2.7000, y_unit="kN", upper=True)
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??FOXA").convert_unit("kN")
                        self.value = self.channel.get_data(unit="kN")[np.argmax(np.abs(self.channel.get_data()))]
                        self.rating = self.limits.get_limit_min_value(self.channel)

            class Criterion_Chest(Criterion):
                name = "Chest"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_chest_deflection = self.Criterion_Chest_Deflection(report, isomme, p)
                    self.criterion_chest_vc = self.Criterion_Chest_VC(report, isomme, p)
                    self.criterion_SteeringWheelContact = self.Criterion_SteeringWheelContact(report, isomme, p)
                    self.criterion_ShoulderBeltLoad = self.Criterion_ShoulderBeltLoad(report, isomme, p)

                def calculation(self):
                    self.criterion_chest_deflection.calculate()
                    self.criterion_chest_vc.calculate()

                    self.rating = np.min([self.criterion_chest_deflection.rating,
                                          self.criterion_chest_vc.rating])

                    # Modifier
                    self.criterion_SteeringWheelContact.calculate()
                    self.criterion_ShoulderBeltLoad.calculate()
                    self.rating += np.sum([self.criterion_SteeringWheelContact.rating,
                                           self.criterion_ShoulderBeltLoad.rating])

                class Criterion_Chest_Deflection(Criterion):
                    name = "Chest Deflection"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_Capping([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -34, y_unit="mm", upper=True),
                            Limit_0Points([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -34, y_unit="mm", lower=True),
                            Limit_1Points([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -30, y_unit="mm", lower=True),
                            Limit_2Points([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -26, y_unit="mm", lower=True),
                            Limit_3Points([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -22, y_unit="mm", lower=True),
                            Limit_4Points([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -18, y_unit="mm", lower=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}CHST0003??DSXC", f"?{self.p}CHST0000??DSXC").convert_unit("mm")
                        self.value = np.min(self.channel.get_data())
                        self.rating = self.limits.get_limit_min_value(self.channel, interpolate=True)
                        self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_Chest_VC(Criterion):
                    name = "Chest VC"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_4Points([f"?{self.p}VCCR0000??VEX?"], func=lambda x: 0.500, y_unit="m/s", upper=True),
                            Limit_3Points([f"?{self.p}VCCR0000??VEX?"], func=lambda x: 0.625, y_unit="m/s", upper=True),
                            Limit_2Points([f"?{self.p}VCCR0000??VEX?"], func=lambda x: 0.750, y_unit="m/s", upper=True),
                            Limit_1Points([f"?{self.p}VCCR0000??VEX?"], func=lambda x: 0.875, y_unit="m/s", upper=True),
                            Limit_0Points([f"?{self.p}VCCR0000??VEX?"], func=lambda x: 1.000, y_unit="m/s", upper=True),
                            Limit_Capping([f"?{self.p}VCCR0000??VEX?"], func=lambda x: 1.000, y_unit="m/s", lower=True),
                        ])

                    def calculation(self):
                        chest_deflection = (self.isomme.get_channel(f"?{self.p}CHST0003??DSXC", f"?{self.p}CHST0000??DSXC"))
                        chest_deflection = chest_deflection * -1 if abs(min(chest_deflection.get_data())) > max(chest_deflection.get_data()) else chest_deflection

                        self.channel = calculate_chest_vc(chest_deflection).convert_unit("m/s")
                        self.value = max(self.channel.get_data())
                        self.rating = np.interp(self.value, [0.5, 1.0], [4, 0], left=4, right=-np.inf)

                class Criterion_SteeringWheelContact(Criterion):
                    name = "Modifier Chest Steering Wheel Contact"
                    steering_wheel_contact: bool = False

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                    def calculation(self):
                        is_driver = self.report.criterion_master[self.isomme].p_driver == self.p
                        self.rating = -1 if is_driver and self.steering_wheel_contact else 0

                class Criterion_ShoulderBeltLoad(Criterion):
                    name = "Modifier Shoulder Belt Load"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit([f"?{self.p}SEBE????B3FO[X0]?"], name="-2 pt. Modifier", func=lambda: 6.0, y_unit="kN", lower=True, color="red")
                        ])

                    def calculate(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}SEBE????B3FO[X0]D")
                        self.value = np.max(self.channel.get_data(unit="kN"))
                        self.rating = -2 if self.value >= 6 else 0

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

                        self.extend_limit_list([
                            Limit_4Points([f"?{self.p}FEMRLE00??FOZ?", f"?{self.p}FEMRRI00??FOZ?"], func=lambda x: -2.6, y_unit="kN", lower=True),
                            Limit_3Points([f"?{self.p}FEMRLE00??FOZ?", f"?{self.p}FEMRRI00??FOZ?"], func=lambda x: -3.5, y_unit="kN", lower=True),
                            Limit_2Points([f"?{self.p}FEMRLE00??FOZ?", f"?{self.p}FEMRRI00??FOZ?"], func=lambda x: -4.4, y_unit="kN", lower=True),
                            Limit_1Points([f"?{self.p}FEMRLE00??FOZ?", f"?{self.p}FEMRRI00??FOZ?"], func=lambda x: -5.3, y_unit="kN", lower=True),
                            Limit_0Points([f"?{self.p}FEMRLE00??FOZ?", f"?{self.p}FEMRRI00??FOZ?"], func=lambda x: -6.2, y_unit="kN", lower=True, upper=True),
                        ])

                        self.criterion_femur_axial_force_left = self.Criterion_Femur_Axial_Force_Left(report, isomme, p=self.p)
                        self.criterion_femur_axial_force_right = self.Criterion_Femur_Axial_Force_Right(report, isomme, p=self.p)

                    def calculation(self):
                        self.criterion_femur_axial_force_left.calculate()
                        self.criterion_femur_axial_force_right.calculate()

                        self.value = np.max([self.criterion_femur_axial_force_left.value, self.criterion_femur_axial_force_right.value])
                        self.rating = np.interp(self.value, [2.6, 6.2], [4, 0], left=4, right=0)

                    class Criterion_Femur_Axial_Force_Left(Criterion):
                        name = "Femur Axial Force Left"

                        def __init__(self, report, isomme, p):
                            super().__init__(report, isomme)

                            self.p = p

                        def calculation(self):
                            self.channel = self.isomme.get_channel(f"?{self.p}FEMRLE00??FOZB")
                            self.value = abs(min(self.channel.get_data(unit="kN")))

                    class Criterion_Femur_Axial_Force_Right(Criterion):
                        name = "Femur Axial Force Right"

                        def __init__(self, report, isomme, p):
                            super().__init__(report, isomme)

                            self.p = p

                        def calculation(self):
                            self.channel = self.isomme.get_channel(f"?{self.p}FEMRRI00??FOZB")
                            self.value = abs(min(self.channel.get_data(unit="kN")))

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

                    self.criterion_hic_15 = self.Criterion_HIC_15(report, isomme, p=self.p)
                    self.criterion_head_a3ms = self.Criterion_Head_a3ms(report, isomme, p=self.p)
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

                class Criterion_HIC_15(Criterion):
                    name = "HIC 15"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_4Points([f"?{self.p}HICR0015??00RX"], func=lambda x: 500, y_unit=1, upper=True),
                            Limit_3Points([f"?{self.p}HICR0015??00RX"], func=lambda x: 550, y_unit=1, upper=True),
                            Limit_2Points([f"?{self.p}HICR0015??00RX"], func=lambda x: 600, y_unit=1, upper=True),
                            Limit_1Points([f"?{self.p}HICR0015??00RX"], func=lambda x: 650, y_unit=1, upper=True),
                            Limit_0Points([f"?{self.p}HICR0015??00RX"], func=lambda x: 700, y_unit=1, upper=True),
                            Limit_Capping([f"?{self.p}HICR0015??00RX"], func=lambda x: 700, y_unit=1, lower=True),
                        ])

                    def calculation(self):
                        self.channel = calculate_hic(self.isomme.get_channel(f"?{self.p}HEAD??00??ACRA"), 15)
                        self.value = self.channel.get_data()[0]
                        self.rating = np.interp(self.value, [500, 700], [4, 0], left=4, right=-np.inf)

                class Criterion_Head_a3ms(Criterion):
                    name = "Head a3ms"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_4Points([f"?{self.p}HEAD003C??ACRA"], func=lambda x: 72, y_unit=Unit(g0), upper=True),
                            Limit_3Points([f"?{self.p}HEAD003C??ACRA"], func=lambda x: 74, y_unit=Unit(g0), upper=True),
                            Limit_2Points([f"?{self.p}HEAD003C??ACRA"], func=lambda x: 76, y_unit=Unit(g0), upper=True),
                            Limit_1Points([f"?{self.p}HEAD003C??ACRA"], func=lambda x: 78, y_unit=Unit(g0), upper=True),
                            Limit_0Points([f"?{self.p}HEAD003C??ACRA"], func=lambda x: 80, y_unit=Unit(g0), upper=True),
                            Limit_Capping([f"?{self.p}HEAD003C??ACRA"], func=lambda x: 80, y_unit=Unit(g0), lower=True),
                        ])

                    def calculation(self):
                        self.channel = calculate_xms(self.isomme.get_channel(f"?{self.p}HEAD0000??ACRA", f"?{self.p}HEADCG00??ACRA"), 3, method="C")
                        self.value = self.channel.get_data(unit=g0)[0]
                        self.rating = np.interp(self.value, [72, 80], [4, 0], left=4, right=-np.inf)

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
                            Limit_4Points([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -36.00, y_unit="Nm", lower=True),
                            Limit_3Points([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -39.25, y_unit="Nm", lower=True),
                            Limit_2Points([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -42.50, y_unit="Nm", lower=True),
                            Limit_1Points([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -45.75, y_unit="Nm", lower=True),
                            Limit_0Points([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -49.00, y_unit="Nm", lower=True, upper=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??MOYB")
                        self.value = np.abs(np.min(self.channel.get_data(unit="Nm")))
                        self.rating = self.limits.get_limit_min_value(self.channel)

                class Criterion_Fz_tension(Criterion):
                    name = "Neck Fz tension"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_4Points([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 1.70, y_unit="kN", upper=True),
                            Limit_3Points([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 1.93, y_unit="kN", upper=True),
                            Limit_2Points([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 2.16, y_unit="kN", upper=True),
                            Limit_1Points([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 2.39, y_unit="kN", upper=True),
                            Limit_0Points([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 2.62, y_unit="kN", upper=True, lower=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??FOZA").convert_unit("kN")
                        self.value = np.max(self.channel.get_data())
                        self.rating = self.limits.get_limit_min_value(self.channel)

                class Criterion_Fx_shear(Criterion):
                    name = "Neck Fx shear"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_4Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.2000, y_unit="kN", upper=True),
                            Limit_3Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.3875, y_unit="kN", upper=True),
                            Limit_2Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.5750, y_unit="kN", upper=True),
                            Limit_1Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.7625, y_unit="kN", upper=True),
                            Limit_0Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.9500, y_unit="kN", upper=True, lower=True),

                            Limit_4Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.2000, y_unit="kN", lower=True),
                            Limit_3Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.3875, y_unit="kN", lower=True),
                            Limit_2Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.5750, y_unit="kN", lower=True),
                            Limit_1Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.7625, y_unit="kN", lower=True),
                            Limit_0Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.9500, y_unit="kN", lower=True, upper=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??FOXA").convert_unit("kN")
                        self.value = self.channel.get_data(unit="kN")[np.argmax(np.abs(self.channel.get_data()))]
                        self.rating = self.limits.get_limit_min_value(self.channel)

            class Criterion_Chest(Criterion):
                name = "Chest"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_chest_deflection = self.Criterion_Chest_Deflection(report, isomme, p)
                    self.criterion_chest_vc = self.Criterion_Chest_VC(report, isomme, p)
                    self.criterion_ShoulderBeltLoad = self.Criterion_ShoulderBeltLoad(report, isomme, p)

                def calculation(self):
                    self.criterion_chest_deflection.calculate()
                    self.criterion_chest_vc.calculate()

                    self.rating = np.min([self.criterion_chest_deflection.rating,
                                          self.criterion_chest_vc.rating])

                    # Modifier
                    self.criterion_ShoulderBeltLoad.calculate()
                    self.rating += self.criterion_ShoulderBeltLoad.rating

                class Criterion_Chest_Deflection(Criterion):
                    name = "Chest Deflection"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_Capping([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -34, y_unit="mm", upper=True),
                            Limit_0Points([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -34, y_unit="mm", lower=True),
                            Limit_1Points([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -30, y_unit="mm", lower=True),
                            Limit_2Points([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -26, y_unit="mm", lower=True),
                            Limit_3Points([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -22, y_unit="mm", lower=True),
                            Limit_4Points([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -18, y_unit="mm", lower=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}CHST0003??DSXC", f"?{self.p}CHST0000??DSXC").convert_unit("mm")
                        self.value = np.min(self.channel.get_data())
                        self.rating = self.limits.get_limit_min_value(self.channel, interpolate=True)
                        self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_Chest_VC(Criterion):
                    name = "Chest VC"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_4Points([f"?{self.p}VCCR0000??VEX?"], func=lambda x: 0.500, y_unit="m/s", upper=True),
                            Limit_3Points([f"?{self.p}VCCR0000??VEX?"], func=lambda x: 0.625, y_unit="m/s", upper=True),
                            Limit_2Points([f"?{self.p}VCCR0000??VEX?"], func=lambda x: 0.750, y_unit="m/s", upper=True),
                            Limit_1Points([f"?{self.p}VCCR0000??VEX?"], func=lambda x: 0.875, y_unit="m/s", upper=True),
                            Limit_0Points([f"?{self.p}VCCR0000??VEX?"], func=lambda x: 1.000, y_unit="m/s", upper=True),
                            Limit_Capping([f"?{self.p}VCCR0000??VEX?"], func=lambda x: 1.000, y_unit="m/s", lower=True),
                        ])

                    def calculation(self):
                        chest_deflection = (self.isomme.get_channel(f"?{self.p}CHST0003??DSXC", f"?{self.p}CHST0000??DSXC"))
                        chest_deflection = chest_deflection * -1 if abs(min(chest_deflection.get_data())) > max(chest_deflection.get_data()) else chest_deflection

                        self.channel = calculate_chest_vc(chest_deflection).convert_unit("m/s")
                        self.value = max(self.channel.get_data())
                        self.rating = np.interp(self.value, [0.5, 1.0], [4, 0], left=4, right=-np.inf)

                class Criterion_ShoulderBeltLoad(Criterion):
                    name = "Modifier Shoulder Belt Load"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit([f"?{self.p}SEBE????B3FO[X0]?"], name="-2 pt. Modifier", func=lambda: 6.0, y_unit="kN", lower=True, color="red")
                        ])

                    def calculate(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}SEBE????B3FO[X0]D")
                        self.value = np.max(self.channel.get_data(unit="kN"))
                        self.rating = -2 if self.value >= 6 else 0

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

                        self.extend_limit_list([
                            Limit_4Points([f"?{self.p}FEMRLE00??FOZ?", f"?{self.p}FEMRRI00??FOZ?"], func=lambda x: -2.6, y_unit="kN", lower=True),
                            Limit_3Points([f"?{self.p}FEMRLE00??FOZ?", f"?{self.p}FEMRRI00??FOZ?"], func=lambda x: -3.5, y_unit="kN", lower=True),
                            Limit_2Points([f"?{self.p}FEMRLE00??FOZ?", f"?{self.p}FEMRRI00??FOZ?"], func=lambda x: -4.4, y_unit="kN", lower=True),
                            Limit_1Points([f"?{self.p}FEMRLE00??FOZ?", f"?{self.p}FEMRRI00??FOZ?"], func=lambda x: -5.3, y_unit="kN", lower=True),
                            Limit_0Points([f"?{self.p}FEMRLE00??FOZ?", f"?{self.p}FEMRRI00??FOZ?"], func=lambda x: -6.2, y_unit="kN", lower=True, upper=True),
                        ])

                        self.criterion_femur_axial_force_left = self.Criterion_Femur_Axial_Force_Left(report, isomme, p=self.p)
                        self.criterion_femur_axial_force_right = self.Criterion_Femur_Axial_Force_Right(report, isomme, p=self.p)

                    def calculation(self):
                        self.criterion_femur_axial_force_left.calculate()
                        self.criterion_femur_axial_force_right.calculate()

                        self.value = np.max([self.criterion_femur_axial_force_left.value, self.criterion_femur_axial_force_right.value])
                        self.rating = np.interp(self.value, [2.6, 6.2], [4, 0], left=4, right=0)

                    class Criterion_Femur_Axial_Force_Left(Criterion):
                        name = "Femur Axial Force Left"

                        def __init__(self, report, isomme, p):
                            super().__init__(report, isomme)

                            self.p = p

                        def calculation(self):
                            self.channel = self.isomme.get_channel(f"?{self.p}FEMRLE00??FOZB")
                            self.value = abs(min(self.channel.get_data(unit="kN")))

                    class Criterion_Femur_Axial_Force_Right(Criterion):
                        name = "Femur Axial Force Right"

                        def __init__(self, report, isomme, p):
                            super().__init__(report, isomme)

                            self.p = p

                        def calculation(self):
                            self.channel = self.isomme.get_channel(f"?{self.p}FEMRRI00??FOZB")
                            self.value = abs(min(self.channel.get_data(unit="kN")))

                class Criterion_Submarining(Criterion):
                    name = "Submarining"
                    submarining: bool = False

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                    def calculation(self):
                        self.value = self.submarining
                        self.rating = -4 if self.submarining else 0

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

                    self.criterion_hic_15 = self.Criterion_HIC_15(report, isomme, p=self.p)
                    self.criterion_head_a3ms = self.Criterion_Head_a3ms(report, isomme, p=self.p)
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

                class Criterion_HIC_15(Criterion):
                    name = "HIC 15"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_4Points([f"?{self.p}HICR0015??00RX"], func=lambda x: 500, y_unit=1, upper=True),
                            Limit_3Points([f"?{self.p}HICR0015??00RX"], func=lambda x: 550, y_unit=1, upper=True),
                            Limit_2Points([f"?{self.p}HICR0015??00RX"], func=lambda x: 600, y_unit=1, upper=True),
                            Limit_1Points([f"?{self.p}HICR0015??00RX"], func=lambda x: 650, y_unit=1, upper=True),
                            Limit_0Points([f"?{self.p}HICR0015??00RX"], func=lambda x: 700, y_unit=1, upper=True),
                            Limit_Capping([f"?{self.p}HICR0015??00RX"], func=lambda x: 700, y_unit=1, lower=True),
                        ])

                    def calculation(self):
                        self.channel = calculate_hic(self.isomme.get_channel(f"?{self.p}HEAD??00??ACRA"), 15)
                        self.value = self.channel.get_data()[0]
                        self.rating = np.interp(self.value, [500, 700], [4, 0], left=4, right=-np.inf)

                class Criterion_Head_a3ms(Criterion):
                    name = "Head a3ms"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_4Points([f"?{self.p}HEAD003C??ACRA"], func=lambda x: 72, y_unit=Unit(g0), upper=True),
                            Limit_3Points([f"?{self.p}HEAD003C??ACRA"], func=lambda x: 74, y_unit=Unit(g0), upper=True),
                            Limit_2Points([f"?{self.p}HEAD003C??ACRA"], func=lambda x: 76, y_unit=Unit(g0), upper=True),
                            Limit_1Points([f"?{self.p}HEAD003C??ACRA"], func=lambda x: 78, y_unit=Unit(g0), upper=True),
                            Limit_0Points([f"?{self.p}HEAD003C??ACRA"], func=lambda x: 80, y_unit=Unit(g0), upper=True),
                            Limit_Capping([f"?{self.p}HEAD003C??ACRA"], func=lambda x: 80, y_unit=Unit(g0), lower=True),
                        ])

                    def calculation(self):
                        self.channel = calculate_xms(self.isomme.get_channel(f"?{self.p}HEAD0000??ACRA", f"?{self.p}HEADCG00??ACRA"), 3, method="C")
                        self.value = self.channel.get_data(unit=g0)[0]
                        self.rating = np.interp(self.value, [72, 80], [4, 0], left=4, right=-np.inf)

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
                            Limit_4Points([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -36.00, y_unit="Nm", lower=True),
                            Limit_3Points([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -39.25, y_unit="Nm", lower=True),
                            Limit_2Points([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -42.50, y_unit="Nm", lower=True),
                            Limit_1Points([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -45.75, y_unit="Nm", lower=True),
                            Limit_0Points([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -49.00, y_unit="Nm", lower=True, upper=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??MOYB")
                        self.value = np.abs(np.min(self.channel.get_data(unit="Nm")))
                        self.rating = self.limits.get_limit_min_value(self.channel)
                        # Reduce max. rating for rear passenger
                        self.rating = np.min([2, self.rating])

                class Criterion_Fz_tension(Criterion):
                    name = "Neck Fz tension"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_4Points([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 1.70, y_unit="kN", upper=True),
                            Limit_3Points([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 1.93, y_unit="kN", upper=True),
                            Limit_2Points([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 2.16, y_unit="kN", upper=True),
                            Limit_1Points([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 2.39, y_unit="kN", upper=True),
                            Limit_0Points([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 2.62, y_unit="kN", upper=True, lower=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??FOZA").convert_unit("kN")
                        self.value = np.max(self.channel.get_data())
                        self.rating = self.limits.get_limit_min_value(self.channel)
                        # Reduce max. rating for rear passenger
                        self.rating = np.min([1, self.rating])

                class Criterion_Fx_shear(Criterion):
                    name = "Neck Fx shear"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_4Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.2000, y_unit="kN", upper=True),
                            Limit_3Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.3875, y_unit="kN", upper=True),
                            Limit_2Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.5750, y_unit="kN", upper=True),
                            Limit_1Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.7625, y_unit="kN", upper=True),
                            Limit_0Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 1.9500, y_unit="kN", upper=True, lower=True),

                            Limit_4Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.2000, y_unit="kN", lower=True),
                            Limit_3Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.3875, y_unit="kN", lower=True),
                            Limit_2Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.5750, y_unit="kN", lower=True),
                            Limit_1Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.7625, y_unit="kN", lower=True),
                            Limit_0Points([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -1.9500, y_unit="kN", lower=True, upper=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??FOXA").convert_unit("kN")
                        self.value = self.channel.get_data(unit="kN")[np.argmax(np.abs(self.channel.get_data()))]
                        self.rating = self.limits.get_limit_min_value(self.channel)
                        # Reduce max. rating for rear passenger
                        self.rating = np.min([1, self.rating])

            class Criterion_Chest(Criterion):
                name = "Chest"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_chest_deflection = self.Criterion_Chest_Deflection(report, isomme, p)
                    self.criterion_chest_vc = self.Criterion_Chest_VC(report, isomme, p)
                    self.criterion_ShoulderBeltLoad = self.Criterion_ShoulderBeltLoad(report, isomme, p)

                def calculation(self):
                    self.criterion_chest_deflection.calculate()
                    self.criterion_chest_vc.calculate()

                    self.rating = np.min([self.criterion_chest_deflection.rating,
                                          self.criterion_chest_vc.rating])

                    # Modifier
                    self.criterion_ShoulderBeltLoad.calculate()
                    self.rating += self.criterion_ShoulderBeltLoad.rating

                class Criterion_Chest_Deflection(Criterion):
                    name = "Chest Deflection"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_Capping([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -34, y_unit="mm", upper=True),
                            Limit_0Points([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -34, y_unit="mm", lower=True),
                            Limit_1Points([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -30, y_unit="mm", lower=True),
                            Limit_2Points([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -26, y_unit="mm", lower=True),
                            Limit_3Points([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -22, y_unit="mm", lower=True),
                            Limit_4Points([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -18, y_unit="mm", lower=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}CHST0003??DSXC", f"?{self.p}CHST0000??DSXC").convert_unit("mm")
                        self.value = np.min(self.channel.get_data())
                        self.rating = self.limits.get_limit_min_value(self.channel, interpolate=True)
                        self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_Chest_VC(Criterion):
                    name = "Chest VC"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_4Points([f"?{self.p}VCCR0000??VEX?"], func=lambda x: 0.500, y_unit="m/s", upper=True),
                            Limit_3Points([f"?{self.p}VCCR0000??VEX?"], func=lambda x: 0.625, y_unit="m/s", upper=True),
                            Limit_2Points([f"?{self.p}VCCR0000??VEX?"], func=lambda x: 0.750, y_unit="m/s", upper=True),
                            Limit_1Points([f"?{self.p}VCCR0000??VEX?"], func=lambda x: 0.875, y_unit="m/s", upper=True),
                            Limit_0Points([f"?{self.p}VCCR0000??VEX?"], func=lambda x: 1.000, y_unit="m/s", upper=True),
                            Limit_Capping([f"?{self.p}VCCR0000??VEX?"], func=lambda x: 1.000, y_unit="m/s", lower=True),
                        ])

                    def calculation(self):
                        chest_deflection = (self.isomme.get_channel(f"?{self.p}CHST0003??DSXC", f"?{self.p}CHST0000??DSXC"))
                        chest_deflection = chest_deflection * -1 if abs(min(chest_deflection.get_data())) > max(chest_deflection.get_data()) else chest_deflection

                        self.channel = calculate_chest_vc(chest_deflection).convert_unit("m/s")
                        self.value = max(self.channel.get_data())
                        self.rating = np.interp(self.value, [0.5, 1.0], [4, 0], left=4, right=-np.inf)

                class Criterion_ShoulderBeltLoad(Criterion):
                    name = "Modifier Shoulder Belt Load"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit([f"?{self.p}SEBE????B3FO[X0]?"], name="-2 pt. Modifier", func=lambda: 6.0, y_unit="kN", lower=True, color="red")
                        ])

                    def calculate(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}SEBE????B3FO[X0]D")
                        self.value = np.max(self.channel.get_data(unit="kN"))
                        self.rating = -2 if self.value >= 6 else 0

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

                        self.extend_limit_list([
                            Limit_4Points([f"?{self.p}FEMRLE00??FOZ?", f"?{self.p}FEMRRI00??FOZ?"], func=lambda x: -2.6, y_unit="kN", lower=True),
                            Limit_3Points([f"?{self.p}FEMRLE00??FOZ?", f"?{self.p}FEMRRI00??FOZ?"], func=lambda x: -3.5, y_unit="kN", lower=True),
                            Limit_2Points([f"?{self.p}FEMRLE00??FOZ?", f"?{self.p}FEMRRI00??FOZ?"], func=lambda x: -4.4, y_unit="kN", lower=True),
                            Limit_1Points([f"?{self.p}FEMRLE00??FOZ?", f"?{self.p}FEMRRI00??FOZ?"], func=lambda x: -5.3, y_unit="kN", lower=True),
                            Limit_0Points([f"?{self.p}FEMRLE00??FOZ?", f"?{self.p}FEMRRI00??FOZ?"], func=lambda x: -6.2, y_unit="kN", lower=True, upper=True),
                        ])

                        self.criterion_femur_axial_force_left = self.Criterion_Femur_Axial_Force_Left(report, isomme, p=self.p)
                        self.criterion_femur_axial_force_right = self.Criterion_Femur_Axial_Force_Right(report, isomme, p=self.p)

                    def calculation(self):
                        self.criterion_femur_axial_force_left.calculate()
                        self.criterion_femur_axial_force_right.calculate()

                        self.value = np.max([self.criterion_femur_axial_force_left.value, self.criterion_femur_axial_force_right.value])
                        self.rating = np.interp(self.value, [2.6, 6.2], [4, 0], left=4, right=0)

                    class Criterion_Femur_Axial_Force_Left(Criterion):
                        name = "Femur Axial Force Left"

                        def __init__(self, report, isomme, p):
                            super().__init__(report, isomme)

                            self.p = p

                        def calculation(self):
                            self.channel = self.isomme.get_channel(f"?{self.p}FEMRLE00??FOZB")
                            self.value = abs(min(self.channel.get_data(unit="kN")))

                    class Criterion_Femur_Axial_Force_Right(Criterion):
                        name = "Femur Axial Force Right"

                        def __init__(self, report, isomme, p):
                            super().__init__(report, isomme)

                            self.p = p

                        def calculation(self):
                            self.channel = self.isomme.get_channel(f"?{self.p}FEMRRI00??FOZB")
                            self.value = abs(min(self.channel.get_data(unit="kN")))

                class Criterion_Submarining(Criterion):
                    name = "Submarining"
                    submarining: bool = False

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                    def calculation(self):
                        self.value = self.submarining
                        self.rating = -4 if self.submarining else 0

        class Criterion_DoorOpeningDuringImpact(Criterion):
            name: str = "Door Opening During Impact"
            door_opening_during_impact: bool = False

            def calculation(self):
                self.value = self.door_opening_during_impact
                self.rating = -1 if self.door_opening_during_impact else 0

    class Page_Driver_Result_Table(Page_Result_Table):
        name: str = "Driver Result Table"
        title: str = "Driver Result"
        table_content: dict

        # TODO: Ähnlich wie report.print_results() --> systematisieren und code reduzieren
        #  als Input nur Criterion levels (1=nur subcriteria, 2=sub und subsubcriteria)
        #   name und titel automtisch aus Criteria bestimmen

        def __init__(self, report):
            super().__init__(report)
            self.table_content = {
                "Head": [f"{self.report.criterion_master[isomme].criterion_driver.criterion_head.rating:.0f}" for isomme in self.report.isomme_list],
                "Neck": [f"{self.report.criterion_master[isomme].criterion_driver.criterion_neck.rating:.0f}" for isomme in self.report.isomme_list],
                "Chest": [f"{self.report.criterion_master[isomme].criterion_driver.criterion_chest.rating:.0f}" for isomme in self.report.isomme_list],
                "Femur": [f"{self.report.criterion_master[isomme].criterion_driver.criterion_femur.rating:.0f}" for isomme in self.report.isomme_list],
                "Total": [f"{self.report.criterion_master[isomme].criterion_driver.rating:.0f}" for isomme in self.report.isomme_list],
            }

    class Page_Driver_Result_Values_Table(Page_Result_Table):
        name: str = "Driver Result Values Table"
        title: str = "Driver Result Values"
        table_content: dict

        def __init__(self, report):
            super().__init__(report)
            # TODO: add units
            self.table_content = {
                "Head - hard contact": [f"{self.report.criterion_master[isomme].criterion_driver.criterion_head.hard_contact}" for isomme in self.report.isomme_list],
                "Head - HIC15": [f"{self.report.criterion_master[isomme].criterion_driver.criterion_head.criterion_hic_15.value:.2f}" for isomme in self.report.isomme_list],
                "Head - a3ms [g]": [f"{self.report.criterion_master[isomme].criterion_driver.criterion_head.criterion_head_a3ms.value:.2f}" for isomme in self.report.isomme_list],

                "Neck - My extension [Nm]": [f"{self.report.criterion_master[isomme].criterion_driver.criterion_neck.criterion_my_extension.value:.2f}" for isomme in self.report.isomme_list],
                "Neck - Fz tension": [f"{self.report.criterion_master[isomme].criterion_driver.criterion_neck.criterion_fz_tension.value:.2f}" for isomme in self.report.isomme_list],
                "Neck - Fx shear": [f"{self.report.criterion_master[isomme].criterion_driver.criterion_neck.criterion_fx_shear.value:.2f}" for isomme in self.report.isomme_list],

                "Chest - Deflection [mm]": [f"{self.report.criterion_master[isomme].criterion_driver.criterion_chest.criterion_chest_deflection.value:.2f}" for isomme in self.report.isomme_list],
                "Chest - VC [m/s]": [f"{self.report.criterion_master[isomme].criterion_driver.criterion_chest.criterion_chest_vc.value:.2f}" for isomme in self.report.isomme_list],

                "Femur - Axial Force Left": [f"{self.report.criterion_master[isomme].criterion_driver.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_left.value:.2f}" for isomme in self.report.isomme_list],
                "Femur - Axial Force Right": [f"{self.report.criterion_master[isomme].criterion_driver.criterion_femur.criterion_femur_axial_force.criterion_femur_axial_force_right.value:.2f}" for isomme in self.report.isomme_list],
            }

    class Page_Driver_Head_Acceleration(Page_Plot_nxn):
        name: str = "Driver Head Acceleration"
        title: str = "Driver Head Acceleration"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report):
            super().__init__(report)
            self.codes = {isomme: [f"1{self.report.criterion_master[isomme].p_driver}HEAD??????AC{xyzr}A" for xyzr in "XYZR"] for isomme in self.report.isomme_list}

    class Page_Driver_Neck_Load(Page_Plot_nxn):
        name: str = "Driver Neck Load"
        title: str = "Driver Neck Load"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = False

        def __init__(self, report):
            super().__init__(report)
            self.codes = {isomme: [f"1{self.report.criterion_master[isomme].p_driver}NECKUP00??MOYB",
                                   f"1{self.report.criterion_master[isomme].p_driver}NECKUP00??FOZA",
                                   f"1{self.report.criterion_master[isomme].p_driver}NECKUP00??FOXA"] for isomme in self.report.isomme_list}

    class Page_Driver_Chest_Deflection(Page_Plot_nxn):
        name: str = "Driver Chest Deflection"
        title: str = "Driver Chest Deflection"
        nrows: int = 1
        ncols: int = 2

        def __init__(self, report):
            super().__init__(report)
            self.codes = {isomme: [f"1{self.report.criterion_master[isomme].p_driver}CHST000???DSXC",
                                   f"1{self.report.criterion_master[isomme].p_driver}VCCR000???VEXX"] for isomme in self.report.isomme_list}

    class Page_Driver_Femur_Axial_Force(Page_Plot_nxn):
        name: str = "Driver Femur Axial Force"
        title: str = "Driver Femur Axial Force"
        nrows: int = 1
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report):
            super().__init__(report)
            self.codes = {isomme: [f"1{self.report.criterion_master[isomme].p_driver}FEMRLE00??FOZB",
                                   f"1{self.report.criterion_master[isomme].p_driver}FEMRRI00??FOZB"] for isomme in self.report.isomme_list}

    class Page_Front_Passenger_Result_Table(Page_Result_Table):
        name: str = "Front Passenger Result Table"
        title: str = "Front Passenger Result"
        table_content: dict

        def __init__(self, report):
            super().__init__(report)
            self.table_content = {
                "Head": [f"{self.report.criterion_master[isomme].criterion_front_passenger.criterion_head.rating:.0f}" for isomme in self.report.isomme_list],
                "Neck": [f"{self.report.criterion_master[isomme].criterion_front_passenger.criterion_neck.rating:.0f}" for isomme in self.report.isomme_list],
                "Chest": [f"{self.report.criterion_master[isomme].criterion_front_passenger.criterion_chest.rating:.0f}" for isomme in self.report.isomme_list],
                "Femur": [f"{self.report.criterion_master[isomme].criterion_front_passenger.criterion_femur.rating:.0f}" for isomme in self.report.isomme_list],
                "Total": [f"{self.report.criterion_master[isomme].criterion_front_passenger.rating:.0f}" for isomme in self.report.isomme_list],
            }

    class Page_Front_Passenger_Head_Acceleration(Page_Plot_nxn):
        name: str = "Front Passenger Head Acceleration"
        title: str = "Front Passenger Head Acceleration"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report):
            super().__init__(report)
            self.codes = {isomme: [f"1{self.report.criterion_master[isomme].p_front_passenger}HEAD??????AC{xyzr}A" for xyzr in "XYZR"] for isomme in self.report.isomme_list}

    class Page_Front_Passenger_Neck_Load(Page_Plot_nxn):
        name: str = "Front Passenger Neck Load"
        title: str = "Front Passenger Neck Load"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = False

        def __init__(self, report):
            super().__init__(report)
            self.codes = {isomme: [f"1{self.report.criterion_master[isomme].p_front_passenger}NECKUP00??MOYB",
                                   f"1{self.report.criterion_master[isomme].p_front_passenger}NECKUP00??FOZA",
                                   f"1{self.report.criterion_master[isomme].p_front_passenger}NECKUP00??FOXA"] for isomme in self.report.isomme_list}

    class Page_Front_Passenger_Chest_Deflection(Page_Plot_nxn):
        name: str = "Front Passenger Chest Deflection"
        title: str = "Front Passenger Chest Deflection"
        nrows: int = 1
        ncols: int = 1

        def __init__(self, report):
            super().__init__(report)
            self.codes = {isomme: [f"1{self.report.criterion_master[isomme].p_front_passenger}CHST000???DSXC"] for isomme in self.report.isomme_list}

    class Page_Front_Passenger_Femur_Axial_Force(Page_Plot_nxn):
        name: str = "Front Passenger Femur Axial Force"
        title: str = "Front Passenger Femur Axial Force"
        nrows: int = 1
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report):
            super().__init__(report)
            self.codes = {isomme: [f"1{self.report.criterion_master[isomme].p_front_passenger}FEMRLE00??FOZB", f"1{self.report.criterion_master[isomme].p_front_passenger}FEMRRI00??FOZB"] for isomme in self.report.isomme_list}

    class Page_Rear_Passenger_Result_Table(Page_Result_Table):
        name: str = "Rear Passenger Result Table"
        title: str = "Rear Passenger Result"
        table_content: dict

        def __init__(self, report):
            super().__init__(report)
            self.table_content = {
                "Head": [f"{self.report.criterion_master[isomme].criterion_rear_passenger.criterion_head.rating:.0f}" for isomme in self.report.isomme_list],
                "Neck": [f"{self.report.criterion_master[isomme].criterion_rear_passenger.criterion_neck.rating:.0f}" for isomme in self.report.isomme_list],
                "Chest": [f"{self.report.criterion_master[isomme].criterion_rear_passenger.criterion_chest.rating:.0f}" for isomme in self.report.isomme_list],
                "Femur": [f"{self.report.criterion_master[isomme].criterion_rear_passenger.criterion_femur.rating:.0f}" for isomme in self.report.isomme_list],
                "Total": [f"{self.report.criterion_master[isomme].criterion_rear_passenger.rating:.0f}" for isomme in self.report.isomme_list],
            }

    class Page_Rear_Passenger_Head_Acceleration(Page_Plot_nxn):
        name: str = "Rear Passenger Head Acceleration"
        title: str = "Rear Passenger Head Acceleration"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report):
            super().__init__(report)
            self.codes = {isomme: [f"1{self.report.criterion_master[isomme].p_rear_passenger}HEAD??????AC{xyzr}A" for xyzr in "XYZR"] for isomme in self.report.isomme_list}

    class Page_Rear_Passenger_Neck_Load(Page_Plot_nxn):
        name: str = "Rear Passenger Neck Load"
        title: str = "Rear Passenger Neck Load"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = False

        def __init__(self, report):
            super().__init__(report)
            self.codes = {isomme: [f"1{self.report.criterion_master[isomme].p_rear_passenger}NECKUP00??MOYB",
                                   f"1{self.report.criterion_master[isomme].p_rear_passenger}NECKUP00??FOZA",
                                   f"1{self.report.criterion_master[isomme].p_rear_passenger}NECKUP00??FOXA"] for isomme in self.report.isomme_list}

    class Page_Rear_Passenger_Chest_Deflection(Page_Plot_nxn):
        name: str = "Rear Passenger Chest Deflection"
        title: str = "Rear Passenger Chest Deflection"
        nrows: int = 1
        ncols: int = 1

        def __init__(self, report):
            super().__init__(report)
            self.codes = {isomme: [f"1{self.report.criterion_master[isomme].p_rear_passenger}CHST000???DSXC"] for isomme in self.report.isomme_list}

    class Page_Rear_Passenger_Femur_Axial_Force(Page_Plot_nxn):
        name: str = "Rear Passenger Femur Axial Force"
        title: str = "Rear Passenger Femur Axial Force"
        nrows: int = 1
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report):
            super().__init__(report)
            self.codes = {isomme: [f"1{self.report.criterion_master[isomme].p_rear_passenger}FEMRLE00??FOZB",
                                   f"1{self.report.criterion_master[isomme].p_rear_passenger}FEMRRI00??FOZB"] for isomme in self.report.isomme_list}
