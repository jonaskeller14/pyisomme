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
    side_shoulder_lateral_force_spec_for,
)
from pyisomme.report.manual import Manual, manual
from pyisomme.report.page2 import (
    ChannelPlotPage,
    CoverPage,
    CriterionTablePage,
    CriterionValuesChartPage,
    HICPage,
    criterion_values_chart_spec_for,
    hic_spec_for,
    values_table_spec_for,
)
from pyisomme.report.report import Report
from pyisomme.report.un.limits import Limit_Fail, Limit_Pass
from pyisomme.report.un.pages import (
    side_pole_abdomen_compression_spec_for,
    side_pole_chest_compression_spec_for,
    side_pole_spine_t12_acceleration_spec_for,
)
from pyisomme.report.un.protocols import PROTOCOL_R135_2016
from pyisomme.unit import Unit, g0

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
        rating = Criterion.rating_of(self.criterion_dummy)
        return CriterionResult(
            channel=None,
            value=rating,
            rating=rating,
            color=None,
        )

    class Criterion_Dummy(Criterion):
        name = "Dummy"

        def calculation(self) -> CriterionResult:
            rating = self.min_of_children()
            return CriterionResult(
                channel=None,
                value=rating,
                rating=rating,
                color=None,
            )

        class Criterion_HIC_36(Criterion):
            name = "HIC 36"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}HICR0036??00RX", "?{p}HICRCG36??00RX")
                return [
                    Limit_Pass(codes, func=lambda x: 1000, y_unit=1, upper=True),
                    Limit_Fail(codes, func=lambda x: 1000, y_unit=1, lower=True),
                ]

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}HICR0036??00RX"),
                    self.ctx.code("?{p}HICRCG36??00RX"),
                )
                value = channel.get_data()[0]
                evaluation = self.limits.evaluate(channel)
                rating = evaluation.get_limit_min_rating(interpolate=False)
                color = evaluation.get_limit_min_color()
                return CriterionResult(
                    channel=channel,
                    value=value,
                    rating=rating,
                    color=color,
                )

        class Criterion_Shoulder_Lateral_Force(Criterion):
            name = "Shoulder Lateral Force"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes(
                    "?{p}SHLD0000??FOY?", "?{p}SHLDLE00??FOY?", "?{p}SHLDRI00??FOY?"
                )
                return [
                    Limit_Fail(codes, func=lambda x: -3, y_unit="kN", upper=True),
                    Limit_Pass(codes, func=lambda x: -3, y_unit="kN", lower=True),
                    Limit_Pass(codes, func=lambda x: 3, y_unit="kN", upper=True),
                    Limit_Fail(codes, func=lambda x: 3.0, y_unit="kN", lower=True),
                ]

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}SHLD0000??FOYB")
                ).convert_unit("kN")
                value = channel.get_data()[np.argmax(np.abs(channel.get_data()))]
                evaluation = self.limits.evaluate(channel)
                rating = evaluation.get_limit_min_rating(interpolate=False)
                color = evaluation.get_limit_min_color()
                return CriterionResult(
                    channel=channel,
                    value=value,
                    rating=rating,
                    color=color,
                )

        class Criterion_Chest_Resultant_Compression(Criterion):
            name = "Chest Resultant Compression"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}TRRI??0[0123]??DSR?")
                return [
                    Limit_Fail(codes, func=lambda x: -55, y_unit="mm", upper=True),
                    Limit_Pass(codes, func=lambda x: -55, y_unit="mm", lower=True),
                ]

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}TRRI??00??DSRB")
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

        class Criterion_Abdomen_Resultant_Compression(Criterion):
            name = "Abdomen Resultant Compression"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}ABRI??0[012]??DSR?")
                return [
                    Limit_Fail(codes, func=lambda x: -65, y_unit="mm", upper=True),
                    Limit_Pass(codes, func=lambda x: -65, y_unit="mm", lower=True),
                ]

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}ABRI??00??DSRB")
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

        class Criterion_Spine_T12_a3ms(Criterion):
            name = "Spine T12 Acceleration a3ms"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("1{p}THSP123C??ACR?")
                return [
                    Limit_Pass(codes, func=lambda x: 75, y_unit=Unit(g0), upper=True),
                    Limit_Fail(codes, func=lambda x: 75, y_unit=Unit(g0), lower=True),
                ]

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("1{p}THSP123C??ACRX")
                ).convert_unit(Unit(g0))
                value = np.max(channel.get_data())
                evaluation = self.limits.evaluate(channel)
                rating = evaluation.get_limit_min_rating(interpolate=False)
                color = evaluation.get_limit_min_color()
                return CriterionResult(
                    channel=channel,
                    value=value,
                    rating=rating,
                    color=color,
                )

        class Criterion_Pubic_Symphysis_Force(Criterion):
            name = "Pubic Symphysis Force"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}PUBC0000??FOY?")
                return [
                    Limit_Fail(codes, func=lambda x: -3.36, y_unit="kN", upper=True),
                    Limit_Pass(codes, func=lambda x: -3.36, y_unit="kN", lower=True),
                    Limit_Pass(codes, func=lambda x: 3.36, y_unit="kN", upper=True),
                    Limit_Fail(codes, func=lambda x: 3.36, y_unit="kN", lower=True),
                ]

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}PUBC0000??FOYB")
                ).convert_unit("kN")
                value = channel.get_data()[np.argmax(np.abs(channel.get_data()))]
                evaluation = self.limits.evaluate(channel)
                rating = evaluation.get_limit_min_rating(interpolate=True)
                color = evaluation.get_limit_min_color()
                return CriterionResult(
                    channel=channel,
                    value=value,
                    rating=rating,
                    color=color,
                )

        criterion_hic_36 = sub(Criterion_HIC_36)
        criterion_shoulder_lateral_force = sub(Criterion_Shoulder_Lateral_Force)
        criterion_chest_resultant_compression = sub(
            Criterion_Chest_Resultant_Compression
        )
        criterion_abdomen_resultant_compression = sub(
            Criterion_Abdomen_Resultant_Compression
        )
        criterion_spine_t12_a3ms = sub(Criterion_Spine_T12_a3ms)
        criterion_pubic_symphysis_force = sub(Criterion_Pubic_Symphysis_Force)

    criterion_dummy = sub(Criterion_Dummy, at=from_input(P), role=Role.AGGREGATE)


class UN_Side_Pole_R135(Report[Overall]):
    _name = "UN-R135 | Pole Side Impact at 32 km/h"
    _protocol = PROTOCOL_R135_2016
    _protocols = (PROTOCOL_R135_2016,)
    Criterion_Overall = Overall

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._available_pages = (
            CoverPage(self),
            CriterionValuesChartPage(self, spec=criterion_values_chart_spec_for(
                self, name="Values Chart", title="Values"
            ).with_criteria(lambda report: {
                isomme: [
                        report.overall(isomme).criterion_dummy.criterion_hic_36,
                        report.overall(isomme).criterion_dummy.criterion_shoulder_lateral_force,
                        report.overall(isomme).criterion_dummy.criterion_chest_resultant_compression,
                        report.overall(isomme).criterion_dummy.criterion_abdomen_resultant_compression,
                        report.overall(isomme).criterion_dummy.criterion_spine_t12_a3ms,
                        report.overall(isomme).criterion_dummy.criterion_pubic_symphysis_force,
                ]
                for isomme in report.isomme_list
            })),
            CriterionTablePage(
                self, name="Values Table", title="Values",
                spec=values_table_spec_for(self).with_criteria(lambda report: {
                    isomme: [
                        report.overall(isomme).criterion_dummy.criterion_hic_36,
                        report.overall(isomme).criterion_dummy.criterion_shoulder_lateral_force,
                        report.overall(isomme).criterion_dummy.criterion_chest_resultant_compression,
                        report.overall(isomme).criterion_dummy.criterion_abdomen_resultant_compression,
                        report.overall(isomme).criterion_dummy.criterion_spine_t12_a3ms,
                        report.overall(isomme).criterion_dummy.criterion_pubic_symphysis_force,
                    ]
                    for isomme in report.isomme_list
                }),
            ),
            ChannelPlotPage(self, spec=side_head_acceleration_spec_for(self)),
            HICPage(
                self,
                spec=hic_spec_for(
                    self,
                    name="HIC36",
                    title="HIC36",
                    timespan=36,
                ).with_position(
                    lambda report, isomme: report.overall(isomme).p
                ).with_criterion(
                    lambda report, isomme: report.overall(
                        isomme
                    ).criterion_dummy.criterion_hic_36
                ),
            ),
            ChannelPlotPage(self, spec=side_shoulder_lateral_force_spec_for(self)),
            ChannelPlotPage(self, spec=side_pole_chest_compression_spec_for(self)),
            ChannelPlotPage(self, spec=side_pole_abdomen_compression_spec_for(self)),
            ChannelPlotPage(self, spec=side_pole_spine_t12_acceleration_spec_for(self)),
            ChannelPlotPage(self, spec=side_pubic_symphysis_force_spec_for(self)),
        )
        self._selected_pages = list(self._available_pages)
