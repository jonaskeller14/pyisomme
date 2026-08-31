from __future__ import annotations

import logging
from typing import Any

import numpy as np

from pyisomme.channel import Channel
from pyisomme.correlation import Correlation_ISO18571
from pyisomme.isomme import Isomme
from pyisomme.limit import Limit
from pyisomme.report.criterion import Criterion, Role, sub
from pyisomme.report.criterion_result import CriterionResult
from pyisomme.report.ctx import from_input
from pyisomme.report.euro_ncap.pages import (
    side_abdomen_lateral_compression_spec_for,
    side_pubic_symphysis_force_spec_for,
)
from pyisomme.report.euro_ncap.protocols import PROTOCOL_VTC_1_0
from pyisomme.report.manual import Manual, manual
from pyisomme.report.page2 import (
    ChannelPlotPage,
    CoverPage,
    CriterionTablePage,
    CriterionTableSpec,
    channel_plot_spec_for,
)
from pyisomme.report.report import Report
from pyisomme.unit import g0

logger = logging.getLogger(__name__)

P = manual(
    "1",
    source="test report",
    doc=(
        "Channel-code position of the assessed occupant. Defaults to the "
        "'Driver position object 1' test-info field when the test carries it."
    ),
)


class Overall(Criterion):
    report: EuroNCAP_Side_Farside_VTC
    name = "Overall"
    role = Role.AGGREGATE
    p: Manual[str, P]

    def __init__(self, report: Report[Any], isomme: Isomme) -> None:
        super().__init__(report, isomme)
        # Also at construction: the pages read `p` when the report is built.
        self.prepare()

    def prepare(self) -> None:
        """Take the occupant's position from the test info before the children read it."""
        p_driver = self.isomme.get_test_info("Driver position object 1")
        if p_driver is not None:
            self.set_derived_input("p", str(p_driver).strip())

    def calculation(self) -> CriterionResult:
        rating = self.min_of_children()
        return CriterionResult(
            channel=None,
            value=rating,
            rating=rating,
            color=None,
        )

    class Criterion_Validation_ISO_Scores(Criterion):
        report: EuroNCAP_Side_Farside_VTC
        role = Role.AGGREGATE
        name = "Validation ISO Scores"
        criteria_iso_score: list[Criterion]

        def calculation(self) -> CriterionResult:
            value = np.min(
                [
                    Criterion.value_of(self.head_avr),
                    Criterion.value_of(self.thsp_04_acr),
                    Criterion.value_of(self.thsp_12_acr),
                    Criterion.value_of(self.pelv_acr),
                    Criterion.value_of(self.b_pillar_acr),
                    Criterion.value_of(self.belt_b3_fo0),
                ]
            )
            rating = True if value >= 0.5 else False
            color = "green" if value >= 0.5 else "red"
            return CriterionResult(
                channel=None,
                value=value,
                rating=rating,
                color=color,
            )

        class Criterion_Individual_ISO_Score(Criterion):
            name = "Individual ISO-Score"
            validate_ignore = {"code_pattern": "ISO-score threshold, read directly"}
            # Deliberately optional: a missing channel leaves the score at nan rather
            # than marking the criterion n/a (see the guard in calculation()).
            ref_channel: Channel | None = None
            _channel: Channel | None = None

            def define_limits(self) -> list[Limit]:
                return [
                    Limit(
                        (),
                        func=lambda x: 0.5,
                        y_unit="1",
                        rating=True,
                        color="green",
                        lower=True,
                    ),
                    Limit(
                        (),
                        func=lambda x: 0.5,
                        y_unit="1",
                        rating=False,
                        color="red",
                        upper=True,
                    ),
                ]

            def calculation(self) -> CriterionResult:
                channel = self._channel
                value = float(np.nan)
                rating = False
                color = "red"
                if channel is not None and self.ref_channel is not None:
                    value = Correlation_ISO18571(
                        reference_channel=self.ref_channel,
                        comparison_channel=channel,
                    ).overall_rating()
                    rating = True if value >= 0.5 else False
                    color = "green" if value >= 0.5 else "red"
                return CriterionResult(
                    channel=channel,
                    value=value,
                    rating=rating,
                    color=color,
                )

        class Criterion_Head_COG_Angular_Velocity_X(Criterion_Individual_ISO_Score):
            name = "Head COG Angular Velocity X"

            def calculation(self) -> CriterionResult:
                self._channel = self.isomme.get_channel(
                    f"1{self.ctx.field('p')}HEAD0000??AVXA",
                    f"1{self.ctx.field('p')}HEADCG00??AVXA",
                )
                self.ref_channel = self.report.isomme_list[0].get_channel(
                    f"1{self.ctx.field('p')}HEAD0000??AVXA",
                    f"1{self.ctx.field('p')}HEADCG00??AVXA",
                )  # FIXME p
                return super().calculation()

        class Criterion_Head_COG_Angular_Velocity_Y(Criterion_Individual_ISO_Score):
            name = "Head COG Angular Velocity Y"

            def calculation(self) -> CriterionResult:
                self._channel = self.isomme.get_channel(
                    f"1{self.ctx.field('p')}HEAD0000??AVYA",
                    f"1{self.ctx.field('p')}HEADCG00??AVYA",
                )
                self.ref_channel = self.report.isomme_list[0].get_channel(
                    f"1{self.ctx.field('p')}HEAD0000??AVYA",
                    f"1{self.ctx.field('p')}HEADCG00??AVYA",
                )
                return super().calculation()

        class Criterion_Head_COG_Angular_Velocity_Z(Criterion_Individual_ISO_Score):
            name = "Head COG Angular Velocity Z"

            def calculation(self) -> CriterionResult:
                self._channel = self.isomme.get_channel(
                    f"1{self.ctx.field('p')}HEAD0000??AVZA",
                    f"1{self.ctx.field('p')}HEADCG00??AVZA",
                )
                self.ref_channel = self.report.isomme_list[0].get_channel(
                    f"1{self.ctx.field('p')}HEAD0000??AVZA",
                    f"1{self.ctx.field('p')}HEADCG00??AVZA",
                )
                return super().calculation()

        class Criterion_Spine_T4_Acceleration_X(Criterion_Individual_ISO_Score):
            name = "T4 Acceleration X"

            def calculation(self) -> CriterionResult:
                self._channel = self.isomme.get_channel(
                    f"1{self.ctx.field('p')}THSP0400??ACXA"
                )
                self.ref_channel = self.report.isomme_list[0].get_channel(
                    f"1{self.ctx.field('p')}THSP0400??ACXA"
                )
                return super().calculation()

        class Criterion_Spine_T4_Acceleration_Y(Criterion_Individual_ISO_Score):
            name = "T4 Acceleration Y"

            def calculation(self) -> CriterionResult:
                self._channel = self.isomme.get_channel(
                    f"1{self.ctx.field('p')}THSP0400??ACYA"
                )
                self.ref_channel = self.report.isomme_list[0].get_channel(
                    f"1{self.ctx.field('p')}THSP0400??ACYA"
                )
                return super().calculation()

        class Criterion_Spine_T4_Acceleration_Z(Criterion_Individual_ISO_Score):
            name = "T4 Acceleration Z"

            def calculation(self) -> CriterionResult:
                self._channel = self.isomme.get_channel(
                    f"1{self.ctx.field('p')}THSP0400??ACZA"
                )
                self.ref_channel = self.report.isomme_list[0].get_channel(
                    f"1{self.ctx.field('p')}THSP0400??ACZA"
                )
                return super().calculation()

        class Criterion_Spine_T12_Acceleration_X(Criterion_Individual_ISO_Score):
            name = "T12 Acceleration X"

            def calculation(self) -> CriterionResult:
                self._channel = self.isomme.get_channel(
                    f"1{self.ctx.field('p')}THSP1200??ACXA"
                )
                self.ref_channel = self.report.isomme_list[0].get_channel(
                    f"1{self.ctx.field('p')}THSP1200??ACXA"
                )
                return super().calculation()

        class Criterion_Spine_T12_Acceleration_Y(Criterion_Individual_ISO_Score):
            name = "T12 Acceleration Y"

            def calculation(self) -> CriterionResult:
                self._channel = self.isomme.get_channel(
                    f"1{self.ctx.field('p')}THSP1200??ACYA"
                )
                self.ref_channel = self.report.isomme_list[0].get_channel(
                    f"1{self.ctx.field('p')}THSP1200??ACYA"
                )
                return super().calculation()

        class Criterion_Spine_T12_Acceleration_Z(Criterion_Individual_ISO_Score):
            name = "T12 Acceleration Z"

            def calculation(self) -> CriterionResult:
                self._channel = self.isomme.get_channel(
                    f"1{self.ctx.field('p')}THSP1200??ACZA"
                )
                self.ref_channel = self.report.isomme_list[0].get_channel(
                    f"1{self.ctx.field('p')}THSP1200??ACZA"
                )
                return super().calculation()

        class Criterion_Pelvis_Acceleration_X(Criterion_Individual_ISO_Score):
            name = "Pelvis Acceleration X"

            def calculation(self) -> CriterionResult:
                self._channel = self.isomme.get_channel(
                    f"1{self.ctx.field('p')}PELV0000??ACXA"
                )
                self.ref_channel = self.report.isomme_list[0].get_channel(
                    f"1{self.ctx.field('p')}PELV0000??ACXA"
                )
                return super().calculation()

        class Criterion_Pelvis_Acceleration_Y(Criterion_Individual_ISO_Score):
            name = "Pelvis Acceleration Y"

            def calculation(self) -> CriterionResult:
                self._channel = self.isomme.get_channel(
                    f"1{self.ctx.field('p')}PELV0000??ACYA"
                )
                self.ref_channel = self.report.isomme_list[0].get_channel(
                    f"1{self.ctx.field('p')}PELV0000??ACYA"
                )
                return super().calculation()

        class Criterion_Pelvis_Acceleration_Z(Criterion_Individual_ISO_Score):
            name = "Pelvis Acceleration Z"

            def calculation(self) -> CriterionResult:
                self._channel = self.isomme.get_channel(
                    f"1{self.ctx.field('p')}PELV0000??ACZA"
                )
                self.ref_channel = self.report.isomme_list[0].get_channel(
                    f"1{self.ctx.field('p')}PELV0000??ACZA"
                )
                return super().calculation()

        class Criterion_B_Pillar_Acceleration_X(Criterion_Individual_ISO_Score):
            report: EuroNCAP_Side_Farside_VTC
            name = "B-Pillar Acceleration X"

            def calculation(self) -> CriterionResult:
                p = self.ctx.field("p")
                p_ref = self.report.criterion_overall[self.report.isomme_list[0]].p
                self._channel = self.isomme.get_channel(
                    f"1{'4' if p == '1' else '6'}BPILLO0000ACXC"
                )
                self.ref_channel = self.report.isomme_list[0].get_channel(
                    f"1{'4' if p_ref == '1' else '6'}BPILLO0000ACXC"
                )
                return super().calculation()

        class Criterion_B_Pillar_Acceleration_Y(Criterion_Individual_ISO_Score):
            report: EuroNCAP_Side_Farside_VTC
            name = "B-Pillar Acceleration Y"

            def calculation(self) -> CriterionResult:
                p = self.ctx.field("p")
                p_ref = self.report.criterion_overall[self.report.isomme_list[0]].p
                self._channel = self.isomme.get_channel(
                    f"1{'4' if p == '1' else '6'}BPILLO0000ACYC"
                )
                self.ref_channel = self.report.isomme_list[0].get_channel(
                    f"1{'4' if p_ref == '1' else '6'}BPILLO0000ACYC"
                )
                return super().calculation()

        class Criterion_B_Pillar_Acceleration_Z(Criterion_Individual_ISO_Score):
            report: EuroNCAP_Side_Farside_VTC
            name = "B-Pillar Acceleration Z"

            def calculation(self) -> CriterionResult:
                p = self.ctx.field("p")
                p_ref = self.report.criterion_overall[self.report.isomme_list[0]].p
                self._channel = self.isomme.get_channel(
                    f"1{'4' if p == '1' else '6'}BPILLO0000ACZC"
                )
                self.ref_channel = self.report.isomme_list[0].get_channel(
                    f"1{'4' if p_ref == '1' else '6'}BPILLO0000ACZC"
                )
                return super().calculation()

        class Criterion_Shoulder_B3_Force(Criterion_Individual_ISO_Score):
            name = "Shoulder Belt (B3) Force"

            def calculation(self) -> CriterionResult:
                self._channel = self.isomme.get_channel(
                    f"1{self.ctx.field('p')}SEBE0003B3FO0C"
                )
                self.ref_channel = self.report.isomme_list[0].get_channel(
                    f"1{self.ctx.field('p')}SEBE0003B3FO0C"
                )
                return super().calculation()

        class Criterion_Reference_ISO_Score(Criterion):
            name = "Reference ISO-Score"
            role = Role.AGGREGATE
            validate_ignore = {"code_pattern": "ISO-score threshold, read directly"}
            #: Attribute names — on this criterion's *parent* — of the per-axis scores it
            #: weights together. Names, not objects: the components are its siblings, and
            #: a ``sub()`` cannot hand one child a reference to another. They are declared
            #: before this one, so they are already calculated when ``calculation()`` runs.
            components: tuple[str, ...] = ()
            values: np.ndarray[Any, Any]
            weights: np.ndarray[Any, Any]

            def define_limits(self) -> list[Limit]:
                return [
                    Limit(
                        (),
                        func=lambda x: 0.5,
                        y_unit="1",
                        rating=True,
                        color="green",
                        lower=True,
                    ),
                    Limit(
                        (),
                        func=lambda x: 0.5,
                        y_unit="1",
                        rating=False,
                        color="red",
                        upper=True,
                    ),
                ]

            @property
            def criteria_individual_iso_score(self) -> tuple[Criterion, ...]:
                parent = self.require(self.parent, f"{self.name}: parent criterion")
                return tuple(getattr(parent, name) for name in self.components)

            def calculation(self) -> CriterionResult:
                channels = [
                    self.require(Criterion.channel_of(c), c.name)
                    for c in self.criteria_individual_iso_score
                ]
                self.values = np.array(
                    [Criterion.value_of(c) for c in self.criteria_individual_iso_score]
                )

                unit = channels[0].unit
                channel_abs_max = np.array(
                    [
                        np.max(np.abs(channel.get_data(unit=unit)))
                        for channel in channels
                    ]
                )
                self.weights = np.array(
                    [
                        channel_abs_max_i / np.sum(channel_abs_max)
                        for channel_abs_max_i in channel_abs_max
                    ]
                )

                value = np.dot(self.weights, self.values)
                rating = True if value >= 0.5 else False
                color = "green" if value >= 0.5 else "red"
                return CriterionResult(
                    channel=None,
                    value=value,
                    rating=rating,
                    color=color,
                )

        class Criterion_Head_COG_Angular_Velocity(Criterion_Reference_ISO_Score):
            name = "Head COG Angular Velocity"
            components = ("head_avx", "head_avy", "head_avz")

        class Criterion_Spine_T4_Acceleration(Criterion_Reference_ISO_Score):
            name = "T4 Acceleration"
            components = ("thsp_04_acx", "thsp_04_acy", "thsp_04_acz")

        class Criterion_Spine_T12_Acceleration(Criterion_Reference_ISO_Score):
            name = "T12 Acceleration"
            components = ("thsp_12_acx", "thsp_12_acy", "thsp_12_acz")

        class Criterion_Pelvis_Acceleration(Criterion_Reference_ISO_Score):
            name = "Pelvis Acceleration"
            components = ("pelv_acx", "pelv_acy", "pelv_acz")

        class Criterion_B_Pillar_Acceleration(Criterion_Reference_ISO_Score):
            name = "B-Pillar Acceleration"
            components = ("b_pillar_acx", "b_pillar_acy", "b_pillar_acz")

        # Declaration order is calculation order, so every resultant follows its three axes.
        head_avx = sub(Criterion_Head_COG_Angular_Velocity_X)
        head_avy = sub(Criterion_Head_COG_Angular_Velocity_Y)
        head_avz = sub(Criterion_Head_COG_Angular_Velocity_Z)
        head_avr = sub(Criterion_Head_COG_Angular_Velocity)

        thsp_04_acx = sub(Criterion_Spine_T4_Acceleration_X)
        thsp_04_acy = sub(Criterion_Spine_T4_Acceleration_Y)
        thsp_04_acz = sub(Criterion_Spine_T4_Acceleration_Z)
        thsp_04_acr = sub(Criterion_Spine_T4_Acceleration)

        thsp_12_acx = sub(Criterion_Spine_T12_Acceleration_X)
        thsp_12_acy = sub(Criterion_Spine_T12_Acceleration_Y)
        thsp_12_acz = sub(Criterion_Spine_T12_Acceleration_Z)
        thsp_12_acr = sub(Criterion_Spine_T12_Acceleration)

        pelv_acx = sub(Criterion_Pelvis_Acceleration_X)
        pelv_acy = sub(Criterion_Pelvis_Acceleration_Y)
        pelv_acz = sub(Criterion_Pelvis_Acceleration_Z)
        pelv_acr = sub(Criterion_Pelvis_Acceleration)

        b_pillar_acx = sub(Criterion_B_Pillar_Acceleration_X)
        b_pillar_acy = sub(Criterion_B_Pillar_Acceleration_Y)
        b_pillar_acz = sub(Criterion_B_Pillar_Acceleration_Z)
        b_pillar_acr = sub(Criterion_B_Pillar_Acceleration)

        belt_b3_fo0 = sub(Criterion_Shoulder_B3_Force)

    class Criterion_Validation_Injury_Criteria(Criterion):
        name = "Validation Injury Criteria"
        role = Role.AGGREGATE

        def calculation(self) -> CriterionResult:
            rating = self.min_of_children()
            return CriterionResult(
                channel=None,
                value=rating,
                rating=rating,
                color=None,
            )

        class Criterion_HIC_15(Criterion):
            name = "HIC 15"
            ref_channel: Channel
            ac_limit: float = np.nan
            ac_test: float = np.nan
            ac_sim: float = np.nan
            r_ac_test: float = np.nan
            r_ac_sim: float = np.nan

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}HICR0015??00RX"),
                    self.ctx.code("?{p}HICRCG15??00RX"),
                )
                self.ref_channel = self.require_channel(
                    self.ctx.code("?{p}HICR0015??00RX"),
                    self.ctx.code("?{p}HICRCG15??00RX"),
                    isomme=self.report.isomme_list[0],
                )

                self.ac_test = self.ref_channel.get_data()[0]
                self.ac_sim = channel.get_data()[0]

                self.ac_limit = 700
                self.r_ac_test = self.ac_test / self.ac_limit
                self.r_ac_sim = self.ac_sim / self.ac_limit

                value = np.abs(self.r_ac_test - self.r_ac_sim)
                rating = self.r_ac_test < 0.5 or value < 0.3
                color = "green" if rating else "red"
                return CriterionResult(
                    channel=channel,
                    value=value,
                    rating=rating,
                    color=color,
                )

        class Criterion_Head_a3ms(Criterion):
            name = "Head a3ms"
            ref_channel: Channel
            ac_limit: float = np.nan
            ac_test: float = np.nan
            ac_sim: float = np.nan
            r_ac_test: float = np.nan
            r_ac_sim: float = np.nan

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}HEAD003C??ACRX"),
                    self.ctx.code("?{p}HEADCG3C??ACRX"),
                )
                self.ref_channel = self.require_channel(
                    self.ctx.code("?{p}HEAD003C??ACRX"),
                    self.ctx.code("?{p}HEADCG3C??ACRX"),
                    isomme=self.report.isomme_list[0],
                )

                self.ac_test = self.ref_channel.get_data(unit=g0)[0]
                self.ac_sim = channel.get_data(unit=g0)[0]

                self.ac_limit = 80
                self.r_ac_test = self.ac_test / self.ac_limit
                self.r_ac_sim = self.ac_sim / self.ac_limit

                value = np.abs(self.r_ac_test - self.r_ac_sim)
                rating = self.r_ac_test < 0.5 or value < 0.3
                color = "green" if rating else "red"
                return CriterionResult(
                    channel=channel,
                    value=value,
                    rating=rating,
                    color=color,
                )

        criterion_hic_15 = sub(Criterion_HIC_15)
        criterion_head_a3ms = sub(Criterion_Head_a3ms)

    validation_iso_scores = sub(
        Criterion_Validation_ISO_Scores, at=from_input(P), role=Role.AGGREGATE
    )
    criterion_validation_injury_criteria = sub(
        Criterion_Validation_Injury_Criteria, at=from_input(P), role=Role.AGGREGATE
    )


class EuroNCAP_Side_Farside_VTC(Report[Overall]):
    _name = "Euro NCAP | Virtual Far Side Simulations"
    _protocol = PROTOCOL_VTC_1_0
    _protocols = (PROTOCOL_VTC_1_0,)
    Criterion_Overall = Overall

    @staticmethod
    def _validation_iso_score_criteria(
        report: EuroNCAP_Side_Farside_VTC,
    ) -> dict[Isomme, list[Criterion]]:
        return {
            isomme: [
                report.criterion_overall[isomme].validation_iso_scores.head_avx,
                report.criterion_overall[isomme].validation_iso_scores.head_avy,
                report.criterion_overall[isomme].validation_iso_scores.head_avz,
                report.criterion_overall[isomme].validation_iso_scores.head_avr,
                report.criterion_overall[isomme].validation_iso_scores.thsp_04_acx,
                report.criterion_overall[isomme].validation_iso_scores.thsp_04_acy,
                report.criterion_overall[isomme].validation_iso_scores.thsp_04_acz,
                report.criterion_overall[isomme].validation_iso_scores.thsp_04_acr,
                report.criterion_overall[isomme].validation_iso_scores.thsp_12_acx,
                report.criterion_overall[isomme].validation_iso_scores.thsp_12_acy,
                report.criterion_overall[isomme].validation_iso_scores.thsp_12_acz,
                report.criterion_overall[isomme].validation_iso_scores.thsp_12_acr,
                report.criterion_overall[isomme].validation_iso_scores.pelv_acx,
                report.criterion_overall[isomme].validation_iso_scores.pelv_acy,
                report.criterion_overall[isomme].validation_iso_scores.pelv_acz,
                report.criterion_overall[isomme].validation_iso_scores.pelv_acr,
                report.criterion_overall[isomme].validation_iso_scores.b_pillar_acx,
                report.criterion_overall[isomme].validation_iso_scores.b_pillar_acy,
                report.criterion_overall[isomme].validation_iso_scores.b_pillar_acz,
                report.criterion_overall[isomme].validation_iso_scores.b_pillar_acr,
                report.criterion_overall[isomme].validation_iso_scores.belt_b3_fo0,
            ]
            for isomme in report.isomme_list[1:]
        }

    @staticmethod
    def _validation_injury_criteria(
        report: EuroNCAP_Side_Farside_VTC,
    ) -> dict[Isomme, list[Criterion]]:
        return {
            isomme: [
                report.criterion_overall[
                    isomme
                ].criterion_validation_injury_criteria.criterion_hic_15,
                report.criterion_overall[
                    isomme
                ].criterion_validation_injury_criteria.criterion_head_a3ms,
            ]
            for isomme in report.isomme_list
        }

    @staticmethod
    def _validation_row_label(criterion: Criterion) -> str:
        return f"{criterion.name}"

    @staticmethod
    def _validation_iso_score_cell_text(criterion: Criterion) -> str:
        return f"{Criterion.value_of(criterion):.1%}"

    @staticmethod
    def _validation_injury_cell_text(criterion: Criterion) -> str:
        injury_criteria = Overall.Criterion_Validation_Injury_Criteria
        if not isinstance(
            criterion,
            (injury_criteria.Criterion_HIC_15, injury_criteria.Criterion_Head_a3ms),
        ):
            raise TypeError("Expected a validation injury criterion.")
        return f"{criterion.r_ac_sim:.1%}\n{Criterion.value_of(criterion):.1%}"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._available_pages = (
            CoverPage(self),
            CriterionTablePage(
                self,
                name="Validation ISO-Score Table", title="Validation ISO-Score",
                spec=CriterionTableSpec(
                    criteria=self._validation_iso_score_criteria,
                    row_label=self._validation_row_label,
                    cell_text=self._validation_iso_score_cell_text,
                ),
            ),
            CriterionTablePage(
                self,
                name="Validation Injury-Criteria Percentage Table", title="Validation Injury-Criteria Percentage",
                spec=CriterionTableSpec(
                    criteria=self._validation_injury_criteria,
                    row_label=self._validation_row_label,
                    cell_text=self._validation_injury_cell_text,
                ),
            ),
            ChannelPlotPage(self, spec=channel_plot_spec_for(self, name="Head Acceleration", title="Head Acceleration", nrows=2, ncols=2, sharey=True).with_channels(lambda report: {
                isomme: [[f"?{report.criterion_overall[isomme].p}HEAD??????AC{axis}A"] for axis in "XYZR"]
                for isomme in report.isomme_list
            })),
            ChannelPlotPage(self, spec=channel_plot_spec_for(self, name="Chest Lateral Compression", title="Chest Lateral Compression", nrows=3, ncols=2, sharey=True).with_channels(lambda report: {
                isomme: [[f"?{report.criterion_overall[isomme].p}TRRILE01??DSYC"], [f"?{report.criterion_overall[isomme].p}TRRIRI01??DSYC"], [f"?{report.criterion_overall[isomme].p}TRRILE02??DSYC"], [f"?{report.criterion_overall[isomme].p}TRRIRI02??DSYC"], [f"?{report.criterion_overall[isomme].p}TRRILE03??DSYC"], [f"?{report.criterion_overall[isomme].p}TRRIRI03??DSYC"]]
                for isomme in report.isomme_list
            })),
            ChannelPlotPage(self, spec=side_abdomen_lateral_compression_spec_for(self)),
            ChannelPlotPage(self, spec=side_pubic_symphysis_force_spec_for(self)),
        )
        self._selected_pages = list(self._available_pages)
