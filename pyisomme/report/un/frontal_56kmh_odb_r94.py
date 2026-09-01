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
    driver_femur_axial_force_spec_for,
    driver_head_acceleration_spec_for,
    driver_neck_load_spec_for,
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
    rating_table_spec_for,
    values_table_spec_for,
)
from pyisomme.report.page2.plot_nxn import channel_plot_spec_for
from pyisomme.report.report import Report
from pyisomme.report.un.frontal_50kmh_r137 import (
    Criterion_Chest_VC as Criterion_Chest_VC_R137,
    Criterion_Head_a3ms as Criterion_Head_a3ms_R137,
    Criterion_HPC36 as Criterion_HPC36_R137,
    Criterion_Neck_My_extension as Criterion_Neck_My_extension_R137,
    Overall as Overall_Frontal_50kmh_R137,
)
from pyisomme.report.un.limits import Limit_Fail, Limit_Pass
from pyisomme.report.un.protocols import PROTOCOL_R94_2022

logger = logging.getLogger(__name__)

P_DRIVER = manual(
    "1",
    source="test report",
    doc=(
        "Channel-code position of the driver. Defaults to the "
        "'Driver position object 1' test-info field when the test carries it."
    ),
)
P_PASSENGER = manual(
    "3",
    source="test report",
    doc=(
        "Channel-code position of the front passenger. Derived from p_driver "
        "('1' for a right-hand-drive test) unless set explicitly."
    ),
)


class Overall(Criterion):
    name = "Overall"
    role = Role.AGGREGATE
    p_driver: Manual[str, P_DRIVER]
    p_passenger: Manual[str, P_PASSENGER]

    def __init__(self, report: Report[Any], isomme: Isomme) -> None:
        super().__init__(report, isomme)
        # Also at construction: the pages read the positions when the report is built.
        self.prepare()

    def prepare(self) -> None:
        """Settle both positions before the occupants' ``from_input()`` context reads them."""
        p_driver = self.isomme.get_test_info("Driver position object 1")
        if p_driver is not None:
            self.set_derived_input("p_driver", str(p_driver).strip())
        self.set_derived_input("p_passenger", "1" if self.p_driver != "1" else "3")

    def calculation(self) -> CriterionResult:
        rating = self.min_of_children()
        return CriterionResult(
            channel=None,
            value=rating,
            rating=rating,
            color=None,
        )

    class Criterion_Driver(Criterion):
        name = "Driver"
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

        class Criterion_Head_a3ms(Criterion_Head_a3ms_R137):
            pass

        class Criterion_Neck_Fz_tension(Criterion):
            name = "Neck Fz tension"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}NECKUP00??FOZ?")
                return [
                    Limit_Pass(
                        codes,
                        func=lambda x: np.interp(x, [0, 35, 60], [3.3, 2.9, 1.1]),
                        x_unit="ms",
                        y_unit="kN",
                        upper=True,
                    ),
                    Limit_Fail(
                        codes,
                        func=lambda x: np.interp(x, [0, 35, 60], [3.3, 2.9, 1.1]),
                        x_unit="ms",
                        y_unit="kN",
                        lower=True,
                    ),
                ]

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}NECKUP00??FOZA")
                ).convert_unit("kN")
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

        class Criterion_Neck_Fx_shear(Criterion):
            name = "Neck Fx shear"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}NECKUP00??FOX?")
                return [
                    Limit_Fail(
                        codes,
                        func=lambda x: (
                            -np.interp(x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1])
                        ),
                        x_unit="ms",
                        y_unit="kN",
                        upper=True,
                    ),
                    Limit_Pass(
                        codes,
                        func=lambda x: (
                            -np.interp(x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1])
                        ),
                        x_unit="ms",
                        y_unit="kN",
                        lower=True,
                    ),
                    Limit_Pass(
                        codes,
                        func=lambda x: np.interp(
                            x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1]
                        ),
                        x_unit="ms",
                        y_unit="kN",
                        upper=True,
                    ),
                    Limit_Fail(
                        codes,
                        func=lambda x: np.interp(
                            x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1]
                        ),
                        x_unit="ms",
                        y_unit="kN",
                        lower=True,
                    ),
                ]

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}NECKUP00??FOXA")
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

        class Criterion_Neck_My_extension(Criterion_Neck_My_extension_R137):
            pass

        class Criterion_Chest_Deflection(
            Overall_Frontal_50kmh_R137.Criterion_Driver.Criterion_Chest_Deflection
        ):
            pass

        class Criterion_Chest_VC(Criterion_Chest_VC_R137):
            pass

        class Criterion_Femur_Compression(Criterion):
            name = "Femur Compression"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}FEMR??00??FOZ?")
                return [
                    Limit_Fail(
                        codes,
                        func=lambda x: np.interp(x, [0, 10], [-9.07, -7.58]),
                        y_unit="kN",
                        x_unit="ms",
                        upper=True,
                    ),
                    Limit_Pass(
                        codes,
                        func=lambda x: np.interp(x, [0, 10], [-9.07, -7.58]),
                        y_unit="kN",
                        x_unit="ms",
                        lower=True,
                    ),
                ]

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}FEMR0000??FOZB")
                ).convert_unit("kN")
                evaluation = self.limits.evaluate(channel)
                value = evaluation.get_limit_min_y()
                rating = evaluation.get_limit_min_rating(interpolate=False)
                color = evaluation.get_limit_min_color()
                return CriterionResult(
                    channel=channel,
                    value=value,
                    rating=rating,
                    color=color,
                )

        class Criterion_Tibia_Compression(Criterion):
            name = "Tibia Compression"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}TIBI??????FOZ?")
                return [
                    Limit_Fail(codes, func=lambda x: -8, y_unit="kN", upper=True),
                    Limit_Pass(codes, func=lambda x: -8, y_unit="kN", lower=True),
                ]

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}TIBI0000??FOZB")
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

        class Criterion_Tibia_Index(Criterion):
            name = "Tibia Index"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}TIIN??00??000?")
                return [
                    Limit_Pass(codes, func=lambda x: 1.3, y_unit="1", upper=True),
                    Limit_Fail(codes, func=lambda x: 1.3, y_unit="1", lower=True),
                ]

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(self.ctx.code("?{p}TIIN0000??000B"))
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

        class Criterion_Knee_Slider_Compression(Criterion):
            name = "Knee Slider Compression"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}KNSL??00??DSX?")
                return [
                    Limit_Fail(codes, func=lambda x: -15, y_unit="mm", upper=True),
                    Limit_Pass(codes, func=lambda x: -15, y_unit="mm", lower=True),
                ]

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}KNSL0000??DSXC")
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

        criterion_hpc36 = sub(Criterion_HPC36)
        criterion_head_a3ms = sub(Criterion_Head_a3ms)
        criterion_neck_fz_tension = sub(Criterion_Neck_Fz_tension)
        criterion_neck_fx_shear = sub(Criterion_Neck_Fx_shear)
        criterion_neck_my_extension = sub(Criterion_Neck_My_extension)
        criterion_chest_deflection = sub(Criterion_Chest_Deflection)
        criterion_chest_vc = sub(Criterion_Chest_VC)
        criterion_femur_compression = sub(Criterion_Femur_Compression)
        criterion_tibia_compression = sub(Criterion_Tibia_Compression)
        criterion_tibia_index = sub(Criterion_Tibia_Index)
        criterion_knee_slider_compression = sub(Criterion_Knee_Slider_Compression)

    class Criterion_Passenger(Criterion):
        name = "Passenger"
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

        class Criterion_Head_a3ms(Criterion_Head_a3ms_R137):
            pass

        class Criterion_Neck_Fz_tension(Criterion):
            name = "Neck Fz tension"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}NECKUP00??FOZ?")
                return [
                    Limit_Pass(
                        codes,
                        func=lambda x: np.interp(x, [0, 35, 60], [3.3, 2.9, 1.1]),
                        x_unit="ms",
                        y_unit="kN",
                        upper=True,
                    ),
                    Limit_Fail(
                        codes,
                        func=lambda x: np.interp(x, [0, 35, 60], [3.3, 2.9, 1.1]),
                        x_unit="ms",
                        y_unit="kN",
                        lower=True,
                    ),
                ]

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}NECKUP00??FOZA")
                ).convert_unit("kN")
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

        class Criterion_Neck_Fx_shear(Criterion):
            name = "Neck Fx shear"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}NECKUP00??FOX?")
                return [
                    Limit_Fail(
                        codes,
                        func=lambda x: (
                            -np.interp(x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1])
                        ),
                        x_unit="ms",
                        y_unit="kN",
                        upper=True,
                    ),
                    Limit_Pass(
                        codes,
                        func=lambda x: (
                            -np.interp(x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1])
                        ),
                        x_unit="ms",
                        y_unit="kN",
                        lower=True,
                    ),
                    Limit_Pass(
                        codes,
                        func=lambda x: np.interp(
                            x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1]
                        ),
                        x_unit="ms",
                        y_unit="kN",
                        upper=True,
                    ),
                    Limit_Fail(
                        codes,
                        func=lambda x: np.interp(
                            x, [0, 25, 35, 45], [3.1, 1.5, 1.5, 1.1]
                        ),
                        x_unit="ms",
                        y_unit="kN",
                        lower=True,
                    ),
                ]

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}NECKUP00??FOXA")
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

        class Criterion_Neck_My_extension(Criterion_Neck_My_extension_R137):
            pass

        class Criterion_Chest_Deflection(
            Overall_Frontal_50kmh_R137.Criterion_Driver.Criterion_Chest_Deflection
        ):
            pass

        class Criterion_Chest_VC(Criterion_Chest_VC_R137):
            pass

        class Criterion_Femur_Compression(Criterion):
            name = "Femur Compression"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}FEMR??00??FOZ?")
                return [
                    Limit_Fail(
                        codes,
                        func=lambda x: np.interp(x, [0, 10], [-9.07, -7.58]),
                        y_unit="kN",
                        x_unit="ms",
                        upper=True,
                    ),
                    Limit_Pass(
                        codes,
                        func=lambda x: np.interp(x, [0, 10], [-9.07, -7.58]),
                        y_unit="kN",
                        x_unit="ms",
                        lower=True,
                    ),
                ]

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}FEMR0000??FOZB")
                ).convert_unit("kN")
                evaluation = self.limits.evaluate(channel)
                value = evaluation.get_limit_min_y()
                rating = evaluation.get_limit_min_rating(interpolate=False)
                color = evaluation.get_limit_min_color()
                return CriterionResult(
                    channel=channel,
                    value=value,
                    rating=rating,
                    color=color,
                )

        class Criterion_Tibia_Compression(Criterion):
            name = "Tibia Compression"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}TIBI??????FOZ?")
                return [
                    Limit_Fail(codes, func=lambda x: -8, y_unit="kN", upper=True),
                    Limit_Pass(codes, func=lambda x: -8, y_unit="kN", lower=True),
                ]

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}TIBI0000??FOZB")
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

        class Criterion_Tibia_Index(Criterion):
            name = "Tibia Index"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}TIIN??00??000?")
                return [
                    Limit_Pass(codes, func=lambda x: 1.3, y_unit="1", upper=True),
                    Limit_Fail(codes, func=lambda x: 1.3, y_unit="1", lower=True),
                ]

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(self.ctx.code("?{p}TIIN0000??000B"))
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

        class Criterion_Knee_Slider_Compression(Criterion):
            name = "Knee Slider Compression"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}KNSL??00??DSX?")
                return [
                    Limit_Fail(codes, func=lambda x: -15, y_unit="mm", upper=True),
                    Limit_Pass(codes, func=lambda x: -15, y_unit="mm", lower=True),
                ]

            def calculation(self) -> CriterionResult:
                channel = self.require_channel(
                    self.ctx.code("?{p}KNSL0000??DSXC")
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

        criterion_hpc36 = sub(Criterion_HPC36)
        criterion_head_a3ms = sub(Criterion_Head_a3ms)
        criterion_neck_fz_tension = sub(Criterion_Neck_Fz_tension)
        criterion_neck_fx_shear = sub(Criterion_Neck_Fx_shear)
        criterion_neck_my_extension = sub(Criterion_Neck_My_extension)
        criterion_chest_deflection = sub(Criterion_Chest_Deflection)
        criterion_chest_vc = sub(Criterion_Chest_VC)
        criterion_femur_compression = sub(Criterion_Femur_Compression)
        criterion_tibia_compression = sub(Criterion_Tibia_Compression)
        criterion_tibia_index = sub(Criterion_Tibia_Index)
        criterion_knee_slider_compression = sub(Criterion_Knee_Slider_Compression)

    criterion_driver = sub(
        Criterion_Driver, at=from_input(P_DRIVER), role=Role.AGGREGATE
    )
    criterion_passenger = sub(
        Criterion_Passenger, role=Role.AGGREGATE, at=from_input(P_PASSENGER)
    )


class UN_Frontal_56kmh_ODB_R94(Report[Overall]):
    _name = "UN-R94 | Frontal-Impact against ODB with 40 % Overlap at 56 km/h"
    _protocol = PROTOCOL_R94_2022
    _protocols = (PROTOCOL_R94_2022,)
    Criterion_Overall = Overall

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._available_pages = (
            CoverPage(self),
            CriterionTablePage(
                self, name="Rating", title="Rating",
                spec=rating_table_spec_for(self).with_criteria(lambda report: {
                    isomme: [
                        report.overall(isomme).criterion_driver,
                        report.overall(isomme).criterion_passenger,
                        report.overall(isomme),
                    ]
                    for isomme in report.isomme_list
                }),
            ),
            CriterionValuesChartPage(self, spec=criterion_values_chart_spec_for(
                self, name="Driver Result Values Chart", title="Driver Result"
            ).with_criteria(lambda report: {
                isomme: [
                        report.overall(isomme).criterion_driver.criterion_hpc36,
                        report.overall(isomme).criterion_driver.criterion_head_a3ms,
                        report.overall(isomme).criterion_driver.criterion_neck_fz_tension,
                        report.overall(isomme).criterion_driver.criterion_neck_fx_shear,
                        report.overall(isomme).criterion_driver.criterion_neck_my_extension,
                        report.overall(isomme).criterion_driver.criterion_chest_deflection,
                        report.overall(isomme).criterion_driver.criterion_chest_vc,
                        report.overall(isomme).criterion_driver.criterion_femur_compression,
                        report.overall(isomme).criterion_driver.criterion_tibia_compression,
                        report.overall(isomme).criterion_driver.criterion_tibia_index,
                        report.overall(isomme).criterion_driver.criterion_knee_slider_compression,
                ]
                for isomme in report.isomme_list
            })),
            CriterionTablePage(
                self, name="Driver Values Table", title="Driver Values",
                spec=values_table_spec_for(self).with_criteria(lambda report: {
                    isomme: [
                        report.overall(isomme).criterion_driver.criterion_hpc36,
                        report.overall(isomme).criterion_driver.criterion_head_a3ms,
                        report.overall(isomme).criterion_driver.criterion_neck_fz_tension,
                        report.overall(isomme).criterion_driver.criterion_neck_fx_shear,
                        report.overall(isomme).criterion_driver.criterion_neck_my_extension,
                        report.overall(isomme).criterion_driver.criterion_chest_deflection,
                        report.overall(isomme).criterion_driver.criterion_chest_vc,
                        report.overall(isomme).criterion_driver.criterion_femur_compression,
                        report.overall(isomme).criterion_driver.criterion_tibia_compression,
                        report.overall(isomme).criterion_driver.criterion_tibia_index,
                        report.overall(isomme).criterion_driver.criterion_knee_slider_compression,
                    ]
                    for isomme in report.isomme_list
                }),
            ),
            ChannelPlotPage(self, spec=driver_head_acceleration_spec_for(self)),
            HICPage(
                self,
                spec=hic_spec_for(
                    self,
                    name="Driver HPC36",
                    title="Driver HPC36",
                    timespan=36,
                ).with_position(
                    lambda report, isomme: report.overall(isomme).p_driver
                ).with_criterion(
                    lambda report, isomme: report.overall(
                        isomme
                    ).criterion_driver.criterion_hpc36
                ),
            ),
            ChannelPlotPage(self, spec=driver_neck_load_spec_for(self)),
            ChannelPlotPage(
                self,
                spec=channel_plot_spec_for(
                    self, name="Driver Chest Deflection", title="Driver Chest Deflection",
                    nrows=1, ncols=2,
                ).with_channels(lambda report: {
                    isomme: [
                        [f"?{report.overall(isomme).p_driver}CHST000???DSXC"],
                        [f"?{report.overall(isomme).p_driver}VCCR000???VEXC"],
                    ]
                    for isomme in report.isomme_list
                }),
            ),
            ChannelPlotPage(self, spec=driver_femur_axial_force_spec_for(self)),
            ChannelPlotPage(
                self,
                spec=channel_plot_spec_for(
                    self,
                    name="Driver Knee Slider Compression",
                    title="Driver Knee Slider Compression",
                    nrows=1,
                    ncols=2,
                    sharey=True,
                ).with_channels(lambda report: {
                    isomme: [
                        [f"?{report.overall(isomme).p_driver}KNSLLE00??DSXC"],
                        [f"?{report.overall(isomme).p_driver}KNSLRI00??DSXC"],
                    ]
                    for isomme in report.isomme_list
                }),
            ),
            ChannelPlotPage(
                self,
                spec=channel_plot_spec_for(
                    self,
                    name="Driver Tibia Compression",
                    title="Driver Tibia Compression",
                    nrows=2,
                    ncols=2,
                    sharey=True,
                ).with_channels(lambda report: {
                    isomme: [
                        [f"?{report.overall(isomme).p_driver}TIBILEUP??FOZB"],
                        [f"?{report.overall(isomme).p_driver}TIBIRIUP??FOZB"],
                        [f"?{report.overall(isomme).p_driver}TIBILELO??FOZB"],
                        [f"?{report.overall(isomme).p_driver}TIBIRILO??FOZB"],
                    ]
                    for isomme in report.isomme_list
                }),
            ),
            ChannelPlotPage(
                self,
                spec=channel_plot_spec_for(
                    self,
                    name="Driver Tibia Index",
                    title="Driver Tibia Index",
                    nrows=2,
                    ncols=2,
                    sharey=True,
                ).with_channels(lambda report: {
                    isomme: [
                        [f"?{report.overall(isomme).p_driver}TIINLU00??000B"],
                        [f"?{report.overall(isomme).p_driver}TIINRU00??000B"],
                        [f"?{report.overall(isomme).p_driver}TIINLL00??000B"],
                        [f"?{report.overall(isomme).p_driver}TIINRL00??000B"],
                    ]
                    for isomme in report.isomme_list
                }),
            ),
            CriterionValuesChartPage(self, spec=criterion_values_chart_spec_for(
                self, name="Passenger Result Values Chart", title="Passenger Result"
            ).with_criteria(lambda report: {
                isomme: [
                        report.overall(isomme).criterion_passenger.criterion_hpc36,
                        report.overall(isomme).criterion_passenger.criterion_head_a3ms,
                        report.overall(isomme).criterion_passenger.criterion_neck_fz_tension,
                        report.overall(isomme).criterion_passenger.criterion_neck_fx_shear,
                        report.overall(isomme).criterion_passenger.criterion_neck_my_extension,
                        report.overall(isomme).criterion_passenger.criterion_chest_deflection,
                        report.overall(isomme).criterion_passenger.criterion_chest_vc,
                        report.overall(isomme).criterion_passenger.criterion_femur_compression,
                        report.overall(isomme).criterion_passenger.criterion_tibia_compression,
                        report.overall(isomme).criterion_passenger.criterion_tibia_index,
                        report.overall(isomme).criterion_passenger.criterion_knee_slider_compression,
                ]
                for isomme in report.isomme_list
            })),
            CriterionTablePage(
                self, name="Passenger Values Table", title="Passenger Values",
                spec=values_table_spec_for(self).with_criteria(lambda report: {
                    isomme: [
                        report.overall(isomme).criterion_passenger.criterion_hpc36,
                        report.overall(isomme).criterion_passenger.criterion_head_a3ms,
                        report.overall(isomme).criterion_passenger.criterion_neck_fz_tension,
                        report.overall(isomme).criterion_passenger.criterion_neck_fx_shear,
                        report.overall(isomme).criterion_passenger.criterion_neck_my_extension,
                        report.overall(isomme).criterion_passenger.criterion_chest_deflection,
                        report.overall(isomme).criterion_passenger.criterion_chest_vc,
                        report.overall(isomme).criterion_passenger.criterion_femur_compression,
                        report.overall(isomme).criterion_passenger.criterion_tibia_compression,
                        report.overall(isomme).criterion_passenger.criterion_tibia_index,
                        report.overall(isomme).criterion_passenger.criterion_knee_slider_compression,
                    ]
                    for isomme in report.isomme_list
                }),
            ),
            ChannelPlotPage(
                self,
                spec=channel_plot_spec_for(
                    self, name="Passenger Head Acceleration", title="Passenger Head Acceleration",
                    nrows=2, ncols=2, sharey=True,
                ).with_channels(lambda report: {
                    isomme: [
                        [f"?{report.overall(isomme).p_passenger}HEAD??????ACXA"],
                        [f"?{report.overall(isomme).p_passenger}HEAD??????ACYA"],
                        [f"?{report.overall(isomme).p_passenger}HEAD??????ACZA"],
                        [f"?{report.overall(isomme).p_passenger}HEAD??????ACRA"],
                    ]
                    for isomme in report.isomme_list
                }),
            ),
            HICPage(
                self,
                spec=hic_spec_for(
                    self,
                    name="Passenger HPC36",
                    title="Passenger HPC36",
                    timespan=36,
                ).with_position(
                    lambda report, isomme: report.overall(isomme).p_passenger
                ).with_criterion(
                    lambda report, isomme: report.overall(
                        isomme
                    ).criterion_passenger.criterion_hpc36
                ),
            ),
            ChannelPlotPage(
                self,
                spec=channel_plot_spec_for(
                    self, name="Passenger Neck Load", title="Passenger Neck Load",
                    nrows=2, ncols=2,
                ).with_channels(lambda report: {
                    isomme: [
                        [f"?{report.overall(isomme).p_passenger}NECKUP00??MOYB"],
                        [f"?{report.overall(isomme).p_passenger}NECKUP00??FOZA"],
                        [f"?{report.overall(isomme).p_passenger}NECKUP00??FOXA"],
                    ]
                    for isomme in report.isomme_list
                }),
            ),
            ChannelPlotPage(
                self,
                spec=channel_plot_spec_for(
                    self, name="Passenger Chest Deflection", title="Passenger Chest Deflection",
                    nrows=1, ncols=2,
                ).with_channels(lambda report: {
                    isomme: [
                        [f"?{report.overall(isomme).p_passenger}CHST000???DSXC"],
                        [f"?{report.overall(isomme).p_passenger}VCCR000???VEXC"],
                    ]
                    for isomme in report.isomme_list
                }),
            ),
            ChannelPlotPage(
                self,
                spec=channel_plot_spec_for(
                    self, name="Passenger Femur Axial Force", title="Passenger Femur Axial Force",
                    nrows=1, ncols=2, sharey=True,
                ).with_channels(lambda report: {
                    isomme: [
                        [f"?{report.overall(isomme).p_passenger}FEMRLE00??FOZB"],
                        [f"?{report.overall(isomme).p_passenger}FEMRRI00??FOZB"],
                    ]
                    for isomme in report.isomme_list
                }),
            ),
            ChannelPlotPage(
                self,
                spec=channel_plot_spec_for(
                    self,
                    name="Passenger Knee Slider Compression",
                    title="Passenger Knee Slider Compression",
                    nrows=1,
                    ncols=2,
                    sharey=True,
                ).with_channels(lambda report: {
                    isomme: [
                        [f"?{report.overall(isomme).p_passenger}KNSLLE00??DSXC"],
                        [f"?{report.overall(isomme).p_passenger}KNSLRI00??DSXC"],
                    ]
                    for isomme in report.isomme_list
                }),
            ),
            ChannelPlotPage(
                self,
                spec=channel_plot_spec_for(
                    self,
                    name="Passenger Tibia Compression",
                    title="Passenger Tibia Compression",
                    nrows=2,
                    ncols=2,
                    sharey=True,
                ).with_channels(lambda report: {
                    isomme: [
                        [f"?{report.overall(isomme).p_passenger}TIBILEUP??FOZB"],
                        [f"?{report.overall(isomme).p_passenger}TIBIRIUP??FOZB"],
                        [f"?{report.overall(isomme).p_passenger}TIBILELO??FOZB"],
                        [f"?{report.overall(isomme).p_passenger}TIBIRILO??FOZB"],
                    ]
                    for isomme in report.isomme_list
                }),
            ),
            ChannelPlotPage(
                self,
                spec=channel_plot_spec_for(
                    self,
                    name="Passenger Tibia Index",
                    title="Passenger Tibia Index",
                    nrows=2,
                    ncols=2,
                    sharey=True,
                ).with_channels(lambda report: {
                    isomme: [
                        [f"?{report.overall(isomme).p_passenger}TIINLU00??000B"],
                        [f"?{report.overall(isomme).p_passenger}TIINRU00??000B"],
                        [f"?{report.overall(isomme).p_passenger}TIINLL00??000B"],
                        [f"?{report.overall(isomme).p_passenger}TIINRL00??000B"],
                    ]
                    for isomme in report.isomme_list
                }),
            ),
        )
        self._selected_pages = list(self._available_pages)
