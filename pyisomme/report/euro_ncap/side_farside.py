from __future__ import annotations

import logging
from typing import Any

import numpy as np

from pyisomme.calculate import calculate_damage
from pyisomme.channel import Channel
from pyisomme.isomme import Isomme
from pyisomme.limit import Limit
from pyisomme.report.criterion import Criterion, Role, sub
from pyisomme.report.criterion_result import CriterionResult
from pyisomme.report.ctx import from_input
from pyisomme.report.euro_ncap.frontal_50kmh import (
    Criterion_Head_a3ms as Criterion_Head_a3ms_F50,
    Criterion_HIC_15 as Criterion_HIC_15_F50,
)
from pyisomme.report.euro_ncap.limits import Limit_A, Limit_G, Limit_M, Limit_P, Limit_W
from pyisomme.report.euro_ncap.pages import (
    side_abdomen_lateral_compression_spec_for,
    side_chest_lateral_compression_spec_for,
    side_head_acceleration_spec_for,
    side_pubic_symphysis_force_spec_for,
)
from pyisomme.report.euro_ncap.protocols import (
    PROTOCOL_FARSIDE_2_4,
    PROTOCOL_FARSIDE_2_5,
)
from pyisomme.report.euro_ncap.side_barrier import Overall as Overall_Side_Barrier
from pyisomme.report.euro_ncap.side_pole import (
    Overall as Overall_Side_Pole,
)
from pyisomme.report.manual import Manual, manual
from pyisomme.report.page2 import (
    ChannelPlotPage,
    CoverPage,
    CriterionTablePage,
    CriterionValuesChartPage,
    HICPage,
    channel_plot_spec_for,
    criterion_values_chart_spec_for,
    hic_spec_for,
    rating_table_spec_for,
    values_table_spec_for,
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

    def __init__(self, report: Report[Any], isomme: Isomme) -> None:
        super().__init__(report, isomme)
        self.prepare()

    def prepare(self) -> None:
        """Take the far-side position from the test info before the criteria read it."""
        p = self.isomme.get_test_info("Driver position object 1")
        if p is not None:
            self.set_derived_input("p", str(p).strip())

    def calculation(self) -> CriterionResult:
        rating = np.sum(
            [
                Criterion.rating_of(self.criterion_head),
                Criterion.rating_of(self.criterion_neck),
                Criterion.rating_of(self.criterion_chest_abdomen),
            ]
        )

        # §7.4.1 modifier applies to the 12-point sled-test score.
        rating += Criterion.rating_of(self.criterion_pelvis_lumbar_modifier)

        # §7.1 scales the 12-point sled-test score down to the 4-point far-side
        # contribution. §7.4.2 then deducts from that final score.
        rating = rating / 3
        rating += Criterion.rating_of(self.criterion_occupant_to_occupant_protection)
        rating = float(np.max([0.0, rating]))
        return CriterionResult(
            channel=None,
            value=rating,
            rating=rating,
            color=None,
        )

    class Criterion_Head_Excursion(Criterion):
        name = "Head Excursion"
        source = "§7.2"
        far_side_countermeasure: Manual[
            bool,
            manual(
                False,
                source="test report",
                doc=(
                    "Is a far-side countermeasure fitted? This selects the applicable "
                    "§7.2 head-excursion score-cap table."
                ),
            ),
        ]
        excursion_zone: Manual[
            str,
            manual(
                "green",
                source="high-speed video",
                doc=(
                    "Peak head-excursion zone: capping, red, orange, yellow, or green."
                ),
            ),
        ]
        red_line_more_than_125_mm_outboard: Manual[
            bool,
            manual(
                False,
                source="test set-up measurement",
                doc=(
                    "For a red-zone excursion with a countermeasure, is the red line "
                    "more than 125 mm outboard of the orange line?"
                ),
            ),
        ]
        max_head_score: float = 4
        max_neck_score: float = 4
        max_chest_score: float = 4

        def calculation(self) -> CriterionResult:
            zone = self.excursion_zone.lower().replace("-", "_").replace(" ", "_")
            if self.far_side_countermeasure:
                if zone == "red" and self.red_line_more_than_125_mm_outboard:
                    zone = "red_over_125"
                score_caps = {
                    "capping": (0.0, 0.0, 0.0),
                    "red": (0.0, 4.0, 0.0),
                    "red_over_125": (2.0, 4.0, 0.0),
                    "orange": (3.0, 3.0, 3.0),
                    "yellow": (4.0, 4.0, 4.0),
                    "green": (4.0, 4.0, 4.0),
                }
            else:
                score_caps = {
                    "capping": (0.0, 0.0, 0.0),
                    "red": (0.0, 1.0, 0.0),
                    "orange": (1.0, 1.0, 1.0),
                    "yellow": (2.0, 2.0, 2.0),
                    "green": (4.0, 4.0, 4.0),
                }

            try:
                (
                    self.max_head_score,
                    self.max_neck_score,
                    self.max_chest_score,
                ) = score_caps[zone]
            except KeyError as error:
                valid_zones = ", ".join(("capping", "red", "orange", "yellow", "green"))
                raise ValueError(
                    f"Unknown head-excursion zone {self.excursion_zone!r}; "
                    f"expected one of {valid_zones}."
                ) from error

            value = self.max_head_score + self.max_neck_score + self.max_chest_score
            return CriterionResult(channel=None, value=value, rating=value, color=None)

    class Criterion_Head(Criterion):
        report: EuroNCAP_Side_FarSide
        name = "Head"
        source = "§7.3.1"
        hard_contact: Manual[
            bool,
            manual(
                True,
                source="high-speed video",
                doc=(
                    "Was hard head contact observed? A resultant 3 ms acceleration above "
                    "80 g forces this to True regardless."
                ),
            ),
        ]

        def calculation(self) -> CriterionResult:
            head_a3ms_rating = Criterion.rating_of(self.criterion_head_a3ms)
            if Criterion.value_of(self.criterion_head_a3ms) > 80:
                logger.info(
                    "Hard head contact assumed for p=%s in %s",
                    self.ctx.field("p"),
                    self.isomme,
                )
                self.hard_contact = True

            # §7.3.1 scores HIC15 only with direct contact; resultant 3 ms
            # acceleration is always scored. DAMAGE is monitoring-only.
            if self.hard_contact:
                value = rating = min(
                    Criterion.rating_of(self.criterion_hic_15), head_a3ms_rating
                )
            else:
                value = rating = head_a3ms_rating

            # Downscaling
            rating = (
                rating
                / 4
                * self.report.criterion_overall[
                    self.isomme
                ].criterion_head_excursion.max_head_score
            )
            return CriterionResult(
                channel=None,
                value=value,
                rating=rating,
                color=None,
            )

        class Criterion_HIC_15(Criterion_HIC_15_F50):
            pass

        class Criterion_Head_a3ms(Criterion_Head_a3ms_F50):
            pass

        class Criterion_DAMAGE(Criterion):
            name = "Head DAMAGE (monitoring)"
            source = "§7.3.1.1"

            def damage_channels(self) -> tuple[Channel, ...]:
                """Calculate the X/Y/Z/resultant DAMAGE traces from head angular data."""
                return calculate_damage(
                    self.require_channel(self.ctx.code("?{p}HEAD0000??AAXA")),
                    self.require_channel(self.ctx.code("?{p}HEAD0000??AAYA")),
                    self.require_channel(self.ctx.code("?{p}HEAD0000??AAZA")),
                )

            def calculation(self) -> CriterionResult:
                channel = self.damage_channels()[3]
                value = np.max(channel.get_data())
                return CriterionResult(
                    channel=channel,
                    value=value,
                    rating=0.0,
                    color=None,
                )

        criterion_hic_15 = sub(Criterion_HIC_15)
        criterion_head_a3ms = sub(Criterion_Head_a3ms)
        criterion_damage = sub(Criterion_DAMAGE)

    class Criterion_Neck(Criterion):
        report: EuroNCAP_Side_FarSide
        name = "Neck"

        def calculation(self) -> CriterionResult:

            rating = self.min_of_children()

            # Downscaling
            rating = (
                rating
                / 4
                * self.report.criterion_overall[
                    self.isomme
                ].criterion_head_excursion.max_neck_score
            )
            return CriterionResult(
                channel=None,
                value=rating,
                rating=rating,
                color=None,
            )

        class Criterion_Upper_Neck(Criterion):
            name = "Upper_Neck"

            def calculation(self) -> CriterionResult:

                rating = self.min_of_children()
                return CriterionResult(
                    channel=None,
                    value=rating,
                    rating=rating,
                    color=None,
                )

            class Criterion_Tension_Fz(Criterion):
                name = "Upper Neck Fz tension"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}NECKUP00??FOZ?")
                    return [
                        Limit_G(codes, func=lambda x: 3.74, y_unit="kN", upper=True),
                        Limit_P(codes, func=lambda x: 3.74, y_unit="kN", lower=True),
                    ]

                def calculation(self) -> CriterionResult:
                    channel = self.require_channel(
                        self.ctx.code("?{p}NECKUP00??FOZA")
                    ).convert_unit("kN")
                    value = np.max(channel.get_data())
                    evaluation = self.limits.evaluate(channel)
                    rating = evaluation.get_limit_min_rating()
                    color = evaluation.get_limit_min_color()
                    return CriterionResult(
                        channel=channel,
                        value=value,
                        rating=rating,
                        color=color,
                    )

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

                def calculation(self) -> CriterionResult:
                    channel = self.require_channel(self.ctx.code("?{p}TMONUP00??MOXB"))
                    value = channel.get_data()[np.argmax(np.abs(channel.get_data()))]
                    evaluation = self.limits.evaluate(channel)
                    rating = evaluation.get_limit_min_rating()
                    color = evaluation.get_limit_min_color()
                    return CriterionResult(
                        channel=channel,
                        value=value,
                        rating=rating,
                        color=color,
                    )

            class Criterion_Extension_MyOC(Criterion):
                name = "Upper Neck Extension MyOC"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}TMONUP00??MOY?")
                    return [
                        Limit_P(codes, func=lambda x: -50, y_unit="Nm", upper=True),
                        Limit_G(codes, func=lambda x: -50, y_unit="Nm", lower=True),
                    ]

                def calculation(self) -> CriterionResult:
                    channel = self.require_channel(
                        self.ctx.code("?{p}TMONUP00??MOYB")
                    ).convert_unit("N*m")
                    value = np.min(channel.get_data())
                    evaluation = self.limits.evaluate(channel)
                    rating = evaluation.get_limit_min_rating()
                    color = evaluation.get_limit_min_color()
                    return CriterionResult(
                        channel=channel,
                        value=value,
                        rating=rating,
                        color=color,
                    )

            criterion_tension_fz = sub(Criterion_Tension_Fz)
            criterion_lateral_flexion_mxoc = sub(Criterion_Lateral_Flexion_MxOC)
            criterion_extension_myoc = sub(Criterion_Extension_MyOC)

        class Criterion_Lower_Neck(Criterion):
            name = "Lower_Neck"

            def calculation(self) -> CriterionResult:

                rating = self.min_of_children()
                return CriterionResult(
                    channel=None,
                    value=rating,
                    rating=rating,
                    color=None,
                )

            class Criterion_Tension_Fz(Criterion):
                name = "Lower Neck Fz tension"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}NECKLO00??FOZ?")
                    return [
                        Limit_G(codes, func=lambda x: 3.74, y_unit="kN", upper=True),
                        Limit_P(codes, func=lambda x: 3.74, y_unit="kN", lower=True),
                    ]

                def calculation(self) -> CriterionResult:
                    channel = self.require_channel(
                        self.ctx.code("?{p}NECKLO00??FOZA")
                    ).convert_unit("kN")
                    value = np.max(channel.get_data())
                    evaluation = self.limits.evaluate(channel)
                    rating = evaluation.get_limit_min_rating()
                    color = evaluation.get_limit_min_color()
                    return CriterionResult(
                        channel=channel,
                        value=value,
                        rating=rating,
                        color=color,
                    )

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

                def calculation(self) -> CriterionResult:
                    channel = self.require_channel(
                        self.ctx.code("?{p}TMONLO00??MOXB")
                    ).convert_unit("N*m")
                    value = channel.get_data()[np.argmax(np.abs(channel.get_data()))]
                    evaluation = self.limits.evaluate(channel)
                    rating = evaluation.get_limit_min_rating()
                    color = evaluation.get_limit_min_color()
                    return CriterionResult(
                        channel=channel,
                        value=value,
                        rating=rating,
                        color=color,
                    )

            class Criterion_Extension_My_Base(Criterion):
                name = "Lower Neck Extension My Base"

                def define_limits(self) -> list[Limit]:
                    codes = self.ctx.codes("?{p}TMONLO00??MOY?")
                    return [
                        Limit_P(codes, func=lambda x: -100, y_unit="Nm", upper=True),
                        Limit_G(codes, func=lambda x: -100, y_unit="Nm", lower=True),
                    ]

                def calculation(self) -> CriterionResult:
                    channel = self.require_channel(
                        self.ctx.code("?{p}TMONLO00??MOYB")
                    ).convert_unit("N*m")
                    value = np.min(channel.get_data())
                    evaluation = self.limits.evaluate(channel)
                    rating = evaluation.get_limit_min_rating()
                    color = evaluation.get_limit_min_color()
                    return CriterionResult(
                        channel=channel,
                        value=value,
                        rating=rating,
                        color=color,
                    )

            criterion_tension_fz = sub(Criterion_Tension_Fz)
            criterion_lateral_flexion_mx = sub(Criterion_Lateral_Flexion_Mx)
            criterion_extension_my_base = sub(Criterion_Extension_My_Base)

        criterion_upper_neck = sub(Criterion_Upper_Neck)
        criterion_lower_neck = sub(Criterion_Lower_Neck)

    class Criterion_Chest_Abdomen(Criterion):
        report: EuroNCAP_Side_FarSide
        name = "Chest & Abdomen"

        def calculation(self) -> CriterionResult:

            rating = self.min_of_children()

            # Downscaling
            rating = (
                rating
                / 4
                * self.report.criterion_overall[
                    self.isomme
                ].criterion_head_excursion.max_chest_score
            )
            return CriterionResult(
                channel=None,
                value=rating,
                rating=rating,
                color=None,
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

        def calculation(self) -> CriterionResult:
            rating = self.min_of_children(Role.MODIFIER)
            return CriterionResult(
                channel=None,
                value=rating,
                rating=rating,
                color=None,
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

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}PUBC0000??FOYB")
                ).convert_unit("kN")
                evaluation = self.limits.evaluate(channel)
                value = evaluation.get_limit_min_y(unit="kN")
                rating = evaluation.get_limit_min_rating(interpolate=False)
                color = evaluation.get_limit_min_color()
                return CriterionResult(
                    channel=channel,
                    value=value,
                    rating=rating,
                    color=color,
                )

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

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}LUSP0000??FOYB")
                ).convert_unit("kN")
                evaluation = self.limits.evaluate(channel)
                value = evaluation.get_limit_min_y(unit="kN")
                rating = evaluation.get_limit_min_rating(interpolate=False)
                color = evaluation.get_limit_min_color()
                return CriterionResult(
                    channel=channel,
                    value=value,
                    rating=rating,
                    color=color,
                )

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

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}LUSP0000??FOZB")
                ).convert_unit("kN")
                evaluation = self.limits.evaluate(channel)
                value = evaluation.get_limit_min_y(unit="kN")
                rating = evaluation.get_limit_min_rating(interpolate=False)
                color = evaluation.get_limit_min_color()
                return CriterionResult(
                    channel=channel,
                    value=value,
                    rating=rating,
                    color=color,
                )

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

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}LUSP0000??MOXB")
                ).convert_unit("Nm")
                evaluation = self.limits.evaluate(channel)
                value = evaluation.get_limit_min_y(unit="Nm")
                rating = evaluation.get_limit_min_rating(interpolate=False)
                color = evaluation.get_limit_min_color()
                return CriterionResult(
                    channel=channel,
                    value=value,
                    rating=rating,
                    color=color,
                )

        criterion_pubic_symphysis = sub(Criterion_Pubic_Symphysis)
        criterion_lumbar_fy = sub(Criterion_Lumbar_Fy)
        criterion_lumbar_fz = sub(Criterion_Lumbar_Fz)
        criterion_lumbar_mx = sub(Criterion_Lumbar_Mx)

    class Criterion_Occupant_to_Occupant_Protection(Criterion):
        name = "Modifier for Occupant-to-Occupant Protection"
        role = Role.MODIFIER
        source = "§7.4.2"
        excursion_countermeasure_lacks_interaction_protection: Manual[
            bool,
            manual(
                False,
                source="dual-occupancy assessment",
                doc=(
                    "A far-side countermeasure limits excursion but does not provide "
                    "meaningful occupant-to-occupant head protection. −1 final point."
                ),
            ),
        ]
        dual_occupancy_head_interaction: Manual[
            bool,
            manual(
                False,
                source="dual-occupancy high-speed video",
                doc=(
                    "Either dummy head contacted the adjacent occupant, or the head lower "
                    "performance limits were exceeded. −1 final point."
                ),
            ),
        ]
        countermeasure_asymmetric: Manual[
            bool,
            manual(
                False,
                source="dual-occupancy assessment",
                doc=(
                    "The occupant-interaction countermeasure lacks equivalent protection "
                    "for impacts on both sides. −1 final point."
                ),
            ),
        ]
        protection_zone_not_met: Manual[
            bool,
            manual(
                False,
                source="dual-occupancy assessment",
                doc=(
                    "The required occupant-interaction protection zone was not demonstrated. "
                    "−1 final point."
                ),
            ),
        ]

        def calculation(self) -> CriterionResult:
            failed = self.excursion_countermeasure_lacks_interaction_protection or any(
                (
                    self.dual_occupancy_head_interaction,
                    self.countermeasure_asymmetric,
                    self.protection_zone_not_met,
                )
            )
            value = float(failed)
            # §7.4.2 is a single final-score deduction. The two applicability routes
            # must not stack when an assessment records more than one failure.
            rating = -value
            return CriterionResult(
                channel=None,
                value=value,
                rating=rating,
                color=None,
            )

    criterion_head_excursion = sub(Criterion_Head_Excursion)
    criterion_head = sub(Criterion_Head)
    criterion_neck = sub(Criterion_Neck)
    criterion_chest_abdomen = sub(Criterion_Chest_Abdomen)
    criterion_pelvis_lumbar_modifier = sub(
        Criterion_Pelvis_Lumbar_Modifier, role=Role.MODIFIER
    )
    criterion_occupant_to_occupant_protection = sub(
        Criterion_Occupant_to_Occupant_Protection, role=Role.MODIFIER
    )


class EuroNCAP_Side_FarSide(Report[Overall]):
    _name = "Euro NCAP | Far Side Occupant Protection Sled Test"
    _protocol = PROTOCOL_FARSIDE_2_5
    _protocols = (PROTOCOL_FARSIDE_2_4, PROTOCOL_FARSIDE_2_5)
    Criterion_Overall = Overall

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._available_pages = (
            CoverPage(self),
            CriterionValuesChartPage(
                self,
                spec=criterion_values_chart_spec_for(
                    self, name="Values Chart", title="Values"
                ).with_criteria(lambda report: {
                    isomme: [
                        report.criterion_overall[isomme].criterion_head.criterion_hic_15,
                        report.criterion_overall[isomme].criterion_head.criterion_head_a3ms,
                        report.criterion_overall[isomme].criterion_neck.criterion_upper_neck.criterion_tension_fz,
                        report.criterion_overall[isomme].criterion_neck.criterion_upper_neck.criterion_lateral_flexion_mxoc,
                        report.criterion_overall[isomme].criterion_neck.criterion_upper_neck.criterion_extension_myoc,
                        report.criterion_overall[isomme].criterion_neck.criterion_lower_neck.criterion_tension_fz,
                        report.criterion_overall[isomme].criterion_neck.criterion_lower_neck.criterion_lateral_flexion_mx,
                        report.criterion_overall[isomme].criterion_neck.criterion_lower_neck.criterion_extension_my_base,
                        report.criterion_overall[isomme].criterion_chest_abdomen.criterion_chest_lateral_compression,
                        report.criterion_overall[isomme].criterion_chest_abdomen.criterion_abdomen_lateral_compression,
                        report.criterion_overall[isomme].criterion_pelvis_lumbar_modifier.criterion_pubic_symphysis,
                        report.criterion_overall[isomme].criterion_pelvis_lumbar_modifier.criterion_lumbar_fy,
                        report.criterion_overall[isomme].criterion_pelvis_lumbar_modifier.criterion_lumbar_fz,
                        report.criterion_overall[isomme].criterion_pelvis_lumbar_modifier.criterion_lumbar_mx,
                    ] for isomme in report.isomme_list
                }),
            ),
            CriterionTablePage(
                self,
                name="Rating Table", title="Rating",
                spec=rating_table_spec_for(self).with_criteria(lambda report: {
                    isomme: [
                        report.criterion_overall[isomme].criterion_head,
                        report.criterion_overall[isomme].criterion_neck,
                        report.criterion_overall[isomme].criterion_chest_abdomen,
                        report.criterion_overall[isomme].criterion_pelvis_lumbar_modifier,
                        report.criterion_overall[isomme],
                    ] for isomme in report.isomme_list
                }),
            ),
            CriterionTablePage(
                self,
                name="Values Table", title="Values",
                spec=values_table_spec_for(self).with_criteria(lambda report: {
                    isomme: [
                        report.criterion_overall[isomme].criterion_head.criterion_hic_15,
                        report.criterion_overall[isomme].criterion_head.criterion_head_a3ms,
                        report.criterion_overall[isomme].criterion_neck.criterion_upper_neck.criterion_tension_fz,
                        report.criterion_overall[isomme].criterion_neck.criterion_upper_neck.criterion_lateral_flexion_mxoc,
                        report.criterion_overall[isomme].criterion_neck.criterion_upper_neck.criterion_extension_myoc,
                        report.criterion_overall[isomme].criterion_neck.criterion_lower_neck.criterion_tension_fz,
                        report.criterion_overall[isomme].criterion_neck.criterion_lower_neck.criterion_lateral_flexion_mx,
                        report.criterion_overall[isomme].criterion_neck.criterion_lower_neck.criterion_extension_my_base,
                        report.criterion_overall[isomme].criterion_chest_abdomen.criterion_chest_lateral_compression,
                        report.criterion_overall[isomme].criterion_chest_abdomen.criterion_abdomen_lateral_compression,
                        report.criterion_overall[isomme].criterion_pelvis_lumbar_modifier.criterion_pubic_symphysis,
                        report.criterion_overall[isomme].criterion_pelvis_lumbar_modifier.criterion_lumbar_fy,
                        report.criterion_overall[isomme].criterion_pelvis_lumbar_modifier.criterion_lumbar_fz,
                        report.criterion_overall[isomme].criterion_pelvis_lumbar_modifier.criterion_lumbar_mx,
                    ] for isomme in report.isomme_list
                }),
            ),
            ChannelPlotPage(self, spec=side_head_acceleration_spec_for(self)),
            HICPage(
                self,
                spec=hic_spec_for(
                    self,
                    name="HIC15",
                    title="HIC15",
                    timespan=15,
                ).with_position(
                    lambda report, isomme: report.criterion_overall[isomme].p
                ).with_criterion(
                    lambda report, isomme: report.criterion_overall[
                        isomme
                    ].criterion_head.criterion_hic_15
                ),
            ),
            ChannelPlotPage(
                self,
                spec=channel_plot_spec_for(
                    self, name="Head DAMAGE", title="Head DAMAGE", nrows=2, ncols=2, sharey=True
                ).with_channels(lambda report: {
                    isomme: [[channel] for channel in report.criterion_overall[isomme].criterion_head.criterion_damage.damage_channels()[:4]]
                    for isomme in report.isomme_list
                }),
            ),
            ChannelPlotPage(
                self,
                spec=channel_plot_spec_for(self, name="Upper Neck", title="Upper Neck", nrows=2, ncols=2).with_channels(lambda report: {
                    isomme: [
                        [f"?{report.criterion_overall[isomme].p}NECKUP00??FOZA"],
                        [f"?{report.criterion_overall[isomme].p}TMONUP00??MOXB"],
                        [f"?{report.criterion_overall[isomme].p}TMONUP00??MOYB"],
                    ] for isomme in report.isomme_list
                }),
            ),
            ChannelPlotPage(
                self,
                spec=channel_plot_spec_for(self, name="Lower Neck", title="Lower Neck", nrows=2, ncols=2).with_channels(lambda report: {
                    isomme: [
                        [f"?{report.criterion_overall[isomme].p}NECKLO00??FOZA"],
                        [f"?{report.criterion_overall[isomme].p}TMONLO00??MOXB"],
                        [f"?{report.criterion_overall[isomme].p}TMONLO00??MOYB"],
                    ] for isomme in report.isomme_list
                }),
            ),
            ChannelPlotPage(self, spec=side_chest_lateral_compression_spec_for(self)),
            ChannelPlotPage(self, spec=side_abdomen_lateral_compression_spec_for(self)),
            ChannelPlotPage(
                self,
                spec=channel_plot_spec_for(self, name="Lumbar Load", title="Lumbar Load", nrows=2, ncols=2).with_channels(lambda report: {
                    isomme: [
                        [f"?{report.criterion_overall[isomme].p}LUSP0000??FOYB"],
                        [f"?{report.criterion_overall[isomme].p}LUSP0000??FOZB"],
                        [f"?{report.criterion_overall[isomme].p}LUSP0000??MOXB"],
                    ] for isomme in report.isomme_list
                }),
            ),
            ChannelPlotPage(self, spec=side_pubic_symphysis_force_spec_for(self)),
        )
        self._selected_pages = list(self._available_pages)
