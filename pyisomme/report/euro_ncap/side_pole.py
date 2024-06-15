from pyisomme.calculate import calculate_hic, calculate_xms
from pyisomme.unit import Unit, g0
from pyisomme.report.page import Page_Cover, Page_Plot_nxn
from pyisomme.report.report import Report
from pyisomme.report.criterion import Criterion
from pyisomme.report.euro_ncap.limits import Limit_G, Limit_P, Limit_C, Limit_M, Limit_A, Limit_W

import logging
import numpy as np


logger = logging.getLogger(__name__)


# TODO:
#   - Add pages
#   - Add Modifier
#   - Add tests

class EuroNCAP_Side_Pole(Report):
    name = "Euro NCAP | Pole Side Impact at 32 km/h"
    protocol = "9.3"
    protocols = {
        "9.3": "Version 9.3 (05.12.2023) [references/Euro-NCAP/euro-ncap-assessment-protocol-aop-v93.pdf]"
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pages = [
            Page_Cover(self),

            self.Page_Head_Acceleration(self),
            self.Page_Chest_Lateral_Compression(self),
            self.Page_Abdomen_Lateral_Compression(self),
            self.Page_Pubic_Symphysis_Force(self),
        ]

    class Criterion_Master(Criterion):
        name = "Master"
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
                self.criterion_direct_head_contact_with_the_pole = self.Criterion_DirectHeadContactWithThePole(report, isomme)

            def calculation(self):
                self.criterion_hic_15.calculate()
                self.criterion_head_a3ms.calculate()
                self.criterion_direct_head_contact_with_the_pole.calculate()

                self.rating = np.min([
                    self.criterion_hic_15.rating,
                    self.criterion_head_a3ms.rating,
                    self.criterion_direct_head_contact_with_the_pole.rating,
                ])

            class Criterion_HIC_15(Criterion):
                name = "HIC 15"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_G([f"?{self.p}HICR0015??00RX"], func=lambda x: 700.000, y_unit=1, upper=True),
                        Limit_C([f"?{self.p}HICR0015??00RX"], func=lambda x: 700.000, y_unit=1, lower=True),
                    ])

                def calculation(self):
                    self.channel = calculate_hic(self.isomme.get_channel(f"?{self.p}HEAD??00??ACRA"), 15)
                    self.value = self.channel.get_data()[0]
                    self.rating = -np.inf if self.value >= 700 else 4

            class Criterion_Head_a3ms(Criterion):
                name = "Head a3ms"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_G([f"?{self.p}HEAD003C??ACRA"], func=lambda x: 80.000, y_unit=Unit(g0), upper=True),
                        Limit_C([f"?{self.p}HEAD003C??ACRA"], func=lambda x: 80.000, y_unit=Unit(g0), lower=True),
                    ])

                def calculation(self):
                    self.channel = calculate_xms(self.isomme.get_channel(f"?{self.p}HEAD0000??ACRA", f"?{self.p}HEADCG00??ACRA"), 3, method="C")
                    self.value = self.channel.get_data(unit=g0)[0]
                    self.rating = -np.inf if self.value >= 80.0 else 4

            class Criterion_DirectHeadContactWithThePole(Criterion):
                name = "Direct head contact with the pole"
                direct_head_contact_with_the_pole: bool = False

                def calculation(self) -> None:
                    self.value = self.direct_head_contact_with_the_pole
                    self.rating = -np.inf if self.direct_head_contact_with_the_pole else 4


        class Criterion_Chest(Criterion):
            name = "Chest"

            def __init__(self, report, isomme, p):
                super().__init__(report, isomme)

                self.p = p

                self.criterion_chest_lateral_compression = self.Criterion_Chest_Lateral_Compression(self.report, self.isomme, p=self.p)

            def calculation(self) -> None:
                self.criterion_chest_lateral_compression.calculate()

                self.rating = self.criterion_chest_lateral_compression.rating

            class Criterion_Chest_Lateral_Compression(Criterion):
                name = "Chest Lateral Compression"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_C([f"?{self.p}TRRI??0[0123]??DSY?"], func=lambda x: -55.000, y_unit="mm", upper=True),
                        Limit_P([f"?{self.p}TRRI??0[0123]??DSY?"], func=lambda x: -50.000, y_unit="mm", upper=True),
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

                self.criterion_abdomen_lateral_compression = self.Criterion_Abdomen_Lateral_Compression(self.report, self.isomme, p=self.p)

            def calculation(self) -> None:
                self.criterion_abdomen_lateral_compression.calculate()

                self.rating = self.criterion_abdomen_lateral_compression.rating

            class Criterion_Abdomen_Lateral_Compression(Criterion):
                name = "Abdomen Lateral Compression"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_C([f"?{self.p}ABRI??0[012]??DSY?"], func=lambda x: -65, y_unit="mm", upper=True),
                        Limit_P([f"?{self.p}ABRI??0[012]??DSY?"], func=lambda x: -65, y_unit="mm"),
                        Limit_W([f"?{self.p}ABRI??0[012]??DSY?"], func=lambda x: -59, y_unit="mm", upper=True),
                        Limit_M([f"?{self.p}ABRI??0[012]??DSY?"], func=lambda x: -53, y_unit="mm", upper=True),
                        Limit_A([f"?{self.p}ABRI??0[012]??DSY?"], func=lambda x: -47, y_unit="mm", upper=True),
                        Limit_G([f"?{self.p}ABRI??0[012]??DSY?"], func=lambda x: -47, y_unit="mm", lower=True),
                    ])

                def calculation(self) -> None:
                    self.channel = self.isomme.get_channel(f"?{self.p}ABRI??00??DSYC").convert_unit("mm")
                    self.value = np.min(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_value(self.channel, interpolate=True)

        class Criterion_Pelvis(Criterion):
            name = "Pelvis"

            def __init__(self, report, isomme, p):
                super().__init__(report, isomme)

                self.p = p

                self.criterion_pubic_symphysis_force = self.Criterion_Pubic_Symphysis_Force(self.report, self.isomme, p=self.p)

            def calculation(self) -> None:
                self.criterion_pubic_symphysis_force.calculate()

                self.rating = self.criterion_pubic_symphysis_force.rating

            class Criterion_Pubic_Symphysis_Force(Criterion):
                name = "Pubic Symphysis Force"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_C([f"?{self.p}PUBC0000??FOY?"], func=lambda x: -2.800, y_unit="kN", upper=True),
                        Limit_P([f"?{self.p}PUBC0000??FOY?"], func=lambda x: -2.800, y_unit="kN"),
                        Limit_W([f"?{self.p}PUBC0000??FOY?"], func=lambda x: -2.433, y_unit="kN", upper=True),
                        Limit_M([f"?{self.p}PUBC0000??FOY?"], func=lambda x: -2.067, y_unit="kN", upper=True),
                        Limit_A([f"?{self.p}PUBC0000??FOY?"], func=lambda x: -1.700, y_unit="kN", upper=True),
                        Limit_G([f"?{self.p}PUBC0000??FOY?"], func=lambda x: -1.700, y_unit="kN", lower=True),

                        Limit_G([f"?{self.p}PUBC0000??FOY?"], func=lambda x: 1.700, y_unit="kN", upper=True),
                        Limit_A([f"?{self.p}PUBC0000??FOY?"], func=lambda x: 1.700, y_unit="kN", lower=True),
                        Limit_M([f"?{self.p}PUBC0000??FOY?"], func=lambda x: 2.067, y_unit="kN", lower=True),
                        Limit_W([f"?{self.p}PUBC0000??FOY?"], func=lambda x: 2.433, y_unit="kN", lower=True),
                        Limit_P([f"?{self.p}PUBC0000??FOY?"], func=lambda x: 2.800, y_unit="kN"),
                        Limit_C([f"?{self.p}PUBC0000??FOY?"], func=lambda x: 2.800, y_unit="kN", lower=True),
                    ])

                def calculation(self) -> None:
                    self.channel = self.isomme.get_channel(f"?{self.p}PUBC0000??FOYB").convert_unit("kN")
                    self.value = self.channel.get_data()[np.argmax(np.abs(self.channel.get_data()))]
                    self.rating = self.limits.get_limit_min_value(self.channel, interpolate=True)

    class Page_Head_Acceleration(Page_Plot_nxn):
        name: str = "Driver Head Acceleration"
        title: str = "Driver Head Acceleration"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_master[isomme].p}HEAD??????AC{xyzr}A"] for xyzr in "XYZR"] for isomme in self.report.isomme_list}

    class Page_Chest_Lateral_Compression(Page_Plot_nxn):
        name: str = "Chest Lateral Compression"
        title: str = "Chest Lateral Compression"
        nrows: int = 3
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_master[isomme].p}TRRILE01??DSYC"],
                                      [f"?{self.report.criterion_master[isomme].p}TRRIRI01??DSYC"],
                                      [f"?{self.report.criterion_master[isomme].p}TRRILE02??DSYC"],
                                      [f"?{self.report.criterion_master[isomme].p}TRRIRI02??DSYC"],
                                      [f"?{self.report.criterion_master[isomme].p}TRRILE03??DSYC"],
                                      [f"?{self.report.criterion_master[isomme].p}TRRIRI04??DSYC"]] for isomme in self.report.isomme_list}

    class Page_Abdomen_Lateral_Compression(Page_Plot_nxn):
        name: str = "Abdomen Lateral Compression"
        title: str = "Abdomen Lateral Compression"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_master[isomme].p}ABRILE01??DSYC"],
                                      [f"?{self.report.criterion_master[isomme].p}ABRIRI01??DSYC"],
                                      [f"?{self.report.criterion_master[isomme].p}ABRILE02??DSYC"],
                                      [f"?{self.report.criterion_master[isomme].p}ABRIRI03??DSYC"]] for isomme in self.report.isomme_list}

    class Page_Pubic_Symphysis_Force(Page_Plot_nxn):
        name: str = "Pubic Symphysis Force"
        title: str = "Pubic Symphysis Force"

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_master[isomme].p}PUBC0000??FOYB"]] for isomme in self.report.isomme_list}
