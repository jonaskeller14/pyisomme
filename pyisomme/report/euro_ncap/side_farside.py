from pyisomme.limits import Limit
from pyisomme.report.page import Page_Cover, Page_Plot_nxn, Page_Criterion_Values_Chart, Page_Criterion_Rating_Table, \
    Page_Criterion_Values_Table
from pyisomme.report.report import Report
from pyisomme.report.criterion import Criterion
from pyisomme.report.euro_ncap.frontal_50kmh import EuroNCAP_Frontal_50kmh
from pyisomme.report.euro_ncap.side_pole import EuroNCAP_Side_Pole
from pyisomme.report.euro_ncap.side_barrier import EuroNCAP_Side_Barrier
from pyisomme.report.euro_ncap.limits import Limit_G, Limit_P, Limit_M, Limit_A, Limit_W


import logging
import numpy as np


logger = logging.getLogger(__name__)


class EuroNCAP_Side_FarSide(Report):
    name = "Euro NCAP | Far Side Occupant Protection Sled Test"
    protocol = "2.4"
    protocols = {
        "2.4": "Version 2.4 (12.05.2023) [references/Euro-NCAP/euro-ncap-far-side-test-and-assessment-protocol-v24.pdf]",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pages = [
            Page_Cover(self),

            self.Page_Values_Chart(self),
            self.Page_Rating_Table(self),
            self.Page_Values_Table(self),
            self.Page_Head_Acceleration(self),
            self.Page_Upper_Neck(self),
            self.Page_Lower_Neck(self),
            self.Page_Chest_Lateral_Compression(self),
            self.Page_Abdomen_Lateral_Compression(self),
            self.Page_Lumbar_Force(self),
            self.Page_Pubic_Symphysis_Force(self),
        ]

    class Criterion_Overall(Criterion):
        name = "Overall"
        p: int = 1

        def __init__(self, report, isomme):
            super().__init__(report, isomme)

            self.criterion_head_excursion = self.Criterion_Head_Excursion(report, isomme)

            self.criterion_head = self.Criterion_Head(report, isomme, p=self.p)
            self.criterion_neck = self.Criterion_Neck(report, isomme, p=self.p)
            self.criterion_chest_abdomen = self.Criterion_Chest_Abdomen(report, isomme, p=self.p)

            self.criterion_pelvis_lumbar_modifier = self.Criterion_Pelvis_Lumbar_Modifier(report, isomme, p=self.p)

        def calculation(self):
            self.criterion_head.calculate()
            self.criterion_neck.calculate()
            self.criterion_chest_abdomen.calculate()

            self.rating = np.sum([
                self.criterion_head.rating,
                self.criterion_neck.rating,
                self.criterion_chest_abdomen.rating,
            ])

            # Modifier
            self.criterion_pelvis_lumbar_modifier.calculate()
            self.rating += self.criterion_pelvis_lumbar_modifier.rating

            # Scale max. points of 12 down to 4
            self.rating = self.rating / 3

        class Criterion_Head_Excursion(Criterion):
            name = "Head Excursion"
            max_head_score: float = 4
            max_neck_score: float = 4
            max_chest_score: float = 4

            def __init__(self, report, isomme):
                super().__init__(report, isomme)

            def calculation(self):
                pass

        class Criterion_Head(Criterion):
            name = "Head"
            #TODO hard contact

            def __init__(self, report, isomme, p):
                super().__init__(report, isomme)

                self.p = p

                self.criterion_hic_15 = self.Criterion_HIC_15(report, isomme, p=self.p)
                self.criterion_head_a3ms = self.Criterion_Head_a3ms(report, isomme, p=self.p)

            def calculation(self):
                self.criterion_hic_15.calculate()
                self.criterion_head_a3ms.calculate()

                self.rating = self.value = np.min([
                    self.criterion_hic_15.rating,
                    self.criterion_head_a3ms.rating,
                ])

                # Downscaling
                self.rating = self.rating / 4 * self.report.criterion_overall[self.isomme].criterion_head_excursion.max_head_score

            class Criterion_HIC_15(EuroNCAP_Frontal_50kmh.Criterion_Overall.Criterion_Driver.Criterion_Head.Criterion_HIC_15):
                pass

            class Criterion_Head_a3ms(EuroNCAP_Frontal_50kmh.Criterion_Overall.Criterion_Driver.Criterion_Head.Criterion_Head_a3ms):
                pass

        class Criterion_Neck(Criterion):
            name = "Neck"

            def __init__(self, report, isomme, p):
                super().__init__(report, isomme)

                self.p = p

                self.criterion_upper_neck = self.Criterion_Upper_Neck(report, isomme, p=self.p)
                self.criterion_lower_neck = self.Criterion_Lower_Neck(report, isomme, p=self.p)

            def calculation(self):
                self.criterion_upper_neck.calculate()
                self.criterion_lower_neck.calculate()

                self.rating = np.min([
                    self.criterion_upper_neck.rating,
                    self.criterion_lower_neck.rating,
                ])

                # Downscaling
                self.rating = self.rating / 4 * self.report.criterion_overall[self.isomme].criterion_head_excursion.max_neck_score

            class Criterion_Upper_Neck(Criterion):
                name = "Upper_Neck"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_tension_fz = self.Criterion_Tension_Fz(report, isomme, p=self.p)
                    self.criterion_lateral_flexion_mxoc = self.Criterion_Lateral_Flexion_MxOC(report, isomme, p=self.p)
                    self.criterion_extension_myoc = self.Criterion_Extension_MyOC(report, isomme, p=self.p)

                def calculation(self):
                    self.criterion_tension_fz.calculate()
                    self.criterion_lateral_flexion_mxoc.calculate()
                    self.criterion_extension_myoc.calculate()

                    self.rating = np.min([
                        self.criterion_tension_fz.rating,
                        self.criterion_lateral_flexion_mxoc.rating,
                        self.criterion_extension_myoc.rating,
                    ])

                class Criterion_Tension_Fz(Criterion):
                    name = "Upper Neck Fz tension"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_G([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 3.74, y_unit="kN", upper=True),
                            Limit_P([f"?{self.p}NECKUP00??FOZ?"], func=lambda x: 3.74, y_unit="kN", lower=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??FOZA").convert_unit("kN")
                        self.value = np.max(self.channel.get_data())
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_Lateral_Flexion_MxOC(Criterion):
                    name = "Lateral flexion MxOC"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_P([f"?{self.p}TMONUP00??MOX?"], func=lambda x: -248.000, y_unit="Nm", upper=True),
                            Limit_W([f"?{self.p}TMONUP00??MOX?"], func=lambda x: -219.333, y_unit="Nm", upper=True),
                            Limit_M([f"?{self.p}TMONUP00??MOX?"], func=lambda x: -190.667, y_unit="Nm", upper=True),
                            Limit_A([f"?{self.p}TMONUP00??MOX?"], func=lambda x: -162.000, y_unit="Nm", upper=True),
                            Limit_G([f"?{self.p}TMONUP00??MOX?"], func=lambda x: -162.000, y_unit="Nm", lower=True),

                            Limit_G([f"?{self.p}TMONUP00??MOX?"], func=lambda x: 162.000, y_unit="Nm", upper=True),
                            Limit_A([f"?{self.p}TMONUP00??MOX?"], func=lambda x: 162.000, y_unit="Nm", lower=True),
                            Limit_M([f"?{self.p}TMONUP00??MOX?"], func=lambda x: 190.667, y_unit="Nm", lower=True),
                            Limit_W([f"?{self.p}TMONUP00??MOX?"], func=lambda x: 219.333, y_unit="Nm", lower=True),
                            Limit_P([f"?{self.p}TMONUP00??MOX?"], func=lambda x: 248.000, y_unit="Nm", lower=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}TMONUP00??MOXB")
                        self.value = self.channel.get_data()[np.argmax(np.abs(self.channel.get_data()))]
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_Extension_MyOC(Criterion):
                    name = "Upper Neck Extension MyOC"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_P([f"?{self.p}TMONUP00??MOY?"], func=lambda x: -50, y_unit="Nm", upper=True),
                            Limit_G([f"?{self.p}TMONUP00??MOY?"], func=lambda x: -50, y_unit="Nm", lower=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}TMONUP00??MOYB")
                        self.value = np.min(self.channel.get_data(unit="N*m"))
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Lower_Neck(Criterion):
                name = "Lower_Neck"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.criterion_tension_fz = self.Criterion_Tension_Fz(report, isomme, p=self.p)
                    self.criterion_lateral_flexion_mx = self.Criterion_Lateral_Flexion_Mx(report, isomme, p=self.p)
                    self.criterion_extension_my_base = self.Criterion_Extension_My_Base(report, isomme, p=self.p)

                def calculation(self):
                    self.criterion_tension_fz.calculate()
                    self.criterion_lateral_flexion_mx.calculate()
                    self.criterion_extension_my_base.calculate()

                    self.rating = np.min([
                        self.criterion_tension_fz.rating,
                        self.criterion_lateral_flexion_mx.rating,
                        self.criterion_extension_my_base.rating
                    ])

                class Criterion_Tension_Fz(Criterion):
                    name = "Lower Neck Fz tension"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_G([f"?{self.p}NECKLO00??FOZ?"], func=lambda x: 3.74, y_unit="kN", upper=True),
                            Limit_P([f"?{self.p}NECKLO00??FOZ?"], func=lambda x: 3.74, y_unit="kN", lower=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}NECKLO00??FOZA").convert_unit("kN")
                        self.value = np.max(self.channel.get_data())
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_Lateral_Flexion_Mx(Criterion):
                    name = "Lateral flexion Mx (base of neck)"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_P([f"?{self.p}TMONLO00??MOX?"], func=lambda x: -248.000, y_unit="Nm", upper=True),
                            Limit_W([f"?{self.p}TMONLO00??MOX?"], func=lambda x: -219.333, y_unit="Nm", upper=True),
                            Limit_M([f"?{self.p}TMONLO00??MOX?"], func=lambda x: -190.667, y_unit="Nm", upper=True),
                            Limit_A([f"?{self.p}TMONLO00??MOX?"], func=lambda x: -162.000, y_unit="Nm", upper=True),
                            Limit_G([f"?{self.p}TMONLO00??MOX?"], func=lambda x: -162.000, y_unit="Nm", lower=True),

                            Limit_G([f"?{self.p}TMONLO00??MOX?"], func=lambda x: 162.000, y_unit="Nm", upper=True),
                            Limit_A([f"?{self.p}TMONLO00??MOX?"], func=lambda x: 162.000, y_unit="Nm", lower=True),
                            Limit_M([f"?{self.p}TMONLO00??MOX?"], func=lambda x: 190.667, y_unit="Nm", lower=True),
                            Limit_W([f"?{self.p}TMONLO00??MOX?"], func=lambda x: 219.333, y_unit="Nm", lower=True),
                            Limit_P([f"?{self.p}TMONLO00??MOX?"], func=lambda x: 248.000, y_unit="Nm", lower=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}TMONLO00??MOXB")
                        self.value = self.channel.get_data(unit="N*m")[np.argmax(np.abs(self.channel.get_data()))]
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

                class Criterion_Extension_My_Base(Criterion):
                    name = "Lower Neck Extension My Base"

                    def __init__(self, report, isomme, p):
                        super().__init__(report, isomme)

                        self.p = p

                        self.extend_limit_list([
                            Limit_P([f"?{self.p}TMONLO00??MOY?"], func=lambda x: -100, y_unit="Nm", upper=True),
                            Limit_G([f"?{self.p}TMONLO00??MOY?"], func=lambda x: -100, y_unit="Nm", lower=True),
                        ])

                    def calculation(self):
                        self.channel = self.isomme.get_channel(f"?{self.p}TMONLO00??MOYB")
                        self.value = np.min(self.channel.get_data(unit="N*m"))
                        self.rating = self.limits.get_limit_min_rating(self.channel)
                        self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Chest_Abdomen(Criterion):
            name = "Chest & Abdomen"

            def __init__(self, report, isomme, p):
                super().__init__(report, isomme)

                self.p = p

                self.criterion_chest_lateral_compression = self.Criterion_Chest_Lateral_Compression(report, isomme, p=self.p)
                self.criterion_abdomen_lateral_compression = self.Criterion_Abdomen_Lateral_Compression(report, isomme, p=self.p)

            def calculation(self) -> None:
                self.criterion_chest_lateral_compression.calculate()
                self.criterion_abdomen_lateral_compression.calculate()

                self.rating = np.min([
                    self.criterion_chest_lateral_compression.rating,
                    self.criterion_abdomen_lateral_compression.rating
                ])

                # Downscaling
                self.rating = self.rating / 4 * self.report.criterion_overall[self.isomme].criterion_head_excursion.max_chest_score

            class Criterion_Chest_Lateral_Compression(EuroNCAP_Side_Barrier.Criterion_Overall.Criterion_Chest.Criterion_Chest_Lateral_Compression):
                pass

            class Criterion_Abdomen_Lateral_Compression(EuroNCAP_Side_Pole.Criterion_Overall.Criterion_Abdomen.Criterion_Abdomen_Lateral_Compression):
                pass

        class Criterion_Pelvis_Lumbar_Modifier(Criterion):
            name = "Pelvis and Lumbar Modifier"

            def __init__(self, report, isomme, p):
                super().__init__(report, isomme)

                self.p = p

                self.criterion_pubic_symphysis = self.Criterion_Pubic_Symphysis(report, isomme, p=self.p)
                self.criterion_lumbar_fy = self.Criterion_Lumbar_Fy(report, isomme, p=self.p)
                self.criterion_lumbar_fz = self.Criterion_Lumbar_Fz(report, isomme, p=self.p)
                self.criterion_lumbar_mx = self.Criterion_Lumbar_Mx(report, isomme, p=self.p)

            def calculation(self):
                self.criterion_pubic_symphysis.calculate()
                self.criterion_lumbar_fy.calculate()
                self.criterion_lumbar_fz.calculate()
                self.criterion_lumbar_mx.calculate()

                self.rating = np.min([
                    self.criterion_pubic_symphysis.rating,
                    self.criterion_lumbar_fy.rating,
                    self.criterion_lumbar_fz.rating,
                    self.criterion_lumbar_mx.rating,
                ])

            class Criterion_Pubic_Symphysis(Criterion):
                name = "Modifier Pubic Symphysis"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit([f"?{self.p}PUBC0000??FOY?"], func=lambda x: -2.8, y_unit="kN", upper=True, color="red", rating=-4, name="-4 pt. Modifier"),
                        Limit([f"?{self.p}PUBC0000??FOY?"], func=lambda x: 2.8, y_unit="kN", upper=True, color="green", rating=0, name="0 pt. Modifier"),
                        Limit([f"?{self.p}PUBC0000??FOY?"], func=lambda x: 2.8, y_unit="kN", lower=True, color="red", rating=-4, name="-4 pt. Modifier"),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}PUBC0000??FOYB").convert_unit("kN")
                    self.value = self.limits.get_limit_min_y(self.channel, unit="kN")
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Lumbar_Fy(Criterion):
                name = "Modifier Lumbar Fy"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit([f"?{self.p}LUSP0000??FOY?"], func=lambda x: -2, y_unit="kN", upper=True, color="red", rating=-4, name="-4 pt. Modifier"),
                        Limit([f"?{self.p}LUSP0000??FOY?"], func=lambda x: 2, y_unit="kN", upper=True, color="green", rating=0, name="0 pt. Modifier"),
                        Limit([f"?{self.p}LUSP0000??FOY?"], func=lambda x: 2, y_unit="kN", lower=True, color="red", rating=-4, name="-4 pt. Modifier"),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}LUSP0000??FOYB").convert_unit("kN")
                    self.value = self.limits.get_limit_min_y(self.channel, unit="kN")
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Lumbar_Fz(Criterion):
                name = "Modifier Lumbar Fz"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit([f"?{self.p}LUSP0000??FOZ?"], func=lambda x: -3.5, y_unit="kN", upper=True, color="red", rating=-4, name="-4 pt. Modifier"),
                        Limit([f"?{self.p}LUSP0000??FOZ?"], func=lambda x: 3.5, y_unit="kN", upper=True, color="green", rating=0, name="0 pt. Modifier"),
                        Limit([f"?{self.p}LUSP0000??FOZ?"], func=lambda x: 3.5, y_unit="kN", lower=True, color="red", rating=-4, name="-4 pt. Modifier"),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}LUSP0000??FOZB").convert_unit("kN")
                    self.value = self.limits.get_limit_min_y(self.channel, unit="kN")
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Lumbar_Mx(Criterion):
                name = "Modifier Lumbar Mx"

                def __init__(self, report, isomme, p):
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit([f"?{self.p}LUSP0000??MOX?"], func=lambda x: -120, y_unit="Nm", upper=True, color="red", rating=-4, name="-4 pt. Modifier"),
                        Limit([f"?{self.p}LUSP0000??MOX?"], func=lambda x: 120, y_unit="Nm", upper=True, color="green", rating=0, name="0 pt. Modifier"),
                        Limit([f"?{self.p}LUSP0000??MOX?"], func=lambda x: 120, y_unit="Nm", lower=True, color="red", rating=-4, name="-4 pt. Modifier"),
                    ])

                def calculation(self):
                    self.channel = self.isomme.get_channel(f"?{self.p}LUSP0000??MOXB").convert_unit("kN")
                    self.value = self.limits.get_limit_min_y(self.channel, unit="kN")
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                    self.color = self.limits.get_limit_min_color(self.channel)

    class Page_Values_Chart(Page_Criterion_Values_Chart):
        name = "Values Chart"
        title = "Values"

        def __init__(self, report):
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_head.criterion_hic_15,
                self.report.criterion_overall[isomme].criterion_head.criterion_head_a3ms,
                self.report.criterion_overall[isomme].criterion_neck.criterion_upper_neck.criterion_tension_fz,
                self.report.criterion_overall[isomme].criterion_neck.criterion_upper_neck.criterion_lateral_flexion_mxoc,
                self.report.criterion_overall[isomme].criterion_neck.criterion_upper_neck.criterion_extension_myoc,
                self.report.criterion_overall[isomme].criterion_neck.criterion_lower_neck.criterion_tension_fz,
                self.report.criterion_overall[isomme].criterion_neck.criterion_lower_neck.criterion_lateral_flexion_mx,
                self.report.criterion_overall[isomme].criterion_neck.criterion_lower_neck.criterion_extension_my_base,
                self.report.criterion_overall[isomme].criterion_chest_abdomen.criterion_chest_lateral_compression,
                self.report.criterion_overall[isomme].criterion_chest_abdomen.criterion_abdomen_lateral_compression,
                self.report.criterion_overall[isomme].criterion_pelvis_lumbar_modifier.criterion_pubic_symphysis,
                self.report.criterion_overall[isomme].criterion_pelvis_lumbar_modifier.criterion_lumbar_fy,
                self.report.criterion_overall[isomme].criterion_pelvis_lumbar_modifier.criterion_lumbar_fz,
                self.report.criterion_overall[isomme].criterion_pelvis_lumbar_modifier.criterion_lumbar_mx,
            ] for isomme in self.report.isomme_list}

    class Page_Values_Table(Page_Criterion_Values_Table):
        name = "Values Table"
        title = "Values"

        def __init__(self, report):
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_head.criterion_hic_15,
                self.report.criterion_overall[isomme].criterion_head.criterion_head_a3ms,
                self.report.criterion_overall[isomme].criterion_neck.criterion_upper_neck.criterion_tension_fz,
                self.report.criterion_overall[isomme].criterion_neck.criterion_upper_neck.criterion_lateral_flexion_mxoc,
                self.report.criterion_overall[isomme].criterion_neck.criterion_upper_neck.criterion_extension_myoc,
                self.report.criterion_overall[isomme].criterion_neck.criterion_lower_neck.criterion_tension_fz,
                self.report.criterion_overall[isomme].criterion_neck.criterion_lower_neck.criterion_lateral_flexion_mx,
                self.report.criterion_overall[isomme].criterion_neck.criterion_lower_neck.criterion_extension_my_base,
                self.report.criterion_overall[isomme].criterion_chest_abdomen.criterion_chest_lateral_compression,
                self.report.criterion_overall[isomme].criterion_chest_abdomen.criterion_abdomen_lateral_compression,
                self.report.criterion_overall[isomme].criterion_pelvis_lumbar_modifier.criterion_pubic_symphysis,
                self.report.criterion_overall[isomme].criterion_pelvis_lumbar_modifier.criterion_lumbar_fy,
                self.report.criterion_overall[isomme].criterion_pelvis_lumbar_modifier.criterion_lumbar_fz,
                self.report.criterion_overall[isomme].criterion_pelvis_lumbar_modifier.criterion_lumbar_mx,
            ] for isomme in self.report.isomme_list}

    class Page_Rating_Table(Page_Criterion_Rating_Table):
        name: str = "Rating Table"
        title: str = "Rating"

        def __init__(self, report):
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_head,
                self.report.criterion_overall[isomme].criterion_neck.criterion_upper_neck,
                self.report.criterion_overall[isomme].criterion_neck.criterion_lower_neck,
                self.report.criterion_overall[isomme].criterion_chest_abdomen,
                self.report.criterion_overall[isomme].criterion_pelvis_lumbar_modifier,
                self.report.criterion_overall[isomme],
            ] for isomme in self.report.isomme_list}

    class Page_Head_Acceleration(EuroNCAP_Side_Pole.Page_Head_Acceleration):
        pass

    class Page_Upper_Neck(Page_Plot_nxn):
        name = "Upper Neck"
        title = "Upper Neck"
        nrows = 2
        ncols = 2

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[self.report.criterion_overall[isomme].criterion_neck.criterion_upper_neck.criterion_tension_fz.channel],
                                      [self.report.criterion_overall[isomme].criterion_neck.criterion_upper_neck.criterion_lateral_flexion_mxoc.channel],
                                      [self.report.criterion_overall[isomme].criterion_neck.criterion_upper_neck.criterion_extension_myoc.channel]] for isomme in self.report.isomme_list}

    class Page_Lower_Neck(Page_Plot_nxn):
        name = "Lower Neck"
        title = "Lower Neck"
        nrows = 2
        ncols = 2

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[self.report.criterion_overall[isomme].criterion_neck.criterion_lower_neck.criterion_tension_fz.channel],
                                      [self.report.criterion_overall[isomme].criterion_neck.criterion_lower_neck.criterion_lateral_flexion_mx.channel],
                                      [self.report.criterion_overall[isomme].criterion_neck.criterion_lower_neck.criterion_extension_my_base.channel]] for isomme in self.report.isomme_list}

    class Page_Chest_Lateral_Compression(EuroNCAP_Side_Pole.Page_Chest_Lateral_Compression):
        pass

    class Page_Abdomen_Lateral_Compression(EuroNCAP_Side_Pole.Page_Abdomen_Lateral_Compression):
        pass

    class Page_Lumbar_Force(Page_Plot_nxn):
        name = "Lumbar Load"
        title = "Lumbar Load"
        nrows = 2
        ncols = 2

        def __init__(self, report):
            super().__init__(report)
            self.channels = {isomme: [[self.report.criterion_overall[isomme].criterion_pelvis_lumbar_modifier.criterion_lumbar_fy.channel],
                                      [self.report.criterion_overall[isomme].criterion_pelvis_lumbar_modifier.criterion_lumbar_fz.channel],
                                      [self.report.criterion_overall[isomme].criterion_pelvis_lumbar_modifier.criterion_lumbar_mx.channel]] for isomme in self.report.isomme_list}

    class Page_Pubic_Symphysis_Force(EuroNCAP_Side_Pole.Page_Pubic_Symphysis_Force):
        pass
