from pyisomme.report.page import Page_Cover
from pyisomme.report.report import Report
from pyisomme.report.criterion import Criterion
from pyisomme.report.euro_ncap.frontal_50kmh import EuroNCAP_Frontal_50kmh
from pyisomme.report.euro_ncap.side_pole import EuroNCAP_Side_Pole
from pyisomme.report.euro_ncap.limits import Limit_G, Limit_P, Limit_C, Limit_M, Limit_A, Limit_W

import logging
import numpy as np


logger = logging.getLogger(__name__)


class EuroNCAP_Side_Barrier(Report):
    name = "Euro NCAP | Barrier Side Impact (AE-MDB) at 60 km/h"
    protocol = "9.3"
    protocols = {
        "9.3": "Version 9.3 (05.12.2023) [references/Euro-NCAP/euro-ncap-assessment-protocol-aop-v93.pdf]"
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pages = [
            Page_Cover(self),

            self.Page_Values_Chart(self),
            self.Page_Rating_Table(self),
            self.Page_Values_Table(self),
            self.Page_Head_Acceleration(self),
            self.Page_Shoulder_Lateral_Force(self),
            self.Page_Chest_Lateral_Compression(self),
            self.Page_Chest_Lateral_VC(self),
            self.Page_Abdomen_Lateral_Compression(self),
            self.Page_Abdomen_Lateral_VC(self),
            self.Page_Pubic_Symphysis_Force(self),
        ]

    class Criterion_Overall(Criterion):
        name = "Overall"
        p: int = 1

        def __init__(self, report, isomme):
            super().__init__(report, isomme)

            self.criterion_head = self.Criterion_Head(self.report, self.isomme, p=self.p)
            self.criterion_chest = self.Criterion_Chest(self.report, self.isomme, p=self.p)
            self.criterion_abdomen = self.Criterion_Abdomen(self.report, self.isomme, p=self.p)
            self.criterion_pelvis = self.Criterion_Pelvis(self.report, self.isomme, p=self.p)

        def calculation(self):
            self.criterion_head.calculate()
            self.criterion_chest.calculate()
            self.criterion_abdomen.calculate()
            self.criterion_pelvis.calculate()

            self.rating = np.sum([
                self.criterion_head.rating,
                self.criterion_chest.rating,
                self.criterion_abdomen.rating,
                self.criterion_pelvis.rating
            ])
            self.rating = np.interp(self.rating, [0, 16], [0, 16], left=0, right=np.nan)

        class Criterion_Head(Criterion):
            name = "Head"

            def __init__(self, report, isomme, p):
                super().__init__(report, isomme)

                self.p = p

                self.criterion_hic_15 = self.Criterion_HIC_15(self.report, self.isomme, p=self.p)
                self.criterion_head_a3ms = self.Criterion_Head_a3ms(self.report, self.isomme, p=self.p)

            def calculation(self):
                self.criterion_hic_15.calculate()
                self.criterion_head_a3ms.calculate()

                self.rating = np.min([
                    self.criterion_hic_15.rating,
                    self.criterion_head_a3ms.rating,
                ])

            class Criterion_HIC_15(EuroNCAP_Frontal_50kmh.Criterion_Overall.Criterion_Driver.Criterion_Head.Criterion_HIC_15):
                pass

            class Criterion_Head_a3ms(EuroNCAP_Frontal_50kmh.Criterion_Overall.Criterion_Driver.Criterion_Head.Criterion_Head_a3ms):
                pass

        class Criterion_Chest(Criterion):
            name = "Chest"

            def __init__(self, report, isomme, p):
                super().__init__(report, isomme)

                self.p = p

                self.criterion_chest_lateral_compression = self.Criterion_Chest_Lateral_Compression(self.report, self.isomme, p=self.p)
                self.criterion_chest_lateral_vc = self.Criterion_Chest_Lateral_VC(self.report, self.isomme, p=self.p)
                self.criterion_shoulder_lateral_force = self.Criterion_Shoulder_Lateral_Force(self.report, self.isomme, p=self.p)

            def calculation(self) -> None:
                self.criterion_chest_lateral_compression.calculate()
                self.criterion_chest_lateral_vc.calculate()
                self.criterion_shoulder_lateral_force.calculate()

                self.rating = np.min([
                    self.criterion_chest_lateral_compression.rating,
                    self.criterion_chest_lateral_vc.rating,
                    self.criterion_shoulder_lateral_force.rating,
                ])

            class Criterion_Chest_Lateral_Compression(Criterion):
                name = "Chest Lateral Compression"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_C([f"?{self.p}TRRI??0[0123]??DSY?"], func=lambda x: -50.000, y_unit="mm", upper=True),
                        Limit_P([f"?{self.p}TRRI??0[0123]??DSY?"], func=lambda x: -50.000, y_unit="mm"),
                        Limit_W([f"?{self.p}TRRI??0[0123]??DSY?"], func=lambda x: -42.667, y_unit="mm", upper=True),
                        Limit_M([f"?{self.p}TRRI??0[0123]??DSY?"], func=lambda x: -35.333, y_unit="mm", upper=True),
                        Limit_A([f"?{self.p}TRRI??0[0123]??DSY?"], func=lambda x: -28.000, y_unit="mm", upper=True),
                        Limit_G([f"?{self.p}TRRI??0[0123]??DSY?"], func=lambda x: -28.000, y_unit="mm", lower=True),
                    ])

                def calculation(self) -> None:
                    self.channel = self.isomme.get_channel(f"?{self.p}TRRI??00??DSYC").convert_unit("mm")
                    self.value = np.min(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=True)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Chest_Lateral_VC(EuroNCAP_Side_Pole.Criterion_Overall.Criterion_Chest.Criterion_Chest_Lateral_VC):
                pass

            class Criterion_Shoulder_Lateral_Force(EuroNCAP_Side_Pole.Criterion_Overall.Criterion_Chest.Criterion_Shoulder_Lateral_Force):
                pass

        class Criterion_Abdomen(Criterion):
            name = "Abdomen"

            def __init__(self, report, isomme, p):
                super().__init__(report, isomme)

                self.p = p

                self.criterion_abdomen_lateral_compression = self.Criterion_Abdomen_Lateral_Compression(self.report, self.isomme, p=self.p)
                self.criterion_abdomen_lateral_vc = self.Criterion_Abdomen_Lateral_VC(self.report, self.isomme, p=self.p)

            def calculation(self) -> None:
                self.criterion_abdomen_lateral_compression.calculate()
                self.criterion_abdomen_lateral_vc.calculate()

                self.rating = np.min([
                    self.criterion_abdomen_lateral_compression.rating,
                    self.criterion_abdomen_lateral_vc.rating
                ])

            class Criterion_Abdomen_Lateral_Compression(EuroNCAP_Side_Pole.Criterion_Overall.Criterion_Abdomen.Criterion_Abdomen_Lateral_Compression):
                pass

            class Criterion_Abdomen_Lateral_VC(EuroNCAP_Side_Pole.Criterion_Overall.Criterion_Abdomen.Criterion_Abdomen_Lateral_VC):
                pass

        class Criterion_Pelvis(Criterion):
            name = "Pelvis"

            def __init__(self, report, isomme, p):
                super().__init__(report, isomme)

                self.p = p

                self.criterion_pubic_symphysis_force = self.Criterion_Pubic_Symphysis_Force(self.report, self.isomme, p=self.p)

            def calculation(self) -> None:
                self.criterion_pubic_symphysis_force.calculate()

                self.rating = self.criterion_pubic_symphysis_force.rating

            class Criterion_Pubic_Symphysis_Force(EuroNCAP_Side_Pole.Criterion_Overall.Criterion_Pelvis.Criterion_Pubic_Symphysis_Force):
                pass

    class Page_Values_Chart(EuroNCAP_Side_Pole.Page_Values_Chart):
        pass

    class Page_Values_Table(EuroNCAP_Side_Pole.Page_Values_Table):
        pass

    class Page_Rating_Table(EuroNCAP_Side_Pole.Page_Rating_Table):
        pass

    class Page_Head_Acceleration(EuroNCAP_Side_Pole.Page_Head_Acceleration):
        pass

    class Page_Shoulder_Lateral_Force (EuroNCAP_Side_Pole.Page_Shoulder_Lateral_Force):
        pass

    class Page_Chest_Lateral_Compression(EuroNCAP_Side_Pole.Page_Chest_Lateral_Compression):
        pass

    class Page_Chest_Lateral_VC(EuroNCAP_Side_Pole.Page_Chest_Lateral_VC):
        pass

    class Page_Abdomen_Lateral_Compression(EuroNCAP_Side_Pole.Page_Abdomen_Lateral_Compression):
        pass

    class Page_Abdomen_Lateral_VC(EuroNCAP_Side_Pole.Page_Abdomen_Lateral_VC):
        pass

    class Page_Pubic_Symphysis_Force(EuroNCAP_Side_Pole.Page_Pubic_Symphysis_Force):
        pass
