from pyisomme.unit import Unit, g0
from pyisomme.report.page import Page_Cover, Page_Criterion_Rating_Table, Page_Criterion_Values_Chart, Page_Criterion_Values_Table
from pyisomme.report.report import Report
from pyisomme.report.criterion import Criterion
from pyisomme.report.un.limits import Limit_Fail, Limit_Pass
from pyisomme.report.euro_ncap.frontal_50kmh import EuroNCAP_Frontal_50kmh
from pyisomme.report.euro_ncap.frontal_mpdb import EuroNCAP_Frontal_MPDB

import logging
import numpy as np


logger = logging.getLogger(__name__)


class UN_Frontal_50kmh_R137(Report):
    name = "UN-R137 | Frontal-Impact against Rigid Wall with 100 % Overlap at 50 km/h"
    protocol = "12.09.2023"
    protocols = {
        "22.06.2016": "Revision 2 (22.06.2016) [references/UN-R137/R137e.pdf]",
        "12.09.2023": "Revision 2 (12.09.2023) [references/UN-R137/B04.80k7388018sqd01x91957452w3utcf63832377452.pdf]"
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pages = [
            Page_Cover(self),
            self.Page_Rating_Table(self),

            self.Page_Driver_Result_Values_Chart(self),
            self.Page_Driver_Values_Table(self),
            self.Page_Driver_Head_Acceleration(self),
            self.Page_Driver_Neck_Load(self),
            self.Page_Driver_Chest_Deflection(self),
            self.Page_Driver_Femur_Axial_Force(self),

            self.Page_Passenger_Result_Values_Chart(self),
            self.Page_Passenger_Values_Table(self),
            self.Page_Passenger_Head_Acceleration(self),
            self.Page_Passenger_Neck_Load(self),
            self.Page_Passenger_Chest_Deflection(self),
            self.Page_Passenger_Femur_Axial_Force(self),
        ]

    class Criterion_Overall(Criterion):
        name = "Overall"
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

        def calculation(self) -> None:
            self.criterion_driver.calculate()
            self.criterion_passenger.calculate()

            self.rating = np.min([
                self.criterion_driver.rating,
                self.criterion_passenger.rating
            ])

        class Criterion_Driver(Criterion):
            name = "Driver"

            def __init__(self, report, isomme, p):
                super().__init__(report, isomme)

                self.p = p

                self.criterion_hpc36 = self.Criterion_HPC36(report, isomme, p=self.p)
                self.criterion_head_a3ms = self.Criterion_Head_a3ms(report, isomme, p=self.p)
                self.criterion_neck_fz_tension = self.Criterion_Neck_Fz_tension(report, isomme, p=self.p)
                self.criterion_neck_fx_shear = self.Criterion_Neck_Fx_shear(report, isomme, p=self.p)
                self.criterion_neck_my_extension = self.Criterion_Neck_My_extension(report, isomme, p=self.p)
                self.criterion_chest_deflection = self.Criterion_Chest_Deflection(report, isomme, p=self.p)
                self.criterion_chest_vc = self.Criterion_Chest_VC(report, isomme, p=self.p)
                self.criterion_femur_compression = self.Criterion_Femur_Compression(report, isomme, p=self.p)

            def calculation(self) -> None:
                self.criterion_hpc36.calculate()
                self.criterion_head_a3ms.calculate()
                self.criterion_neck_fz_tension.calculate()
                self.criterion_neck_fx_shear.calculate()
                self.criterion_neck_my_extension.calculate()
                self.criterion_chest_deflection.calculate()
                self.criterion_chest_vc.calculate()
                self.criterion_femur_compression.calculate()

                self.rating = np.min([
                    self.criterion_hpc36.rating,
                    self.criterion_head_a3ms.rating,
                    self.criterion_neck_fz_tension.rating,
                    self.criterion_neck_fx_shear.rating,
                    self.criterion_neck_my_extension.rating,
                    self.criterion_chest_deflection.rating,
                    self.criterion_chest_vc.rating,
                    self.criterion_femur_compression.rating,
                ])

            class Criterion_HPC36(Criterion):
                name = "Head Performance Criterion (HPC 36)"
                head_contact: bool = True

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Pass([f"?{self.p}HICR0036??00RX", f"?{self.p}HICRCG36??00RX"], func=lambda x: 1000, y_unit=1, upper=True),
                        Limit_Fail([f"?{self.p}HICR0036??00RX", f"?{self.p}HICRCG36??00RX"], func=lambda x: 1000, y_unit=1, lower=True),
                    ])

                def calculation(self):
                    if self.head_contact:
                        self.channel = self.isomme.get_channel(f"?{self.p}HICR0036??00RX", f"?{self.p}HICRCG36??00RX")
                        self.value = self.channel.get_data()[0]
                        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                        self.color = self.limits.get_limit_min_color(self.channel)
                    else:
                        self.rating = True
                        self.color = Limit_Pass.color

            class Criterion_Head_a3ms(Criterion):
                name = "Head a3ms"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Pass([f"?{self.p}HEAD003C??ACR?", f"?{self.p}HEADCG3C??ACR?"], func=lambda x: 80, y_unit=Unit(g0), upper=True),
                        Limit_Fail([f"?{self.p}HEAD003C??ACR?", f"?{self.p}HEADCG3C??ACR?"], func=lambda x: 80, y_unit=Unit(g0), lower=True),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}HEAD003C??ACRX", f"?{self.p}HEADCG3C??ACRX")
                    self.value = self.channel.get_data(unit=g0)[0]
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Neck_Fz_tension(Criterion):
                name = "Neck Fz tension"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Pass([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 3.3, y_unit="kN", upper=True),
                        Limit_Fail([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 3.3, y_unit="kN", lower=True),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??FOZA").convert_unit("kN")
                    self.value = np.max(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Neck_Fx_shear(Criterion):
                name = "Neck Fx shear"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Fail([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 3.1, y_unit="kN", lower=True),
                        Limit_Pass([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 3.1, y_unit="kN", upper=True),
                        Limit_Pass([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -3.1, y_unit="kN", lower=True),
                        Limit_Fail([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -3.1, y_unit="kN", upper=True),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??FOXA").convert_unit("kN")
                    self.value = self.channel.get_data(unit="kN")[np.argmax(np.abs(self.channel.get_data()))]
                    self.rating = self.limits.get_limit_min_rating(self.channel)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Neck_My_extension(Criterion):
                name = "Neck My extension"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Pass([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -57, y_unit="Nm", lower=True),
                        Limit_Fail([f"?{self.p}NECKUP00??MOY?"], func=lambda x: -57, y_unit="Nm", upper=True),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??MOYB")
                    self.value = np.min(self.channel.get_data(unit="Nm"))
                    self.rating = self.limits.get_limit_min_rating(self.channel)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Chest_Deflection(Criterion):
                name = "Chest Deflection"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Fail([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -42, y_unit="mm", upper=True),
                        Limit_Pass([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -42, y_unit="mm", lower=True),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}CHST0000??DSXC").convert_unit("mm")
                    self.value = np.min(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Chest_VC(Criterion):
                name = "Chest VC"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Fail([f"?{self.p}VCCR000[03]??VEX?"], func=lambda x: -1, y_unit="m/s", upper=True),
                        Limit_Pass([f"?{self.p}VCCR000[03]??VEX?"], func=lambda x: -1, y_unit="m/s", lower=True),
                        Limit_Pass([f"?{self.p}VCCR000[03]??VEX?"], func=lambda x: 1, y_unit="m/s", upper=True),
                        Limit_Fail([f"?{self.p}VCCR000[03]??VEX?"], func=lambda x: 1, y_unit="m/s", lower=True),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}VCCR0003??VEXC", f"?{self.p}VCCR0000??VEXC").convert_unit("m/s")
                    self.value = np.min(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Femur_Compression(Criterion):
                name = "Femur Compression"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Fail([f"?{self.p}FEMR??00??FOZ?"], func=lambda x: -9.07, y_unit="kN", x_unit="ms", upper=True),
                        Limit_Pass([f"?{self.p}FEMR??00??FOZ?"], func=lambda x: -9.07, y_unit="kN", x_unit="ms", lower=True),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}FEMR0000??FOZB").convert_unit("kN")
                    self.value = self.limits.get_limit_min_y(self.channel)
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Passenger(Criterion):
            name = "Passenger"

            def __init__(self, report, isomme, p):
                super().__init__(report, isomme)

                self.p = p

                self.criterion_hpc36 = self.report.Criterion_Overall.Criterion_Driver.Criterion_HPC36(report, isomme, p=self.p)
                self.criterion_head_a3ms = self.report.Criterion_Overall.Criterion_Driver.Criterion_Head_a3ms(report, isomme, p=self.p)
                self.criterion_neck_fz_tension = self.Criterion_Neck_Fz_tension(report, isomme, p=self.p)
                self.criterion_neck_fx_shear = self.Criterion_Neck_Fx_shear(report, isomme, p=self.p)
                self.criterion_neck_my_extension = self.report.Criterion_Overall.Criterion_Driver.Criterion_Neck_My_extension(report, isomme, p=self.p)
                self.criterion_chest_deflection = self.Criterion_Chest_Deflection(report, isomme, p=self.p)
                self.criterion_chest_vc = self.report.Criterion_Overall.Criterion_Driver.Criterion_Chest_VC(report, isomme, p=self.p)
                self.criterion_femur_compression = self.Criterion_Femur_Compression(report, isomme, p=self.p)

            def calculation(self) -> None:
                self.criterion_hpc36.calculate()
                self.criterion_head_a3ms.calculate()
                self.criterion_neck_fz_tension.calculate()
                self.criterion_neck_fx_shear.calculate()
                self.criterion_neck_my_extension.calculate()
                self.criterion_chest_deflection.calculate()
                self.criterion_chest_vc.calculate()
                self.criterion_femur_compression.calculate()

                self.rating = np.min([
                    self.criterion_hpc36.rating,
                    self.criterion_head_a3ms.rating,
                    self.criterion_neck_fz_tension.rating,
                    self.criterion_neck_fx_shear.rating,
                    self.criterion_neck_my_extension.rating,
                    self.criterion_chest_deflection.rating,
                    self.criterion_chest_vc.rating,
                    self.criterion_femur_compression.rating,
                ])

            class Criterion_Neck_Fz_tension(Criterion):
                name = "Neck Fz tension"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Pass([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 2.9, y_unit="kN", upper=True),
                        Limit_Fail([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 2.9, y_unit="kN", lower=True),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??FOZA").convert_unit("kN")
                    self.value = np.max(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Neck_Fx_shear(Criterion):
                name = "Neck Fx shear"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Fail([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 2.9, y_unit="kN", lower=True),
                        Limit_Pass([f"?{self.p}NECKUP00??FOX?"], func=lambda x: 2.9, y_unit="kN", upper=True),
                        Limit_Pass([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -2.9, y_unit="kN", lower=True),
                        Limit_Fail([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -2.9, y_unit="kN", upper=True),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??FOXA").convert_unit("kN")
                    self.value = self.channel.get_data(unit="kN")[np.argmax(np.abs(self.channel.get_data()))]
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Chest_Deflection(Criterion):
                name = "Chest Deflection"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Fail([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -42 if self.report.protocol == "22.06.2016" else -34, y_unit="mm", upper=True),
                        Limit_Pass([f"?{self.p}CHST000[03]??DSX?"], func=lambda x: -42 if self.report.protocol == "22.06.2016" else -34, y_unit="mm", lower=True),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}CHST0000??DSXC").convert_unit("mm")
                    self.value = np.min(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Femur_Compression(Criterion):
                name = "Femur Compression"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Fail([f"?{self.p}FEMR??00??FOZ?"], func=lambda x: -7, y_unit="kN", x_unit="ms", upper=True),
                        Limit_Pass([f"?{self.p}FEMR??00??FOZ?"], func=lambda x: -7, y_unit="kN", x_unit="ms", lower=True),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}FEMR0000??FOZB").convert_unit("kN")
                    self.value = self.limits.get_limit_min_y(self.channel)
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

    class Page_Rating_Table(Page_Criterion_Rating_Table):
        name = "Rating"
        title = "Rating"
        cell_text = staticmethod(lambda criterion: f"{criterion.rating:.0f}")

        def __init__(self, report):
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_driver,
                self.report.criterion_overall[isomme].criterion_passenger,
                self.report.criterion_overall[isomme],
            ] for isomme in self.report.isomme_list}

    class Page_Driver_Result_Values_Chart(Page_Criterion_Values_Chart):
        name = "Driver Result Values Chart"
        title = "Driver Result"

        def __init__(self, report):
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_driver.criterion_hpc36,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_a3ms,
                self.report.criterion_overall[isomme].criterion_driver.criterion_neck_fz_tension,
                self.report.criterion_overall[isomme].criterion_driver.criterion_neck_fx_shear,
                self.report.criterion_overall[isomme].criterion_driver.criterion_neck_my_extension,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest_deflection,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest_vc,
                self.report.criterion_overall[isomme].criterion_driver.criterion_femur_compression,
            ] for isomme in self.report.isomme_list}

    class Page_Driver_Values_Table(Page_Criterion_Values_Table):
        name = "Driver Values Table"
        title = "Driver Values"

        def __init__(self, report):
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_driver.criterion_hpc36,
                self.report.criterion_overall[isomme].criterion_driver.criterion_head_a3ms,
                self.report.criterion_overall[isomme].criterion_driver.criterion_neck_fz_tension,
                self.report.criterion_overall[isomme].criterion_driver.criterion_neck_fx_shear,
                self.report.criterion_overall[isomme].criterion_driver.criterion_neck_my_extension,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest_deflection,
                self.report.criterion_overall[isomme].criterion_driver.criterion_chest_vc,
                self.report.criterion_overall[isomme].criterion_driver.criterion_femur_compression,
            ] for isomme in self.report.isomme_list}

    class Page_Driver_Head_Acceleration(EuroNCAP_Frontal_50kmh.Page_Driver_Head_Acceleration):
        pass

    class Page_Driver_Neck_Load(EuroNCAP_Frontal_50kmh.Page_Driver_Neck_Load):
        pass

    class Page_Driver_Chest_Deflection(EuroNCAP_Frontal_50kmh.Page_Driver_Chest_Deflection):
        pass

    class Page_Driver_Femur_Axial_Force(EuroNCAP_Frontal_50kmh.Page_Driver_Femur_Axial_Force):
        pass

    class Page_Passenger_Result_Values_Chart(Page_Criterion_Values_Chart):
        name = "Passenger Result Values Chart"
        title = "Passenger Result"

        def __init__(self, report):
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_passenger.criterion_hpc36,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_head_a3ms,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_neck_fz_tension,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_neck_fx_shear,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_neck_my_extension,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_chest_deflection,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_chest_vc,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_femur_compression,
            ] for isomme in self.report.isomme_list}

    class Page_Passenger_Values_Table(Page_Criterion_Values_Table):
        name: str = "Passenger Values Table"
        title: str = "Passenger Values"

        def __init__(self, report):
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_passenger.criterion_hpc36,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_head_a3ms,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_neck_fz_tension,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_neck_fx_shear,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_neck_my_extension,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_chest_deflection,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_chest_vc,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_femur_compression,
            ] for isomme in self.report.isomme_list}

    class Page_Passenger_Head_Acceleration(EuroNCAP_Frontal_MPDB.Page_Passenger_Head_Acceleration):
        pass

    class Page_Passenger_Neck_Load(EuroNCAP_Frontal_MPDB.Page_Passenger_Neck_Load):
        pass

    class Page_Passenger_Chest_Deflection(EuroNCAP_Frontal_MPDB.Page_Passenger_Chest_Deflection):
        pass

    class Page_Passenger_Femur_Axial_Force(EuroNCAP_Frontal_MPDB.Page_Passenger_Femur_Axial_Force):
        pass
