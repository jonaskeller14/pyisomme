from __future__ import annotations

import logging
from typing import Any

import numpy as np

from pyisomme.isomme import Isomme
from pyisomme.limit import Limit
from pyisomme.report.criterion import Criterion, Role, sub
from pyisomme.report.ctx import from_input
from pyisomme.report.euro_ncap.frontal_50kmh import (
    Criterion_Head_a3ms as Criterion_Head_a3ms_F50,
    Criterion_HIC_15 as Criterion_HIC_15_F50,
)
from pyisomme.report.euro_ncap.limits import Limit_A, Limit_G, Limit_M, Limit_P, Limit_W
from pyisomme.report.euro_ncap.protocols import PROTOCOL_FARSIDE_2_4
from pyisomme.report.euro_ncap.side_barrier import Overall as Overall_Side_Barrier
from pyisomme.report.euro_ncap.side_pole import (
    EuroNCAP_Side_Pole,
    Overall as Overall_Side_Pole,
)
from pyisomme.report.manual import Manual, manual
from pyisomme.report.page import (
    Page_Cover,
    Page_Criterion_Rating_Table,
    Page_Criterion_Values_Chart,
    Page_Criterion_Values_Table,
    Page_Plot_nxn,
)
from pyisomme.report.report import Report

logger = logging.getLogger(__name__)

P = manual(
    "1",
    source="test report",
    doc=(
        "Channel-code position of the far-side occupant — the only occupant §6 "
        "assesses. Defaults to the 'Driver position object 1' test-info field when "
        "the test carries it."
    ),
)


class Overall(Criterion):
    report: EuroNCAP_Side_FarSide
    name = "Overall"
    role = Role.AGGREGATE
    p: Manual[str, P]
    #: The root pins the code-template field once and the whole tree inherits it.
    _ctx_source = from_input(P)

    def __init__(self, report: Report, isomme: Isomme) -> None:
        super().__init__(report, isomme)
        self.prepare()

    def prepare(self) -> None:
        """Take the far-side position from the test info before the criteria read it."""
        p = self.isomme.get_test_info("Driver position object 1")
        if p is not None:
            self.set_derived_input("p", str(p).strip())

    def calculation(self) -> None:

        self.rating = np.sum(
            [
                self.criterion_head.rating,
                self.criterion_neck.rating,
                self.criterion_chest_abdomen.rating,
            ]
        )

        # Modifier
        self.rating += self.criterion_pelvis_lumbar_modifier.rating

        # Scale max. points of 12 down to 4
        self.rating = self.rating / 3

    class Criterion_Head_Excursion(Criterion):
        name = "Head Excursion"
        max_head_score: float = 4
        max_neck_score: float = 4
        max_chest_score: float = 4

        def calculation(self) -> None:
            pass

    class Criterion_Head(Criterion):
        report: EuroNCAP_Side_FarSide
        name = "Head"
        # TODO hard contact

        def calculation(self) -> None:

            self.rating = self.value = np.min(
                [
                    self.criterion_hic_15.rating,
                    self.criterion_head_a3ms.rating,
                ]
            )

            # Downscaling
            self.rating = (
                self.rating
                / 4
                * self.report.criterion_overall[
                    self.isomme
                ].criterion_head_excursion.max_head_score
            )

        class Criterion_HIC_15(Criterion_HIC_15_F50):
            pass

        class Criterion_Head_a3ms(Criterion_Head_a3ms_F50):
            pass

        criterion_hic_15 = sub(Criterion_HIC_15)
        criterion_head_a3ms = sub(Criterion_Head_a3ms)

    class Criterion_Neck(Criterion):
        report: EuroNCAP_Side_FarSide
        name = "Neck"

        def calculation(self) -> None:

            self.rating = np.min(
                [
                    self.criterion_upper_neck.rating,
                    self.criterion_lower_neck.rating,
                ]
            )

            # Downscaling
            self.rating = (
                self.rating
                / 4
                * self.report.criterion_overall[
                    self.isomme
                ].criterion_head_excursion.max_neck_score
            )

        class Criterion_Upper_Neck(Criterion):
            name = "Upper_Neck"

            def calculation(self) -> None:

                self.rating = np.min(
                    [
                        self.criterion_tension_fz.rating,
                        self.criterion_lateral_flexion_mxoc.rating,
                        self.criterion_extension_myoc.rating,
                    ]
                )

            class Criterion_Tension_Fz(Criterion):
                name = "Upper Neck Fz tension"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}NECKUP00??FOZ?")
                    return [
                        Limit_G(codes, func=lambda x: 3.74, y_unit="kN", upper=True),
                        Limit_P(codes, func=lambda x: 3.74, y_unit="kN", lower=True),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(
                        self.ctx.code("?{p}NECKUP00??FOZA")
                    ).convert_unit("kN")
                    self.value = np.max(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Lateral_Flexion_MxOC(Criterion):
                name = "Lateral flexion MxOC"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}TMONUP00??MOX?")
                    return [
                        Limit_P(
                            codes, func=lambda x: -248.000, y_unit="Nm", upper=True
                        ),
                        Limit_W(
                            codes, func=lambda x: -219.333, y_unit="Nm", upper=True
                        ),
                        Limit_M(
                            codes, func=lambda x: -190.667, y_unit="Nm", upper=True
                        ),
                        Limit_A(
                            codes, func=lambda x: -162.000, y_unit="Nm", upper=True
                        ),
                        Limit_G(
                            codes, func=lambda x: -162.000, y_unit="Nm", lower=True
                        ),
                        Limit_G(codes, func=lambda x: 162.000, y_unit="Nm", upper=True),
                        Limit_A(codes, func=lambda x: 162.000, y_unit="Nm", lower=True),
                        Limit_M(codes, func=lambda x: 190.667, y_unit="Nm", lower=True),
                        Limit_W(codes, func=lambda x: 219.333, y_unit="Nm", lower=True),
                        Limit_P(codes, func=lambda x: 248.000, y_unit="Nm", lower=True),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(
                        self.ctx.code("?{p}TMONUP00??MOXB")
                    )
                    self.value = self.channel.get_data()[
                        np.argmax(np.abs(self.channel.get_data()))
                    ]
                    self.rating = self.limits.get_limit_min_rating(self.channel)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Extension_MyOC(Criterion):
                name = "Upper Neck Extension MyOC"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}TMONUP00??MOY?")
                    return [
                        Limit_P(codes, func=lambda x: -50, y_unit="Nm", upper=True),
                        Limit_G(codes, func=lambda x: -50, y_unit="Nm", lower=True),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(
                        self.ctx.code("?{p}TMONUP00??MOYB")
                    )
                    self.value = np.min(self.channel.get_data(unit="N*m"))
                    self.rating = self.limits.get_limit_min_rating(self.channel)
                    self.color = self.limits.get_limit_min_color(self.channel)

            criterion_tension_fz = sub(Criterion_Tension_Fz)
            criterion_lateral_flexion_mxoc = sub(Criterion_Lateral_Flexion_MxOC)
            criterion_extension_myoc = sub(Criterion_Extension_MyOC)

        class Criterion_Lower_Neck(Criterion):
            name = "Lower_Neck"

            def calculation(self) -> None:

                self.rating = np.min(
                    [
                        self.criterion_tension_fz.rating,
                        self.criterion_lateral_flexion_mx.rating,
                        self.criterion_extension_my_base.rating,
                    ]
                )

            class Criterion_Tension_Fz(Criterion):
                name = "Lower Neck Fz tension"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}NECKLO00??FOZ?")
                    return [
                        Limit_G(codes, func=lambda x: 3.74, y_unit="kN", upper=True),
                        Limit_P(codes, func=lambda x: 3.74, y_unit="kN", lower=True),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(
                        self.ctx.code("?{p}NECKLO00??FOZA")
                    ).convert_unit("kN")
                    self.value = np.max(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Lateral_Flexion_Mx(Criterion):
                name = "Lateral flexion Mx (base of neck)"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}TMONLO00??MOX?")
                    return [
                        Limit_P(
                            codes, func=lambda x: -248.000, y_unit="Nm", upper=True
                        ),
                        Limit_W(
                            codes, func=lambda x: -219.333, y_unit="Nm", upper=True
                        ),
                        Limit_M(
                            codes, func=lambda x: -190.667, y_unit="Nm", upper=True
                        ),
                        Limit_A(
                            codes, func=lambda x: -162.000, y_unit="Nm", upper=True
                        ),
                        Limit_G(
                            codes, func=lambda x: -162.000, y_unit="Nm", lower=True
                        ),
                        Limit_G(codes, func=lambda x: 162.000, y_unit="Nm", upper=True),
                        Limit_A(codes, func=lambda x: 162.000, y_unit="Nm", lower=True),
                        Limit_M(codes, func=lambda x: 190.667, y_unit="Nm", lower=True),
                        Limit_W(codes, func=lambda x: 219.333, y_unit="Nm", lower=True),
                        Limit_P(codes, func=lambda x: 248.000, y_unit="Nm", lower=True),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(
                        self.ctx.code("?{p}TMONLO00??MOXB")
                    )
                    self.value = self.channel.get_data(unit="N*m")[
                        np.argmax(np.abs(self.channel.get_data()))
                    ]
                    self.rating = self.limits.get_limit_min_rating(self.channel)
                    self.color = self.limits.get_limit_min_color(self.channel)

            class Criterion_Extension_My_Base(Criterion):
                name = "Lower Neck Extension My Base"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}TMONLO00??MOY?")
                    return [
                        Limit_P(codes, func=lambda x: -100, y_unit="Nm", upper=True),
                        Limit_G(codes, func=lambda x: -100, y_unit="Nm", lower=True),
                    ]

                def calculation(self) -> None:
                    self.channel = self.require_channel(
                        self.ctx.code("?{p}TMONLO00??MOYB")
                    )
                    self.value = np.min(self.channel.get_data(unit="N*m"))
                    self.rating = self.limits.get_limit_min_rating(self.channel)
                    self.color = self.limits.get_limit_min_color(self.channel)

            criterion_tension_fz = sub(Criterion_Tension_Fz)
            criterion_lateral_flexion_mx = sub(Criterion_Lateral_Flexion_Mx)
            criterion_extension_my_base = sub(Criterion_Extension_My_Base)

        criterion_upper_neck = sub(Criterion_Upper_Neck)
        criterion_lower_neck = sub(Criterion_Lower_Neck)

    class Criterion_Chest_Abdomen(Criterion):
        report: EuroNCAP_Side_FarSide
        name = "Chest & Abdomen"

        def calculation(self) -> None:

            self.rating = np.min(
                [
                    self.criterion_chest_lateral_compression.rating,
                    self.criterion_abdomen_lateral_compression.rating,
                ]
            )

            # Downscaling
            self.rating = (
                self.rating
                / 4
                * self.report.criterion_overall[
                    self.isomme
                ].criterion_head_excursion.max_chest_score
            )

        class Criterion_Chest_Lateral_Compression(
            Overall_Side_Barrier.Criterion_Chest.Criterion_Chest_Lateral_Compression
        ):
            pass

        class Criterion_Abdomen_Lateral_Compression(
            Overall_Side_Pole.Criterion_Abdomen.Criterion_Abdomen_Lateral_Compression
        ):
            pass

        criterion_chest_lateral_compression = sub(Criterion_Chest_Lateral_Compression)
        criterion_abdomen_lateral_compression = sub(
            Criterion_Abdomen_Lateral_Compression
        )

    class Criterion_Pelvis_Lumbar_Modifier(Criterion):
        name = "Pelvis and Lumbar Modifier"

        def calculation(self) -> None:

            self.rating = np.min(
                [
                    self.criterion_pubic_symphysis.rating,
                    self.criterion_lumbar_fy.rating,
                    self.criterion_lumbar_fz.rating,
                    self.criterion_lumbar_mx.rating,
                ]
            )

        class Criterion_Pubic_Symphysis(Criterion):
            name = "Modifier Pubic Symphysis"
            role = Role.MODIFIER
            validate_ignore = {"limit_symmetry": "shared 0 pt. row spans both signs"}

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}PUBC0000??FOY?")
                return [
                    Limit(
                        codes,
                        func=lambda x: -2.8,
                        y_unit="kN",
                        upper=True,
                        color="red",
                        rating=-4,
                        name="-4 pt. Modifier",
                    ),
                    Limit(
                        codes,
                        func=lambda x: 2.8,
                        y_unit="kN",
                        upper=True,
                        color="green",
                        rating=0,
                        name="0 pt. Modifier",
                    ),
                    Limit(
                        codes,
                        func=lambda x: 2.8,
                        y_unit="kN",
                        lower=True,
                        color="red",
                        rating=-4,
                        name="-4 pt. Modifier",
                    ),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(
                    self.ctx.code("?{p}PUBC0000??FOYB")
                ).convert_unit("kN")
                self.value = self.limits.get_limit_min_y(self.channel, unit="kN")
                self.rating = self.limits.get_limit_min_rating(
                    self.channel, interpolate=False
                )
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Lumbar_Fy(Criterion):
            name = "Modifier Lumbar Fy"
            role = Role.MODIFIER
            validate_ignore = {"limit_symmetry": "shared 0 pt. row spans both signs"}

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}LUSP0000??FOY?")
                return [
                    Limit(
                        codes,
                        func=lambda x: -2,
                        y_unit="kN",
                        upper=True,
                        color="red",
                        rating=-4,
                        name="-4 pt. Modifier",
                    ),
                    Limit(
                        codes,
                        func=lambda x: 2,
                        y_unit="kN",
                        upper=True,
                        color="green",
                        rating=0,
                        name="0 pt. Modifier",
                    ),
                    Limit(
                        codes,
                        func=lambda x: 2,
                        y_unit="kN",
                        lower=True,
                        color="red",
                        rating=-4,
                        name="-4 pt. Modifier",
                    ),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(
                    self.ctx.code("?{p}LUSP0000??FOYB")
                ).convert_unit("kN")
                self.value = self.limits.get_limit_min_y(self.channel, unit="kN")
                self.rating = self.limits.get_limit_min_rating(
                    self.channel, interpolate=False
                )
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Lumbar_Fz(Criterion):
            name = "Modifier Lumbar Fz"
            role = Role.MODIFIER
            validate_ignore = {"limit_symmetry": "shared 0 pt. row spans both signs"}

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}LUSP0000??FOZ?")
                return [
                    Limit(
                        codes,
                        func=lambda x: -3.5,
                        y_unit="kN",
                        upper=True,
                        color="red",
                        rating=-4,
                        name="-4 pt. Modifier",
                    ),
                    Limit(
                        codes,
                        func=lambda x: 3.5,
                        y_unit="kN",
                        upper=True,
                        color="green",
                        rating=0,
                        name="0 pt. Modifier",
                    ),
                    Limit(
                        codes,
                        func=lambda x: 3.5,
                        y_unit="kN",
                        lower=True,
                        color="red",
                        rating=-4,
                        name="-4 pt. Modifier",
                    ),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(
                    self.ctx.code("?{p}LUSP0000??FOZB")
                ).convert_unit("kN")
                self.value = self.limits.get_limit_min_y(self.channel, unit="kN")
                self.rating = self.limits.get_limit_min_rating(
                    self.channel, interpolate=False
                )
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Lumbar_Mx(Criterion):
            name = "Modifier Lumbar Mx"
            role = Role.MODIFIER
            validate_ignore = {"limit_symmetry": "shared 0 pt. row spans both signs"}

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}LUSP0000??MOX?")
                return [
                    Limit(
                        codes,
                        func=lambda x: -120,
                        y_unit="Nm",
                        upper=True,
                        color="red",
                        rating=-4,
                        name="-4 pt. Modifier",
                    ),
                    Limit(
                        codes,
                        func=lambda x: 120,
                        y_unit="Nm",
                        upper=True,
                        color="green",
                        rating=0,
                        name="0 pt. Modifier",
                    ),
                    Limit(
                        codes,
                        func=lambda x: 120,
                        y_unit="Nm",
                        lower=True,
                        color="red",
                        rating=-4,
                        name="-4 pt. Modifier",
                    ),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(
                    self.ctx.code("?{p}LUSP0000??MOXB")
                ).convert_unit("Nm")
                self.value = self.limits.get_limit_min_y(self.channel, unit="Nm")
                self.rating = self.limits.get_limit_min_rating(
                    self.channel, interpolate=False
                )
                self.color = self.limits.get_limit_min_color(self.channel)

        criterion_pubic_symphysis = sub(Criterion_Pubic_Symphysis)
        criterion_lumbar_fy = sub(Criterion_Lumbar_Fy)
        criterion_lumbar_fz = sub(Criterion_Lumbar_Fz)
        criterion_lumbar_mx = sub(Criterion_Lumbar_Mx)

    criterion_head_excursion = sub(Criterion_Head_Excursion)
    criterion_head = sub(Criterion_Head)
    criterion_neck = sub(Criterion_Neck)
    criterion_chest_abdomen = sub(Criterion_Chest_Abdomen)
    criterion_pelvis_lumbar_modifier = sub(
        Criterion_Pelvis_Lumbar_Modifier, role=Role.MODIFIER
    )


class EuroNCAP_Side_FarSide(Report[Overall]):
    _name = "Euro NCAP | Far Side Occupant Protection Sled Test"
    _protocol = PROTOCOL_FARSIDE_2_4
    _protocols = (PROTOCOL_FARSIDE_2_4,)
    Criterion_Overall = Overall

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._available_pages = (
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
        )
        self._selected_pages = list(self._available_pages)

    class Page_Values_Chart(Page_Criterion_Values_Chart):
        report: EuroNCAP_Side_FarSide
        name = "Values Chart"
        title = "Values"

        def __init__(self, report: EuroNCAP_Side_FarSide) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_head.criterion_hic_15,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_head.criterion_head_a3ms,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_neck.criterion_upper_neck.criterion_tension_fz,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_neck.criterion_upper_neck.criterion_lateral_flexion_mxoc,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_neck.criterion_upper_neck.criterion_extension_myoc,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_neck.criterion_lower_neck.criterion_tension_fz,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_neck.criterion_lower_neck.criterion_lateral_flexion_mx,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_neck.criterion_lower_neck.criterion_extension_my_base,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_chest_abdomen.criterion_chest_lateral_compression,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_chest_abdomen.criterion_abdomen_lateral_compression,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_pelvis_lumbar_modifier.criterion_pubic_symphysis,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_pelvis_lumbar_modifier.criterion_lumbar_fy,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_pelvis_lumbar_modifier.criterion_lumbar_fz,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_pelvis_lumbar_modifier.criterion_lumbar_mx,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Values_Table(Page_Criterion_Values_Table):
        report: EuroNCAP_Side_FarSide
        name = "Values Table"
        title = "Values"

        def __init__(self, report: EuroNCAP_Side_FarSide) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_head.criterion_hic_15,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_head.criterion_head_a3ms,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_neck.criterion_upper_neck.criterion_tension_fz,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_neck.criterion_upper_neck.criterion_lateral_flexion_mxoc,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_neck.criterion_upper_neck.criterion_extension_myoc,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_neck.criterion_lower_neck.criterion_tension_fz,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_neck.criterion_lower_neck.criterion_lateral_flexion_mx,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_neck.criterion_lower_neck.criterion_extension_my_base,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_chest_abdomen.criterion_chest_lateral_compression,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_chest_abdomen.criterion_abdomen_lateral_compression,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_pelvis_lumbar_modifier.criterion_pubic_symphysis,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_pelvis_lumbar_modifier.criterion_lumbar_fy,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_pelvis_lumbar_modifier.criterion_lumbar_fz,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_pelvis_lumbar_modifier.criterion_lumbar_mx,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Rating_Table(Page_Criterion_Rating_Table):
        report: EuroNCAP_Side_FarSide
        name: str = "Rating Table"
        title: str = "Rating"

        def __init__(self, report: EuroNCAP_Side_FarSide) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[isomme].criterion_head,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_neck.criterion_upper_neck,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_neck.criterion_lower_neck,
                    self.report.criterion_overall[isomme].criterion_chest_abdomen,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_pelvis_lumbar_modifier,
                    self.report.criterion_overall[isomme],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Head_Acceleration(EuroNCAP_Side_Pole.Page_Head_Acceleration):
        pass

    class Page_Upper_Neck(Page_Plot_nxn):
        report: EuroNCAP_Side_FarSide
        name = "Upper Neck"
        title = "Upper Neck"
        nrows = 2
        ncols = 2

        def __init__(self, report: EuroNCAP_Side_FarSide) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        self.report.criterion_overall[
                            isomme
                        ].criterion_neck.criterion_upper_neck.criterion_tension_fz.channel
                    ],
                    [
                        self.report.criterion_overall[
                            isomme
                        ].criterion_neck.criterion_upper_neck.criterion_lateral_flexion_mxoc.channel
                    ],
                    [
                        self.report.criterion_overall[
                            isomme
                        ].criterion_neck.criterion_upper_neck.criterion_extension_myoc.channel
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Lower_Neck(Page_Plot_nxn):
        report: EuroNCAP_Side_FarSide
        name = "Lower Neck"
        title = "Lower Neck"
        nrows = 2
        ncols = 2

        def __init__(self, report: EuroNCAP_Side_FarSide) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        self.report.criterion_overall[
                            isomme
                        ].criterion_neck.criterion_lower_neck.criterion_tension_fz.channel
                    ],
                    [
                        self.report.criterion_overall[
                            isomme
                        ].criterion_neck.criterion_lower_neck.criterion_lateral_flexion_mx.channel
                    ],
                    [
                        self.report.criterion_overall[
                            isomme
                        ].criterion_neck.criterion_lower_neck.criterion_extension_my_base.channel
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Chest_Lateral_Compression(
        EuroNCAP_Side_Pole.Page_Chest_Lateral_Compression
    ):
        pass

    class Page_Abdomen_Lateral_Compression(
        EuroNCAP_Side_Pole.Page_Abdomen_Lateral_Compression
    ):
        pass

    class Page_Lumbar_Force(Page_Plot_nxn):
        report: EuroNCAP_Side_FarSide
        name = "Lumbar Load"
        title = "Lumbar Load"
        nrows = 2
        ncols = 2

        def __init__(self, report: EuroNCAP_Side_FarSide) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [
                        self.report.criterion_overall[
                            isomme
                        ].criterion_pelvis_lumbar_modifier.criterion_lumbar_fy.channel
                    ],
                    [
                        self.report.criterion_overall[
                            isomme
                        ].criterion_pelvis_lumbar_modifier.criterion_lumbar_fz.channel
                    ],
                    [
                        self.report.criterion_overall[
                            isomme
                        ].criterion_pelvis_lumbar_modifier.criterion_lumbar_mx.channel
                    ],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Pubic_Symphysis_Force(EuroNCAP_Side_Pole.Page_Pubic_Symphysis_Force):
        pass
