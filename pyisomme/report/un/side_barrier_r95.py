from __future__ import annotations

import logging
from typing import Any

import numpy as np

from pyisomme.isomme import Isomme
from pyisomme.limit import Limit
from pyisomme.report.criterion import Criterion, Role, sub
from pyisomme.report.criterion_result import CriterionResult
from pyisomme.report.ctx import from_input
from pyisomme.report.euro_ncap.pages import (
    side_head_acceleration_spec_for,
    side_pubic_symphysis_force_spec_for,
)
from pyisomme.report.manual import Manual, manual
from pyisomme.report.page2 import (
    ChannelPlotPage,
    CoverPage,
    CriterionTablePage,
    CriterionValuesChartPage,
    criterion_values_chart_spec_for,
    values_table_spec_for,
)
from pyisomme.report.report import Report
from pyisomme.report.un.frontal_50kmh_r137 import (
    Criterion_HPC36 as Criterion_HPC36_R137,
)
from pyisomme.report.un.limits import Limit_Fail, Limit_Pass
from pyisomme.report.un.pages import (
    side_barrier_abdomen_force_spec_for,
    side_barrier_chest_deflection_spec_for,
    side_barrier_chest_vc_spec_for,
)
from pyisomme.report.un.protocols import PROTOCOL_R95_2023
from pyisomme.report.un.side_pole_r135 import Overall as Overall_Side_Pole_R135

logger = logging.getLogger(__name__)

P = manual(
    "1",
    source="test report",
    doc=(
        "Channel-code position of the struck-side occupant — the only occupant "
        "the regulation assesses. Defaults to the 'Driver position object 1' "
        "test-info field when the test carries it."
    ),
)


class Overall(Criterion):
    name = "Overall"
    role = Role.AGGREGATE
    p: Manual[str, P]

    def __init__(self, report: Report[Any], isomme: Isomme) -> None:
        super().__init__(report, isomme)
        # Also at construction: the pages read `p` when the report is built.
        self.prepare()

    def prepare(self) -> None:
        """Take the struck-side position from the test info before the occupant reads it."""
        p = self.isomme.get_test_info("Driver position object 1")
        if p is not None:
            self.set_derived_input("p", str(p).strip())

    def calculation(self) -> CriterionResult:
        rating = self.rating_of(self.criterion_dummy)
        return CriterionResult(
            channel=None,
            value=rating,
            rating=rating,
            color=None,
        )

    class Criterion_Dummy(Criterion):
        name = "Dummy"
        role = Role.AGGREGATE

        def calculation(self) -> CriterionResult:
            rating = self.min_of_children()
            return CriterionResult(
                channel=None,
                value=rating,
                rating=rating,
                color=None,
            )

        class Criterion_HPC36(Criterion_HPC36_R137):
            pass

        class Criterion_Chest_Lateral_Deflection(Criterion):
            name = "Chest Lateral Deflection"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}RIBS??????DSY?")
                return [
                    Limit_Fail(codes, func=lambda x: -42, y_unit="mm", upper=True),
                    Limit_Pass(codes, func=lambda x: -42, y_unit="mm", lower=True),
                    Limit_Fail(codes, func=lambda x: 42, y_unit="mm", lower=True),
                ]

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}RIBSLE00??DSYC")
                ).convert_unit("mm")
                value = np.min(channel.get_data())
                evaluation = self.limits.evaluate(channel)
                rating = evaluation.get_limit_min_rating(interpolate=False)
                color = evaluation.get_limit_min_color()
                return CriterionResult(
                    channel=channel,
                    value=value,
                    rating=rating,
                    color=color,
                )

        class Criterion_Chest_Lateral_VC(Criterion):
            name = "Chest Lateral VC"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes(
                    "?{p}VCCR00????VEY?", "?{p}VCCRLE????VEY?", "?{p}VCCRRI????VEY?"
                )
                return [
                    Limit_Fail(codes, func=lambda x: -1, y_unit="m/s", upper=True),
                    Limit_Pass(codes, func=lambda x: -1, y_unit="m/s", lower=True),
                    Limit_Pass(codes, func=lambda x: 1, y_unit="m/s", upper=True),
                    Limit_Fail(codes, func=lambda x: 1, y_unit="m/s", lower=True),
                ]

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}VCCRLE00??VEYC")
                ).convert_unit("m/s")
                value = np.min(channel.get_data())
                evaluation = self.limits.evaluate(channel)
                rating = evaluation.get_limit_min_rating(interpolate=False)
                color = evaluation.get_limit_min_color()
                return CriterionResult(
                    channel=channel,
                    value=value,
                    rating=rating,
                    color=color,
                )

        class Criterion_Pubic_Symphysis_Force(
            Overall_Side_Pole_R135.Criterion_Dummy.Criterion_Pubic_Symphysis_Force
        ):
            pass

        class Criterion_Abdomen_Force(Criterion):
            name = "Abdomen Peak Force"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}ABDO??????FOY?")
                return [
                    Limit_Fail(codes, func=lambda x: -2.5, y_unit="kN", upper=True),
                    Limit_Pass(codes, func=lambda x: -2.5, y_unit="kN", lower=True),
                ]

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}ABDOLE00??FOYB")
                ).convert_unit("kN")
                value = np.min(channel.get_data())
                evaluation = self.limits.evaluate(channel)
                rating = evaluation.get_limit_min_rating(interpolate=False)
                color = evaluation.get_limit_min_color()
                return CriterionResult(
                    channel=channel,
                    value=value,
                    rating=rating,
                    color=color,
                )

        criterion_hpc36 = sub(Criterion_HPC36)
        criterion_chest_lateral_deflection = sub(Criterion_Chest_Lateral_Deflection)
        criterion_chest_lateral_vc = sub(Criterion_Chest_Lateral_VC)
        criterion_pubic_symphysis_force = sub(Criterion_Pubic_Symphysis_Force)
        criterion_abdomen_force = sub(Criterion_Abdomen_Force)

    criterion_dummy = sub(Criterion_Dummy, at=from_input(P), role=Role.AGGREGATE)


class UN_Side_Barrier_R95(Report[Overall]):
    _name = "UN-R95 | Barrier Side Impact at 50 km/h"
    _protocol = PROTOCOL_R95_2023
    _protocols = (PROTOCOL_R95_2023,)
    Criterion_Overall = Overall

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._available_pages = (
            CoverPage(self),
            CriterionValuesChartPage(self, spec=criterion_values_chart_spec_for(
                self, name="Values Chart", title="Values"
            ).with_criteria(lambda report: {
                isomme: [
                        report.overall(isomme).criterion_dummy.criterion_hpc36,
                        report.overall(isomme).criterion_dummy.criterion_chest_lateral_deflection,
                        report.overall(isomme).criterion_dummy.criterion_chest_lateral_vc,
                        report.overall(isomme).criterion_dummy.criterion_pubic_symphysis_force,
                        report.overall(isomme).criterion_dummy.criterion_abdomen_force,
                ]
                for isomme in report.isomme_list
            })),
            CriterionTablePage(
                self, name="Values Table", title="Values",
                spec=values_table_spec_for(self).with_criteria(lambda report: {
                    isomme: [
                        report.overall(isomme).criterion_dummy.criterion_hpc36,
                        report.overall(isomme).criterion_dummy.criterion_chest_lateral_deflection,
                        report.overall(isomme).criterion_dummy.criterion_chest_lateral_vc,
                        report.overall(isomme).criterion_dummy.criterion_pubic_symphysis_force,
                        report.overall(isomme).criterion_dummy.criterion_abdomen_force,
                    ]
                    for isomme in report.isomme_list
                }),
            ),
            ChannelPlotPage(self, spec=side_head_acceleration_spec_for(self)),
            ChannelPlotPage(self, spec=side_barrier_chest_deflection_spec_for(self)),
            ChannelPlotPage(self, spec=side_barrier_chest_vc_spec_for(self)),
            ChannelPlotPage(self, spec=side_pubic_symphysis_force_spec_for(self)),
            ChannelPlotPage(self, spec=side_barrier_abdomen_force_spec_for(self)),
        )
        self._selected_pages = list(self._available_pages)
