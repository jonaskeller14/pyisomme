from pyisomme.report.page import Page_Cover, Page_Plot_nxn, Page_Criterion_Values_Chart, Page_Criterion_Values_Table
from pyisomme.report.report import Report
from pyisomme.report.criterion import Criterion
from pyisomme.report.un.limits import Limit_Fail, Limit_Pass
from pyisomme.report.un.frontal_50kmh_r137 import UN_Frontal_50kmh_R137
from pyisomme.report.un.side_pole_r135 import UN_Side_Pole_R135
from pyisomme.report.euro_ncap.side_pole import EuroNCAP_Side_Pole

import logging
import numpy as np


logger = logging.getLogger(__name__)


class UN_Side_Barrier_R95(Report):
    name = "UN-R95 | Barrier Side Impact at 50 km/h"
    protocol = "12.09.2023"
    protocols = {
        "12.09.2023": "Revision 4 (12.09.2023) [references/UN-R95/B04.qtu738801n2c4t17t97571269on1fn63832377126.pdf]"
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pages = [
            Page_Cover(self),
            self.Page_Values_Chart(self),
            self.Page_Values_Table(self),
            self.Page_Head_Acceleration(self),
            self.Page_Chest_Lateral_Deflection(self),
            self.Page_Chest_Lateral_VC(self),
            self.Page_Pubic_Symphysis_Force(self),
            self.Page_Abdomen_Force(self),
        ]

    class Criterion_Overall(Criterion):
        name = "Overall"
        p: int = 1

        def __init__(self, report, isomme):
            super().__init__(report, isomme)

            p = isomme.get_test_info("Driver position object 1")
            if p is not None:
                self.p = int(p)

            self.criterion_dummy = self.Criterion_Dummy(report, isomme, p=self.p)

        def calculation(self) -> None:
            self.criterion_dummy.calculate()

            self.rating = self.criterion_dummy.rating

        class Criterion_Dummy(Criterion):
            name = "Dummy"

            def __init__(self, report, isomme, p):
                super().__init__(report, isomme)

                self.p = p

                self.criterion_hpc36 = self.Criterion_HPC36(report, isomme, p=self.p)
                self.criterion_chest_lateral_deflection = self.Criterion_Chest_Lateral_Deflection(report, isomme, p=self.p)
                self.criterion_chest_lateral_vc = self.Criterion_Chest_Lateral_VC(report, isomme, p=self.p)
                self.criterion_pubic_symphysis_force = self.Criterion_Pubic_Symphysis_Force(report, isomme, p=self.p)
                self.criterion_abdomen_force = self.Criterion_Abdomen_Force(report, isomme, p=self.p)

            def calculation(self) -> None:
                self.criterion_hpc36.calculate()
                self.criterion_chest_lateral_deflection.calculate()
                self.criterion_chest_lateral_vc.calculate()
                self.criterion_pubic_symphysis_force.calculate()
                self.criterion_abdomen_force.calculate()

                self.rating = np.min([
                    self.criterion_hpc36.rating,
                    self.criterion_chest_lateral_deflection.rating,
                    self.criterion_chest_lateral_vc.rating,
                    self.criterion_pubic_symphysis_force.rating,
                    self.criterion_abdomen_force.rating
                ])

            class Criterion_HPC36(UN_Frontal_50kmh_R137.Criterion_Overall.Criterion_Driver.Criterion_HPC36):
                pass

            class Criterion_Chest_Lateral_Deflection(Criterion):
                name = "Chest Lateral Deflection"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Fail([f"?{self.p}RIBS??????DSY?"], func=lambda x: -42, y_unit="mm", upper=True),
                        Limit_Pass([f"?{self.p}RIBS??????DSY?"], func=lambda x: -42, y_unit="mm", lower=True),
                        Limit_Fail([f"?{self.p}RIBS??????DSY?"], func=lambda x: 42, y_unit="mm", lower=True),
                    ])

                def calculation(self) -> None:
                    self.channel = self.isomme.get_channel(f"?{self.p}RIBSLE00??DSYC").convert_unit("mm")
                    self.value = np.min(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Chest_Lateral_VC(Criterion):
                name = "Chest Lateral VC"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Fail([f"?{self.p}VCCR00????VEY?", f"?{self.p}VCCRLE????VEY?", f"?{self.p}VCCRRI????VEY?"], func=lambda x: -1, y_unit="m/s", upper=True),
                        Limit_Pass([f"?{self.p}VCCR00????VEY?", f"?{self.p}VCCRLE????VEY?", f"?{self.p}VCCRRI????VEY?"], func=lambda x: -1, y_unit="m/s", lower=True),
                        Limit_Pass([f"?{self.p}VCCR00????VEY?", f"?{self.p}VCCRLE????VEY?", f"?{self.p}VCCRRI????VEY?"], func=lambda x: 1, y_unit="m/s", upper=True),
                        Limit_Fail([f"?{self.p}VCCR00????VEY?", f"?{self.p}VCCRLE????VEY?", f"?{self.p}VCCRRI????VEY?"], func=lambda x: 1, y_unit="m/s", lower=True),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}VCCRLE00??VEYC").convert_unit("m/s")
                    self.value = np.min(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Pubic_Symphysis_Force(UN_Side_Pole_R135.Criterion_Overall.Criterion_Dummy.Criterion_Pubic_Symphysis_Force):
                pass

            class Criterion_Abdomen_Force(Criterion):
                name = "Abdomen Peak Force"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_Fail([f"?{self.p}ABDO??????FOY?"], func=lambda x: -2.5, y_unit="kN", upper=True),
                        Limit_Pass([f"?{self.p}ABDO??????FOY?"], func=lambda x: -2.5, y_unit="kN", lower=True),
                    ])

                def calculation(self) -> None:
                    self.channel = self.isomme.get_channel(f"?{self.p}ABDOLE00??FOYB").convert_unit("kN")
                    self.value = np.min(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

    class Page_Values_Chart(Page_Criterion_Values_Chart):
        name = "Values Chart"
        title = "Values"

        def __init__(self, report):
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_dummy.criterion_hpc36,
                self.report.criterion_overall[isomme].criterion_dummy.criterion_chest_lateral_deflection,
                self.report.criterion_overall[isomme].criterion_dummy.criterion_chest_lateral_vc,
                self.report.criterion_overall[isomme].criterion_dummy.criterion_pubic_symphysis_force,
                self.report.criterion_overall[isomme].criterion_dummy.criterion_abdomen_force,
            ] for isomme in self.report.isomme_list}

    class Page_Values_Table(Page_Criterion_Values_Table):
        name = "Values Table"
        title = "Values"

        def __init__(self, report):
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_dummy.criterion_hpc36,
                self.report.criterion_overall[isomme].criterion_dummy.criterion_chest_lateral_deflection,
                self.report.criterion_overall[isomme].criterion_dummy.criterion_chest_lateral_vc,
                self.report.criterion_overall[isomme].criterion_dummy.criterion_pubic_symphysis_force,
                self.report.criterion_overall[isomme].criterion_dummy.criterion_abdomen_force,
            ] for isomme in self.report.isomme_list}

    class Page_Head_Acceleration(EuroNCAP_Side_Pole.Page_Head_Acceleration):
        pass

    class Page_Chest_Lateral_Deflection(Page_Plot_nxn):
        name: str = "Chest Lateral Deflection"
        title: str = "Chest Lateral Deflection"
        nrows: int = 3
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p}RIBSLEUP??DSYC"],
                                      [f"?{self.report.criterion_overall[isomme].p}RIBSRIUP??DSYC"],
                                      [f"?{self.report.criterion_overall[isomme].p}RIBSLEMI??DSYC"],
                                      [f"?{self.report.criterion_overall[isomme].p}RIBSRIMI??DSYC"],
                                      [f"?{self.report.criterion_overall[isomme].p}RIBSLELO??DSYC"],
                                      [f"?{self.report.criterion_overall[isomme].p}RIBSRILO??DSYC"]] for isomme in self.report.isomme_list}

    class Page_Chest_Lateral_VC(Page_Plot_nxn):
        name: str = "Chest Lateral VC"
        title: str = "Chest Lateral VC"
        nrows: int = 3
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p}VCCRLEUP??VEYC"],
                                      [f"?{self.report.criterion_overall[isomme].p}VCCRRIUP??VEYC"],
                                      [f"?{self.report.criterion_overall[isomme].p}VCCRLEMI??VEYC"],
                                      [f"?{self.report.criterion_overall[isomme].p}VCCRRIMI??VEYC"],
                                      [f"?{self.report.criterion_overall[isomme].p}VCCRLELO??VEYC"],
                                      [f"?{self.report.criterion_overall[isomme].p}VCCRRILO??VEYC"]] for isomme in self.report.isomme_list}

    class Page_Pubic_Symphysis_Force(EuroNCAP_Side_Pole.Page_Pubic_Symphysis_Force):
        pass

    class Page_Abdomen_Force(Page_Plot_nxn):
        name: str = "Abdomen Force"
        title: str = "Abdomen Force"
        nrows: int = 3
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p}ABDOLEFR??FOYB"],
                                      [f"?{self.report.criterion_overall[isomme].p}ABDORIFR??FOYB"],
                                      [f"?{self.report.criterion_overall[isomme].p}ABDOLEMI??FOYB"],
                                      [f"?{self.report.criterion_overall[isomme].p}ABDORIMI??FOYB"],
                                      [f"?{self.report.criterion_overall[isomme].p}ABDOLERE??FOYB"],
                                      [f"?{self.report.criterion_overall[isomme].p}ABDORIRE??FOYB"]] for isomme in self.report.isomme_list}
