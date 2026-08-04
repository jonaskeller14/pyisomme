from __future__ import annotations

from pyisomme.isomme import Isomme
from pyisomme.report.page import Page_Cover, Page_Criterion_Values_Table
from pyisomme.report.report import Report
from pyisomme.report.criterion import Criterion
from pyisomme.correlation import Correlation_ISO18571
from pyisomme.channel import Channel
from pyisomme.unit import g0
from pyisomme.limit import Limit
from pyisomme.report.euro_ncap.side_pole import EuroNCAP_Side_Pole

import logging
import numpy as np
from typing import Any


logger = logging.getLogger(__name__)


class Overall(Criterion):
    report: EuroNCAP_Side_Farside_VTC
    name = "Overall"
    # TODO(input): make this a manual input as in EuroNCAP_Side_Pole/Side_Barrier —
    #   declare `p: Manual[int, manual(1, ...)]`, derive it from the
    #   "Driver position object 1" test info, and add the sync_position()/
    #   rebuild_child() pair, so the occupant is not pinned to position 1.
    p: int = 1

    def __init__(self, report: Report, isomme: Isomme) -> None:
        super().__init__(report, isomme)

        p_driver = isomme.get_test_info("Driver position object 1")
        if p_driver is not None:
            self.p = int(p_driver)

        self.validation_iso_scores = self.Criterion_Validation_ISO_Scores(report, isomme, p=self.p)
        self.criterion_validation_injury_criteria = self.Criterion_Validation_Injury_Criteria(report, isomme, p=self.p)

    def calculation(self) -> None:
        self.validation_iso_scores.calculate()
        self.criterion_validation_injury_criteria.calculate()

        self.rating = np.min([
            self.validation_iso_scores.rating,
            self.criterion_validation_injury_criteria.rating,
        ])

    class Criterion_Validation_ISO_Scores(Criterion):
        report: EuroNCAP_Side_Farside_VTC
        name = "Validation ISO Scores"
        criteria_iso_score: list[Criterion]

        def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
            super().__init__(report, isomme)

            self.p = p

            self.head_avx = self.Criterion_Head_COG_Angular_Velocity_X(report, isomme, p=self.p)
            self.head_avy = self.Criterion_Head_COG_Angular_Velocity_Y(report, isomme, p=self.p)
            self.head_avz = self.Criterion_Head_COG_Angular_Velocity_Z(report, isomme, p=self.p)
            self.head_avr = self.Criterion_Head_COG_Angular_Velocity(report, isomme, self.head_avx, self.head_avy, self.head_avz)

            self.thsp_04_acx = self.Criterion_Spine_T4_Acceleration_X(report, isomme, p=self.p)
            self.thsp_04_acy = self.Criterion_Spine_T4_Acceleration_Y(report, isomme, p=self.p)
            self.thsp_04_acz = self.Criterion_Spine_T4_Acceleration_Z(report, isomme, p=self.p)
            self.thsp_04_acr = self.Criterion_Spine_T4_Acceleration(report, isomme, self.thsp_04_acx, self.thsp_04_acy, self.thsp_04_acz)

            self.thsp_12_acx = self.Criterion_Spine_T12_Acceleration_X(report, isomme, p=self.p)
            self.thsp_12_acy = self.Criterion_Spine_T12_Acceleration_Y(report, isomme, p=self.p)
            self.thsp_12_acz = self.Criterion_Spine_T12_Acceleration_Z(report, isomme, p=self.p)
            self.thsp_12_acr = self.Criterion_Spine_T12_Acceleration(report, isomme, self.thsp_12_acx, self.thsp_12_acy, self.thsp_12_acz)

            self.pelv_acx = self.Criterion_Pelvis_Acceleration_X(report, isomme, p=self.p)
            self.pelv_acy = self.Criterion_Pelvis_Acceleration_Y(report, isomme, p=self.p)
            self.pelv_acz = self.Criterion_Pelvis_Acceleration_Z(report, isomme, p=self.p)
            self.pelv_acr = self.Criterion_Pelvis_Acceleration(report, isomme, self.pelv_acx, self.pelv_acy, self.pelv_acz)

            self.b_pillar_acx = self.Criterion_B_Pillar_Acceleration_X(report, isomme, p=self.p)
            self.b_pillar_acy = self.Criterion_B_Pillar_Acceleration_Y(report, isomme, p=self.p)
            self.b_pillar_acz = self.Criterion_B_Pillar_Acceleration_Z(report, isomme, p=self.p)
            self.b_pillar_acr = self.Criterion_B_Pillar_Acceleration(report, isomme, self.b_pillar_acx, self.b_pillar_acy, self.b_pillar_acz)

            self.belt_b3_fo0 = self.Criterion_Shoulder_B3_Force(report, isomme, p=self.p)

        def calculation(self) -> None:
            self.head_avx.calculate()
            self.head_avy.calculate()
            self.head_avz.calculate()
            self.head_avr.calculate()

            self.thsp_04_acx.calculate()
            self.thsp_04_acy.calculate()
            self.thsp_04_acz.calculate()
            self.thsp_04_acr.calculate()

            self.thsp_12_acx.calculate()
            self.thsp_12_acy.calculate()
            self.thsp_12_acz.calculate()
            self.thsp_12_acr.calculate()

            self.pelv_acx.calculate()
            self.pelv_acy.calculate()
            self.pelv_acz.calculate()
            self.pelv_acr.calculate()

            self.b_pillar_acx.calculate()
            self.b_pillar_acy.calculate()
            self.b_pillar_acz.calculate()
            self.b_pillar_acr.calculate()

            self.belt_b3_fo0.calculate()

            self.value = np.min([
                self.head_avr.value,
                self.thsp_04_acr.value,
                self.thsp_12_acr.value,
                self.pelv_acr.value,
                self.b_pillar_acr.value,
                self.belt_b3_fo0.value
            ])
            self.rating = True if self.value >= 0.5 else False
            self.color = "green" if self.value >= 0.5 else "red"

        class Criterion_Individual_ISO_Score(Criterion):
            name = "Individual ISO-Score"
            validate_ignore = {"code_pattern": "ISO-score threshold, read directly"}
            # Deliberately optional: a missing channel leaves the score at nan rather
            # than marking the criterion n/a (see the guard in calculation()).
            ref_channel: Channel | None = None

            def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                super().__init__(report, isomme)

                self.p = p

                self.extend_limit_list([
                    Limit([], func=lambda x: 0.5, y_unit="1", rating=True, color="green", lower=True),
                    Limit([], func=lambda x: 0.5, y_unit="1", rating=False, color="red", upper=True),
                ])

            def calculation(self) -> None:
                if self.channel is not None and self.ref_channel is not None:
                    self.value = Correlation_ISO18571(reference_channel=self.ref_channel,
                                                      comparison_channel=self.channel).overall_rating()
                    self.rating = True if self.value >= 0.5 else False
                    self.color = "green" if self.value >= 0.5 else "red"

        class Criterion_Head_COG_Angular_Velocity_X(Criterion_Individual_ISO_Score):
            name = "Head COG Angular Velocity X"

            def calculation(self) -> None:
                self.channel = self.isomme.get_channel(f"1{self.p}HEAD0000??AVXA", f"1{self.p}HEADCG00??AVXA")
                self.ref_channel = self.report.isomme_list[0].get_channel(f"1{self.p}HEAD0000??AVXA", f"1{self.p}HEADCG00??AVXA")  # FIXME p
                super().calculation()

        class Criterion_Head_COG_Angular_Velocity_Y(Criterion_Individual_ISO_Score):
            name = "Head COG Angular Velocity Y"

            def calculation(self) -> None:
                self.channel = self.isomme.get_channel(f"1{self.p}HEAD0000??AVYA", f"1{self.p}HEADCG00??AVYA")
                self.ref_channel = self.report.isomme_list[0].get_channel(f"1{self.p}HEAD0000??AVYA", f"1{self.p}HEADCG00??AVYA")
                super().calculation()

        class Criterion_Head_COG_Angular_Velocity_Z(Criterion_Individual_ISO_Score):
            name = "Head COG Angular Velocity Z"

            def calculation(self) -> None:
                self.channel = self.isomme.get_channel(f"1{self.p}HEAD0000??AVZA", f"1{self.p}HEADCG00??AVZA")
                self.ref_channel = self.report.isomme_list[0].get_channel(f"1{self.p}HEAD0000??AVZA", f"1{self.p}HEADCG00??AVZA")
                super().calculation()

        class Criterion_Spine_T4_Acceleration_X(Criterion_Individual_ISO_Score):
            name = "T4 Acceleration X"

            def calculation(self) -> None:
                self.channel = self.isomme.get_channel(f"1{self.p}THSP0400??ACXA")
                self.ref_channel = self.report.isomme_list[0].get_channel(f"1{self.p}THSP0400??ACXA")
                super().calculation()

        class Criterion_Spine_T4_Acceleration_Y(Criterion_Individual_ISO_Score):
            name = "T4 Acceleration Y"

            def calculation(self) -> None:
                self.channel = self.isomme.get_channel(f"1{self.p}THSP0400??ACYA")
                self.ref_channel = self.report.isomme_list[0].get_channel(f"1{self.p}THSP0400??ACYA")
                super().calculation()

        class Criterion_Spine_T4_Acceleration_Z(Criterion_Individual_ISO_Score):
            name = "T4 Acceleration Z"

            def calculation(self) -> None:
                self.channel = self.isomme.get_channel(f"1{self.p}THSP0400??ACZA")
                self.ref_channel = self.report.isomme_list[0].get_channel(f"1{self.p}THSP0400??ACZA")
                super().calculation()

        class Criterion_Spine_T12_Acceleration_X(Criterion_Individual_ISO_Score):
            name = "T12 Acceleration X"

            def calculation(self) -> None:
                self.channel = self.isomme.get_channel(f"1{self.p}THSP1200??ACXA")
                self.ref_channel = self.report.isomme_list[0].get_channel(f"1{self.p}THSP1200??ACXA")
                super().calculation()

        class Criterion_Spine_T12_Acceleration_Y(Criterion_Individual_ISO_Score):
            name = "T12 Acceleration Y"

            def calculation(self) -> None:
                self.channel = self.isomme.get_channel(f"1{self.p}THSP1200??ACYA")
                self.ref_channel = self.report.isomme_list[0].get_channel(f"1{self.p}THSP1200??ACYA")
                super().calculation()

        class Criterion_Spine_T12_Acceleration_Z(Criterion_Individual_ISO_Score):
            name = "T12 Acceleration Z"

            def calculation(self) -> None:
                self.channel = self.isomme.get_channel(f"1{self.p}THSP1200??ACZA")
                self.ref_channel = self.report.isomme_list[0].get_channel(f"1{self.p}THSP1200??ACZA")
                super().calculation()

        class Criterion_Pelvis_Acceleration_X(Criterion_Individual_ISO_Score):
            name = "Pelvis Acceleration X"

            def calculation(self) -> None:
                self.channel = self.isomme.get_channel(f"1{self.p}PELV0000??ACXA")
                self.ref_channel = self.report.isomme_list[0].get_channel(f"1{self.p}PELV0000??ACXA")
                super().calculation()

        class Criterion_Pelvis_Acceleration_Y(Criterion_Individual_ISO_Score):
            name = "Pelvis Acceleration Y"

            def calculation(self) -> None:
                self.channel = self.isomme.get_channel(f"1{self.p}PELV0000??ACYA")
                self.ref_channel = self.report.isomme_list[0].get_channel(f"1{self.p}PELV0000??ACYA")
                super().calculation()

        class Criterion_Pelvis_Acceleration_Z(Criterion_Individual_ISO_Score):
            name = "Pelvis Acceleration Z"

            def calculation(self) -> None:
                self.channel = self.isomme.get_channel(f"1{self.p}PELV0000??ACZA")
                self.ref_channel = self.report.isomme_list[0].get_channel(f"1{self.p}PELV0000??ACZA")
                super().calculation()

        class Criterion_B_Pillar_Acceleration_X(Criterion_Individual_ISO_Score):
            report: EuroNCAP_Side_Farside_VTC
            name = "B-Pillar Acceleration X"

            def calculation(self) -> None:
                self.channel = self.isomme.get_channel(f"1{4 if self.p == 1 else 6}BPILLO0000ACXC")
                self.ref_channel = self.report.isomme_list[0].get_channel(f"1{4 if self.report.criterion_overall[self.report.isomme_list[0]].p == 1 else 6}BPILLO0000ACXC")
                super().calculation()

        class Criterion_B_Pillar_Acceleration_Y(Criterion_Individual_ISO_Score):
            report: EuroNCAP_Side_Farside_VTC
            name = "B-Pillar Acceleration Y"

            def calculation(self) -> None:
                self.channel = self.isomme.get_channel(f"1{4 if self.p == 1 else 6}BPILLO0000ACYC")
                self.ref_channel = self.report.isomme_list[0].get_channel(f"1{4 if self.report.criterion_overall[self.report.isomme_list[0]].p == 1 else 6}BPILLO0000ACYC")
                super().calculation()

        class Criterion_B_Pillar_Acceleration_Z(Criterion_Individual_ISO_Score):
            report: EuroNCAP_Side_Farside_VTC
            name = "B-Pillar Acceleration Z"

            def calculation(self) -> None:
                self.channel = self.isomme.get_channel(f"1{4 if self.p == 1 else 6}BPILLO0000ACZC")
                self.ref_channel = self.report.isomme_list[0].get_channel(f"1{4 if self.report.criterion_overall[self.report.isomme_list[0]].p == 1 else 6}BPILLO0000ACZC")
                super().calculation()

        class Criterion_Shoulder_B3_Force(Criterion_Individual_ISO_Score):
            name = "Shoulder Belt (B3) Force"

            def calculation(self) -> None:
                self.channel = self.isomme.get_channel(f"1{self.p}SEBE0003B3FO0C")
                self.ref_channel = self.report.isomme_list[0].get_channel(f"1{self.p}SEBE0003B3FO0C")
                super().calculation()

        class Criterion_Reference_ISO_Score(Criterion):
            name = "Reference ISO-Score"
            validate_ignore = {"code_pattern": "ISO-score threshold, read directly"}
            criteria_individual_iso_score: tuple[Criterion, ...]
            values: np.ndarray
            weights: np.ndarray

            def __init__(self, report: Report, isomme: Isomme, *criteria_individual_iso_score: Criterion) -> None:
                super().__init__(report, isomme)

                self.criteria_individual_iso_score = criteria_individual_iso_score

                self.extend_limit_list([
                    Limit([], func=lambda x: 0.5, y_unit="1", rating=True, color="green", lower=True),
                    Limit([], func=lambda x: 0.5, y_unit="1", rating=False, color="red", upper=True),
                ])

            def calculation(self) -> None:
                channels = [self.require(c.channel, c.name) for c in self.criteria_individual_iso_score]
                self.values = np.array([c.value for c in self.criteria_individual_iso_score])

                unit = channels[0].unit
                channel_abs_max = np.array([np.max(np.abs(channel.get_data(unit=unit))) for channel in channels])
                self.weights = np.array([channel_abs_max_i / np.sum(channel_abs_max) for channel_abs_max_i in channel_abs_max])

                self.value = np.dot(self.weights, self.values)
                self.rating = True if self.value >= 0.5 else False
                self.color = "green" if self.value >= 0.5 else "red"

        class Criterion_Head_COG_Angular_Velocity(Criterion_Reference_ISO_Score):
            name = "Head COG Angular Velocity"

        class Criterion_Spine_T4_Acceleration(Criterion_Reference_ISO_Score):
            name = "T4 Acceleration"

        class Criterion_Spine_T12_Acceleration(Criterion_Reference_ISO_Score):
            name = "T12 Acceleration"

        class Criterion_Pelvis_Acceleration(Criterion_Reference_ISO_Score):
            name = "Pelvis Acceleration"

        class Criterion_B_Pillar_Acceleration(Criterion_Reference_ISO_Score):
            name = "B-Pillar Acceleration"

    class Criterion_Validation_Injury_Criteria(Criterion):
        name = "Validation Injury Criteria"

        def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
            super().__init__(report, isomme)

            self.p = p

            self.criterion_hic_15 = self.Criterion_HIC_15(report, isomme, p=self.p)
            self.criterion_head_a3ms = self.Criterion_Head_a3ms(report, isomme, p=self.p)

        def calculation(self) -> None:
            self.criterion_hic_15.calculate()
            self.criterion_head_a3ms.calculate()

            self.rating = np.min([
                self.criterion_hic_15.rating,
                self.criterion_head_a3ms.rating,
            ])

        class Criterion_HIC_15(Criterion):
            name = "HIC 15"
            ref_channel: Channel
            ac_limit: float = np.nan
            ac_test: float = np.nan
            ac_sim: float = np.nan
            r_ac_test: float = np.nan
            r_ac_sim: float = np.nan

            def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                super().__init__(report, isomme)

                self.p = p

            def calculation(self) -> None:
                self.channel = self.require_channel(f"?{self.p}HICR0015??00RX", f"?{self.p}HICRCG15??00RX")
                self.ref_channel = self.require_channel(f"?{self.p}HICR0015??00RX", f"?{self.p}HICRCG15??00RX", isomme=self.report.isomme_list[0])

                self.ac_test = self.ref_channel.get_data()[0]
                self.ac_sim = self.channel.get_data()[0]

                self.ac_limit = 700
                self.r_ac_test = self.ac_test / self.ac_limit
                self.r_ac_sim = self.ac_sim / self.ac_limit

                self.value = np.abs(self.r_ac_test - self.r_ac_sim)
                self.rating = self.r_ac_test < 0.5 or self.value < 0.3
                self.color = "green" if self.rating else "red"

        class Criterion_Head_a3ms(Criterion):
            name = "Head a3ms"
            ref_channel: Channel
            ac_limit: float = np.nan
            ac_test: float = np.nan
            ac_sim: float = np.nan
            r_ac_test: float = np.nan
            r_ac_sim: float = np.nan

            def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                super().__init__(report, isomme)

                self.p = p

            def calculation(self) -> None:
                self.channel = self.require_channel(f"?{self.p}HEAD003C??ACRX", f"?{self.p}HEADCG3C??ACRX")
                self.ref_channel = self.require_channel(f"?{self.p}HEAD003C??ACRX", f"?{self.p}HEADCG3C??ACRX", isomme=self.report.isomme_list[0])

                self.ac_test = self.ref_channel.get_data(unit=g0)[0]
                self.ac_sim = self.channel.get_data(unit=g0)[0]

                self.ac_limit = 80
                self.r_ac_test = self.ac_test / self.ac_limit
                self.r_ac_sim = self.ac_sim / self.ac_limit

                self.value = np.abs(self.r_ac_test - self.r_ac_sim)
                self.rating = self.r_ac_test < 0.5 or self.value < 0.3
                self.color = "green" if self.rating else "red"


class EuroNCAP_Side_Farside_VTC(Report[Overall]):
    name = "Euro NCAP | Virtual Far Side Simulations"
    protocol = "1.0"
    protocols = {
        "1.0": "Version 1.0 (15.06.2023) [references/Euro-NCAP/euro-ncap-vtc-simulation-and-assessment-protocol-v10.pdf]"
    }

    #: The report's criterion tree, defined at module level (see `Overall`).
    Criterion_Overall = Overall

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.pages = [
            Page_Cover(self),

            self.Page_Validation_ISO_Score_Table(self),
            self.Page_Validation_Injury_Criteria_Percentage_Table(self),
            self.Page_Head_Acceleration(self),
            self.Page_Chest_Lateral_Compression(self),
            self.Page_Abdomen_Lateral_Compression(self),
            self.Page_Pubic_Symphysis_Force(self),
        ]


    class Page_Validation_ISO_Score_Table(Page_Criterion_Values_Table):
        report: EuroNCAP_Side_Farside_VTC
        name = "Validation ISO-Score Table"
        title = "Validation ISO-Score"
        row_label = staticmethod(lambda criterion: f"{criterion.name}")
        cell_text = staticmethod(lambda criterion: f"{criterion.value:.1%}")

        def __init__(self, report: EuroNCAP_Side_Farside_VTC) -> None:
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].validation_iso_scores.head_avx,
                self.report.criterion_overall[isomme].validation_iso_scores.head_avy,
                self.report.criterion_overall[isomme].validation_iso_scores.head_avz,
                self.report.criterion_overall[isomme].validation_iso_scores.head_avr,
                self.report.criterion_overall[isomme].validation_iso_scores.thsp_04_acx,
                self.report.criterion_overall[isomme].validation_iso_scores.thsp_04_acy,
                self.report.criterion_overall[isomme].validation_iso_scores.thsp_04_acz,
                self.report.criterion_overall[isomme].validation_iso_scores.thsp_04_acr,
                self.report.criterion_overall[isomme].validation_iso_scores.thsp_12_acx,
                self.report.criterion_overall[isomme].validation_iso_scores.thsp_12_acy,
                self.report.criterion_overall[isomme].validation_iso_scores.thsp_12_acz,
                self.report.criterion_overall[isomme].validation_iso_scores.thsp_12_acr,
                self.report.criterion_overall[isomme].validation_iso_scores.pelv_acx,
                self.report.criterion_overall[isomme].validation_iso_scores.pelv_acy,
                self.report.criterion_overall[isomme].validation_iso_scores.pelv_acz,
                self.report.criterion_overall[isomme].validation_iso_scores.pelv_acr,
                self.report.criterion_overall[isomme].validation_iso_scores.b_pillar_acx,
                self.report.criterion_overall[isomme].validation_iso_scores.b_pillar_acy,
                self.report.criterion_overall[isomme].validation_iso_scores.b_pillar_acz,
                self.report.criterion_overall[isomme].validation_iso_scores.b_pillar_acr,
                self.report.criterion_overall[isomme].validation_iso_scores.belt_b3_fo0,
            ] for isomme in self.report.isomme_list[1:]}

    class Page_Validation_Injury_Criteria_Percentage_Table(Page_Criterion_Values_Table):
        report: EuroNCAP_Side_Farside_VTC
        name = "Validation Injury-Criteria Percentage Table"
        title = "Validation Injury-Criteria Percentage"
        row_label = staticmethod(lambda criterion: f"{criterion.name}")
        cell_text = staticmethod(lambda criterion: f"{criterion.r_ac_sim:.1%}\n{criterion.value:.1%}")

        def __init__(self, report: EuroNCAP_Side_Farside_VTC) -> None:
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_validation_injury_criteria.criterion_hic_15,
                self.report.criterion_overall[isomme].criterion_validation_injury_criteria.criterion_head_a3ms,
            ] for isomme in self.report.isomme_list}

    class Page_Validation_Injury_Criteria_Difference_Table(Page_Criterion_Values_Table):
        pass

    class Page_Head_Acceleration(EuroNCAP_Side_Pole.Page_Head_Acceleration):
        pass

    class Page_Chest_Lateral_Compression(EuroNCAP_Side_Pole.Page_Chest_Lateral_Compression):
        pass

    class Page_Abdomen_Lateral_Compression(EuroNCAP_Side_Pole.Page_Abdomen_Lateral_Compression):
        pass

    class Page_Pubic_Symphysis_Force(EuroNCAP_Side_Pole.Page_Pubic_Symphysis_Force):
        pass

