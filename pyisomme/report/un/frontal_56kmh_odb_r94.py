from pyisomme.report.euro_ncap import EuroNCAP_Frontal_50kmh, EuroNCAP_Frontal_MPDB
from pyisomme.report.page import Page_Cover, Page_Criterion_Rating_Table, Page_Criterion_Values_Chart, Page_Criterion_Values_Table
from pyisomme.report.report import Report
from pyisomme.report.criterion import Criterion
from pyisomme.report.un.limits import Limit_Fail, Limit_Pass
from pyisomme.report.un.frontal_50kmh_r137 import UN_Frontal_50kmh_R137

import logging
import numpy as np


logger = logging.getLogger(__name__)


class UN_Frontal_56kmh_ODB_R94(Report):
    name = "UN-R94 | Frontal-Impact against ODB with 40 % Overlap at 56 km/h"
    protocol = "29.12.2022"
    protocols = {
        "29.12.2022": "Revision 4 (29.12.2022) [references/UN-R94/B04.ckg738531jagx232x0m74928e357ft63809066928.pdf]",
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
            self.Page_Driver_Knee_Slider_Compression(self),
            self.Page_Driver_Tibia_Compression(self),
            self.Page_Driver_Tibia_Index(self),

            self.Page_Passenger_Result_Values_Chart(self),
            self.Page_Passenger_Values_Table(self),
            self.Page_Passenger_Head_Acceleration(self),
            self.Page_Passenger_Neck_Load(self),
            self.Page_Passenger_Chest_Deflection(self),
            self.Page_Passenger_Femur_Axial_Force(self),
            self.Page_Passenger_Knee_Slider_Compression(self),
            self.Page_Passenger_Tibia_Compression(self),
            self.Page_Passenger_Tibia_Index(self),
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
                self.criterion_tibia_compression = self.Criterion_Tibia_Compression(report, isomme, p=self.p)
                self.criterion_tibia_index = self.Criterion_Tibia_Index(report, isomme, p=self.p)
                self.criterion_knee_slider_compression = self.Criterion_Knee_Slider_Compression(report, isomme, p=self.p)

            def calculation(self) -> None:
                self.criterion_hpc36.calculate()
                self.criterion_head_a3ms.calculate()
                self.criterion_neck_fz_tension.calculate()
                self.criterion_neck_fx_shear.calculate()
                self.criterion_neck_my_extension.calculate()
                self.criterion_chest_deflection.calculate()
                self.criterion_chest_vc.calculate()
                self.criterion_femur_compression.calculate()
                self.criterion_tibia_compression.calculate()
                self.criterion_tibia_index.calculate()
                self.criterion_knee_slider_compression.calculate()

                self.rating = np.min([
                    self.criterion_hpc36.rating,
                    self.criterion_head_a3ms.rating,
                    self.criterion_neck_fz_tension.rating,
                    self.criterion_neck_fx_shear.rating,
                    self.criterion_neck_my_extension.rating,
                    self.criterion_chest_deflection.rating,
                    self.criterion_chest_vc.rating,
                    self.criterion_femur_compression.rating,
                    self.criterion_tibia_compression.rating,
                    self.criterion_tibia_index.rating,
                    self.criterion_knee_slider_compression.rating
                ])

            class Criterion_HPC36(UN_Frontal_50kmh_R137.Criterion_Overall.Criterion_Driver.Criterion_HPC36):
                pass

            class Criterion_Head_a3ms(UN_Frontal_50kmh_R137.Criterion_Overall.Criterion_Driver.Criterion_Head_a3ms):
                pass

            class Criterion_Neck_Fz_tension(Criterion):
                name = "Neck Fz tension"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Pass([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: np.interp(x, [0, 35, 60], [3.3, 2.9, 1.1]), x_unit="ms", y_unit="kN", upper=True),
                        Limit_Fail([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: np.interp(x, [0, 35, 60], [3.3, 2.9, 1.1]), x_unit="ms", y_unit="kN", lower=True),
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
                        Limit_Fail([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -np.interp(x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1]), x_unit="ms", y_unit="kN", upper=True),
                        Limit_Pass([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -np.interp(x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1]), x_unit="ms", y_unit="kN", lower=True),
                        Limit_Pass([f"?{self.p}NECKUP00??FOX?"], func=lambda x: np.interp(x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1]), x_unit="ms", y_unit="kN", upper=True),
                        Limit_Fail([f"?{self.p}NECKUP00??FOX?"], func=lambda x: np.interp(x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1]), x_unit="ms", y_unit="kN", lower=True),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??FOXA").convert_unit("kN")
                    self.value = self.channel.get_data(unit="kN")[np.argmax(np.abs(self.channel.get_data()))]
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Neck_My_extension(UN_Frontal_50kmh_R137.Criterion_Overall.Criterion_Driver.Criterion_Neck_My_extension):
                pass

            class Criterion_Chest_Deflection(UN_Frontal_50kmh_R137.Criterion_Overall.Criterion_Driver.Criterion_Chest_Deflection):
                pass

            class Criterion_Chest_VC(UN_Frontal_50kmh_R137.Criterion_Overall.Criterion_Driver.Criterion_Chest_VC):
                pass

            class Criterion_Femur_Compression(Criterion):
                name = "Femur Compression"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Fail([f"?{self.p}FEMR??00??FOZ?"], func=lambda x: np.interp(x, [0, 10], [-9.07, -7.58]), y_unit="kN", x_unit="ms", upper=True),
                        Limit_Pass([f"?{self.p}FEMR??00??FOZ?"], func=lambda x: np.interp(x, [0, 10], [-9.07, -7.58]), y_unit="kN", x_unit="ms", lower=True),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}FEMR0000??FOZB").convert_unit("kN")
                    self.value = self.limits.get_limit_min_y(self.channel)
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Tibia_Compression(Criterion):
                name = "Tibia Compression"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Fail([f"?{self.p}TIBI??????FOZ?"], func=lambda x: -8, y_unit="kN", upper=True),
                        Limit_Pass([f"?{self.p}TIBI??????FOZ?"], func=lambda x: -8, y_unit="kN", lower=True),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}TIBI0000??FOZB").convert_unit("kN")
                    self.value = np.min(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Tibia_Index(Criterion):
                name = "Tibia Index"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Pass([f"?{self.p}TIIN??????000?"], func=lambda x: 1.3, y_unit="1", upper=True),
                        Limit_Fail([f"?{self.p}TIIN??????000?"], func=lambda x: 1.3, y_unit="1", lower=True),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}TIIN0000??000B")
                    self.value = np.max(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Knee_Slider_Compression(Criterion):
                name = "Knee Slider Compression"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Fail([f"?{self.p}KNSL??00??DSX?"], func=lambda x: -15, y_unit="mm", upper=True),
                        Limit_Pass([f"?{self.p}KNSL??00??DSX?"], func=lambda x: -15, y_unit="mm", lower=True),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}KNSL0000??DSXC").convert_unit("mm")
                    self.value = np.min(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Passenger(Criterion):
            name = "Passenger"

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
                self.criterion_tibia_compression = self.Criterion_Tibia_Compression(report, isomme, p=self.p)
                self.criterion_tibia_index = self.Criterion_Tibia_Index(report, isomme, p=self.p)
                self.criterion_knee_slider_compression = self.Criterion_Knee_Slider_Compression(report, isomme, p=self.p)

            def calculation(self) -> None:
                self.criterion_hpc36.calculate()
                self.criterion_head_a3ms.calculate()
                self.criterion_neck_fz_tension.calculate()
                self.criterion_neck_fx_shear.calculate()
                self.criterion_neck_my_extension.calculate()
                self.criterion_chest_deflection.calculate()
                self.criterion_chest_vc.calculate()
                self.criterion_femur_compression.calculate()
                self.criterion_tibia_compression.calculate()
                self.criterion_tibia_index.calculate()
                self.criterion_knee_slider_compression.calculate()

                self.rating = np.min([
                    self.criterion_hpc36.rating,
                    self.criterion_head_a3ms.rating,
                    self.criterion_neck_fz_tension.rating,
                    self.criterion_neck_fx_shear.rating,
                    self.criterion_neck_my_extension.rating,
                    self.criterion_chest_deflection.rating,
                    self.criterion_chest_vc.rating,
                    self.criterion_femur_compression.rating,
                    self.criterion_tibia_compression.rating,
                    self.criterion_tibia_index.rating,
                    self.criterion_knee_slider_compression.rating
                ])

            class Criterion_HPC36(UN_Frontal_50kmh_R137.Criterion_Overall.Criterion_Driver.Criterion_HPC36):
                pass

            class Criterion_Head_a3ms(UN_Frontal_50kmh_R137.Criterion_Overall.Criterion_Driver.Criterion_Head_a3ms):
                pass

            class Criterion_Neck_Fz_tension(Criterion):
                name = "Neck Fz tension"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Pass([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: np.interp(x, [0, 35, 60], [3.3, 2.9, 1.1]), x_unit="ms", y_unit="kN", upper=True),
                        Limit_Fail([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: np.interp(x, [0, 35, 60], [3.3, 2.9, 1.1]), x_unit="ms", y_unit="kN", lower=True),
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
                        Limit_Fail([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -np.interp(x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1]), x_unit="ms", y_unit="kN", upper=True),
                        Limit_Pass([f"?{self.p}NECKUP00??FOX?"], func=lambda x: -np.interp(x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1]), x_unit="ms", y_unit="kN", lower=True),
                        Limit_Pass([f"?{self.p}NECKUP00??FOX?"], func=lambda x: np.interp(x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1]), x_unit="ms", y_unit="kN", upper=True),
                        Limit_Fail([f"?{self.p}NECKUP00??FOX?"], func=lambda x: np.interp(x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1]), x_unit="ms", y_unit="kN", lower=True),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??FOXA").convert_unit("kN")
                    self.value = self.channel.get_data(unit="kN")[np.argmax(np.abs(self.channel.get_data()))]
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Neck_My_extension(UN_Frontal_50kmh_R137.Criterion_Overall.Criterion_Driver.Criterion_Neck_My_extension):
                pass

            class Criterion_Chest_Deflection(UN_Frontal_50kmh_R137.Criterion_Overall.Criterion_Driver.Criterion_Chest_Deflection):
                pass

            class Criterion_Chest_VC(UN_Frontal_50kmh_R137.Criterion_Overall.Criterion_Driver.Criterion_Chest_VC):
                pass

            class Criterion_Femur_Compression(Criterion):
                name = "Femur Compression"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Fail([f"?{self.p}FEMR??00??FOZ?"], func=lambda x: np.interp(x, [0, 10], [-9.07, -7.58]), y_unit="kN", x_unit="ms", upper=True),
                        Limit_Pass([f"?{self.p}FEMR??00??FOZ?"], func=lambda x: np.interp(x, [0, 10], [-9.07, -7.58]), y_unit="kN", x_unit="ms", lower=True),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}FEMR0000??FOZB").convert_unit("kN")
                    self.value = self.limits.get_limit_min_y(self.channel)
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Tibia_Compression(Criterion):
                name = "Tibia Compression"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Fail([f"?{self.p}TIBI??????FOZ?"], func=lambda x: -8, y_unit="kN", upper=True),
                        Limit_Pass([f"?{self.p}TIBI??????FOZ?"], func=lambda x: -8, y_unit="kN", lower=True),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}TIBI0000??FOZB").convert_unit("kN")
                    self.value = np.min(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Tibia_Index(Criterion):
                name = "Tibia Index"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Pass([f"?{self.p}TIIN??????000?"], func=lambda x: 1.3, y_unit="1", upper=True),
                        Limit_Fail([f"?{self.p}TIIN??????000?"], func=lambda x: 1.3, y_unit="1", lower=True),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}TIIN0000??000B")
                    self.value = np.max(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Knee_Slider_Compression(Criterion):
                name = "Knee Slider Compression"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Fail([f"?{self.p}KNSL??00??DSX?"], func=lambda x: -15, y_unit="mm", upper=True),
                        Limit_Pass([f"?{self.p}KNSL??00??DSX?"], func=lambda x: -15, y_unit="mm", lower=True),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}KNSL0000??DSXC").convert_unit("mm")
                    self.value = np.min(self.channel.get_data())
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
                self.report.criterion_overall[isomme].criterion_driver.criterion_tibia_compression,
                self.report.criterion_overall[isomme].criterion_driver.criterion_tibia_index,
                self.report.criterion_overall[isomme].criterion_driver.criterion_knee_slider_compression,
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
                self.report.criterion_overall[isomme].criterion_driver.criterion_tibia_compression,
                self.report.criterion_overall[isomme].criterion_driver.criterion_tibia_index,
                self.report.criterion_overall[isomme].criterion_driver.criterion_knee_slider_compression,
            ] for isomme in self.report.isomme_list}

    class Page_Driver_Head_Acceleration(EuroNCAP_Frontal_50kmh.Page_Driver_Head_Acceleration):
        pass

    class Page_Driver_Neck_Load(EuroNCAP_Frontal_50kmh.Page_Driver_Neck_Load):
        pass

    class Page_Driver_Chest_Deflection(EuroNCAP_Frontal_50kmh.Page_Driver_Chest_Deflection):
        pass

    class Page_Driver_Femur_Axial_Force(EuroNCAP_Frontal_50kmh.Page_Driver_Femur_Axial_Force):
        pass

    class Page_Driver_Knee_Slider_Compression(EuroNCAP_Frontal_MPDB.Page_Driver_Knee_Slider_Compression):
        pass

    class Page_Driver_Tibia_Compression(EuroNCAP_Frontal_MPDB.Page_Driver_Tibia_Compression):
        pass

    class Page_Driver_Tibia_Index(EuroNCAP_Frontal_MPDB.Page_Driver_Tibia_Index):
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
                self.report.criterion_overall[isomme].criterion_passenger.criterion_tibia_compression,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_tibia_index,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_knee_slider_compression,
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
                self.report.criterion_overall[isomme].criterion_passenger.criterion_tibia_compression,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_tibia_index,
                self.report.criterion_overall[isomme].criterion_passenger.criterion_knee_slider_compression,
            ] for isomme in self.report.isomme_list}

    class Page_Passenger_Head_Acceleration(EuroNCAP_Frontal_MPDB.Page_Passenger_Head_Acceleration):
        pass

    class Page_Passenger_Neck_Load(EuroNCAP_Frontal_MPDB.Page_Passenger_Neck_Load):
        pass

    class Page_Passenger_Chest_Deflection(EuroNCAP_Frontal_MPDB.Page_Passenger_Chest_Deflection):
        pass

    class Page_Passenger_Femur_Axial_Force(EuroNCAP_Frontal_MPDB.Page_Passenger_Femur_Axial_Force):
        pass

    class Page_Passenger_Knee_Slider_Compression(EuroNCAP_Frontal_MPDB.Page_Passenger_Knee_Slider_Compression):
        pass

    class Page_Passenger_Tibia_Compression(EuroNCAP_Frontal_MPDB.Page_Passenger_Tibia_Compression):
        pass

    class Page_Passenger_Tibia_Index(EuroNCAP_Frontal_MPDB.Page_Passenger_Tibia_Index):
        pass
