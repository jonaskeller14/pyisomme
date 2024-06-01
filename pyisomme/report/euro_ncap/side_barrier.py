from pyisomme.report.page import Page_Cover
from pyisomme.report.report import Report
from pyisomme.report.criterion import Criterion
from pyisomme.report.euro_ncap.frontal_50kmh import EuroNCAP_Frontal_50kmh
from pyisomme.report.euro_ncap.side_pole import EuroNCAP_Side_Pole
from pyisomme.report.euro_ncap.limits import Limit_G, Limit_P, Limit_C, Limit_M, Limit_A, Limit_W

import logging
import numpy as np


logger = logging.getLogger(__name__)


# TODO:
#   - Add pages
#   - Add Modifier
#   - Add tests

class EuroNCAP_Side_Barrier(Report):
    """
    Protocol Version 9.3 (05.12.2023)

    References:
        - references/Euro-NCAP/euro-ncap-assessment-protocol-aop-v93.pdf
    """
    name = "Euro NCAP | Barrier Side Impact (AE-MDB) at 60 km/h"

    def __init__(self, isomme_list, title: str = "Report"):
        super().__init__(isomme_list, title)

        self.pages = [
            Page_Cover(self),
        ]

    class Criterion_Master(Criterion):
        name = "Master"
        p: int = 1

        def __init__(self, report, isomme):
            super().__init__(report, isomme)

            self.criterion_head = self.Criterion_Head(report, isomme, p=self.p)
            self.criterion_chest = self.Criterion_Chest(report, isomme, p=self.p)
            self.criterion_abdomen = self.Criterion_Abdomen(report, isomme, p=self.p)
            self.criterion_pelvis = self.Criterion_Pelvis(report, isomme, p=self.p)

        def calculation(self):
            self.criterion_head.calculate()
            self.criterion_chest.calculate()
            self.criterion_abdomen.calculate()
            self.criterion_pelvis.calculate()

            self.rating = self.value = np.sum([
                self.criterion_head.rating,
                self.criterion_chest.rating,
                self.criterion_abdomen.rating,
                self.criterion_pelvis.rating
            ])
            self.rating = self.value = np.interp(self.rating, [0, 16], [0, 16], left=0, right=np.nan)

        class Criterion_Head(Criterion):
            name = "Head"

            def __init__(self, report, isomme, p):
                super().__init__(report, isomme)

                self.p = p

                self.criterion_hic_15 = EuroNCAP_Frontal_50kmh.Criterion_Master.Criterion_Driver.Criterion_Head.Criterion_HIC_15(report, isomme, p=self.p)
                self.criterion_head_a3ms = EuroNCAP_Frontal_50kmh.Criterion_Master.Criterion_Driver.Criterion_Head.Criterion_Head_a3ms(report, isomme, p=self.p)

            def calculation(self):
                self.criterion_hic_15.calculate()
                self.criterion_head_a3ms.calculate()

                self.rating = self.value = np.min([
                    self.criterion_hic_15.rating,
                    self.criterion_head_a3ms.rating,
                ])

        class Criterion_Chest(Criterion):
            name = "Chest"

            def __init__(self, report, isomme, p):
                super().__init__(report, isomme)

                self.p = p

                self.criterion_chest_lateral_compression = self.Criterion_Chest_Lateral_Compression(report, isomme, p=self.p)

            def calculation(self) -> None:
                self.criterion_chest_lateral_compression.calculate()

                self.rating = self.criterion_chest_lateral_compression.rating

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
                    self.rating = self.limits.get_limit_min_value(self.channel, interpolate=True)

        class Criterion_Abdomen(Criterion):
            name = "Abdomen"

            def __init__(self, report, isomme, p):
                super().__init__(report, isomme)

                self.p = p

                self.criterion_abdomen_lateral_compression = EuroNCAP_Side_Pole.Criterion_Master.Criterion_Abdomen.Criterion_Abdomen_Lateral_Compression(report, isomme, p=self.p)

            def calculation(self) -> None:
                self.criterion_abdomen_lateral_compression.calculate()

                self.rating = self.value = self.criterion_abdomen_lateral_compression.rating

        class Criterion_Pelvis(Criterion):
            name = "Pelvis"

            def __init__(self, report, isomme, p):
                super().__init__(report, isomme)

                self.p = p

                self.criterion_public_symphysis_force = EuroNCAP_Side_Pole.Criterion_Master.Criterion_Pelvis.Criterion_Public_Symphysis_Force(report, isomme, p=self.p)

            def calculation(self) -> None:
                self.criterion_public_symphysis_force.calculate()

                self.rating = self.value = self.criterion_public_symphysis_force.rating
