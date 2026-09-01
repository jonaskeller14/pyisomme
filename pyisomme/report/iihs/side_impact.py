from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from pyisomme.calculate.vc import calculate_vc
from pyisomme.channel import Channel, time_intersect
from pyisomme.isomme import Isomme
from pyisomme.limit import Limit
from pyisomme.report.criterion import Criterion, Role, sub
from pyisomme.report.criterion_result import CriterionResult
from pyisomme.report.ctx import from_input
from pyisomme.report.iihs.limits import (
    Limit_A,
    Limit_G,
    Limit_M,
    Limit_P,
)
from pyisomme.report.iihs.pages import driver_head_acceleration_spec_for
from pyisomme.report.iihs.protocols import PROTOCOL_SIDE_IMPACT_IV
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

P_DRIVER = manual(
    "1",
    source="test report",
    doc=(
        "Channel-code position of the driver SID-IIs dummy. Defaults to the "
        "'Driver position object 1' test-info field when available."
    ),
)
P_REAR_PASSENGER = manual(
    "6",
    source="test report",
    doc="Channel-code position of the left-rear passenger SID-IIs dummy; derived from the driver side.",
)

RIB_DEFLECTION_CODES = (
    "?{p}TRRILE01??DSYC",
    "?{p}TRRILE02??DSYC",
    "?{p}TRRILE03??DSYC",
    "?{p}ABRILE01??DSYC",
    "?{p}ABRILE02??DSYC",
)
RIB_RATE_CODES = tuple(code.replace("DSYC", "VEY?") for code in RIB_DEFLECTION_CODES)
RIB_VC_CODES = (
    "?{p}VCCRLE01??VEY?",
    "?{p}VCCRLE02??VEY?",
    "?{p}VCCRLE03??VEY?",
    "?{p}VCARLE01??VEY?",
    "?{p}VCARLE02??VEY?",
)


class Criterion_Head_Neck(Criterion):
    name = "Head and neck"
    role = Role.AGGREGATE
    aggregation = "min"

    class Criterion_HIC_15(Criterion):
        name = "HIC15"
        validate_ignore = {
            "limit_flags": "discrete demerits use successive upper bounds with interpolation disabled",
        }

        def define_limits(self) -> list[Limit]:
            codes = self.ctx.codes("?{p}HICR0015??00RX")
            return [
                Limit_G(codes, lambda x: 623, y_unit=1, upper=True, rating=0),
                Limit_A(codes, lambda x: 779, y_unit=1, upper=True, rating=-2),
                Limit_M(codes, lambda x: 935, y_unit=1, upper=True, rating=-10),
                Limit_P(codes, lambda x: 935, y_unit=1, lower=True, rating=-35),
            ]

        def calculation(self) -> CriterionResult:
            channel = self.require_channel(self.ctx.code("?{p}HICR0015??00RX"))
            value = float(channel.get_data()[0])
            evaluation = self.limits.evaluate(channel)
            rating = evaluation.get_limit_min_rating(interpolate=False)
            color = evaluation.get_limit_min_color()
            return CriterionResult(
                channel=channel,
                value=value,
                rating=rating,
                color=color,
            )

    class Criterion_Neck_Tension(Criterion):
        name = "Neck axial tension"
        validate_ignore = {
            "limit_flags": "discrete demerits use successive upper bounds with interpolation disabled",
        }

        def define_limits(self) -> list[Limit]:
            codes = self.ctx.codes("?{p}NECKUP00??FOZ?")
            return [
                Limit_G(codes, lambda x: 2.1, y_unit="kN", upper=True, rating=0),
                Limit_A(codes, lambda x: 2.5, y_unit="kN", upper=True, rating=-2),
                Limit_M(codes, lambda x: 2.9, y_unit="kN", upper=True, rating=-10),
                Limit_P(codes, lambda x: 2.9, y_unit="kN", lower=True, rating=-35),
            ]

        def calculation(self) -> CriterionResult:
            channel = self.require_channel(
                self.ctx.code("?{p}NECKUP00??FOZB")
            ).convert_unit("kN")
            value = float(np.max(channel.get_data()))
            evaluation = self.limits.evaluate(channel)
            rating = evaluation.get_limit_min_rating(interpolate=False)
            color = evaluation.get_limit_min_color()
            return CriterionResult(
                channel=channel,
                value=value,
                rating=rating,
                color=color,
            )

    class Criterion_Neck_Compression(Criterion):
        name = "Neck axial compression"

        def define_limits(self) -> list[Limit]:
            codes = self.ctx.codes("?{p}NECKUP00??FOZ?")
            return [
                Limit_G(codes, lambda x: -2.5, y_unit="kN", lower=True, rating=0),
                Limit_A(codes, lambda x: -2.5, y_unit="kN", upper=True, rating=-2),
                Limit_M(codes, lambda x: -3.0, y_unit="kN", upper=True, rating=-10),
                Limit_P(codes, lambda x: -3.5, y_unit="kN", upper=True, rating=-35),
            ]

        def calculation(self) -> CriterionResult:
            channel = self.require_channel(
                self.ctx.code("?{p}NECKUP00??FOZB")
            ).convert_unit("kN")
            value = float(-np.min(channel.get_data()))
            evaluation = self.limits.evaluate(channel)
            rating = evaluation.get_limit_min_rating(interpolate=False)
            color = evaluation.get_limit_min_color()
            return CriterionResult(
                channel=channel,
                value=value,
                rating=rating,
                color=color,
            )

    def calculation(self) -> CriterionResult:
        rating = self.min_of_children()
        color = {
            0.0: Limit_G.color,
            -2.0: Limit_A.color,
            -10.0: Limit_M.color,
            -35.0: Limit_P.color,
        }.get(rating)
        return CriterionResult(
            channel=None,
            value=rating,
            rating=rating,
            color=color,
        )

    criterion_hic_15 = sub(Criterion_HIC_15)
    criterion_neck_tension = sub(Criterion_Neck_Tension)
    criterion_neck_compression = sub(Criterion_Neck_Compression)


class Criterion_Torso(Criterion):
    name = "Torso"
    role = Role.AGGREGATE
    aggregation = "min"
    shoulder_bottoming: Manual[
        bool,
        manual(
            False,
            source="high-speed video and postcrash inspection",
            doc="True when shoulder excursion exceeds 60 mm or the shoulder bottoms out.",
        ),
    ]

    class Criterion_Rib_Deflection(Criterion):
        name = "Average peak rib deflection"
        validate_ignore = {
            "limit_flags": "discrete demerits use successive upper bounds with interpolation disabled",
        }

        def define_limits(self) -> list[Limit]:
            codes = self.ctx.codes(*RIB_DEFLECTION_CODES)
            return [
                Limit_G(codes, lambda x: 28, y_unit="mm", upper=True, rating=0),
                Limit_A(codes, lambda x: 38, y_unit="mm", upper=True, rating=-2),
                Limit_M(codes, lambda x: 48, y_unit="mm", upper=True, rating=-10),
                Limit_P(codes, lambda x: 48, y_unit="mm", lower=True, rating=-35),
            ]

        def calculation(self) -> CriterionResult:
            channels = [
                self.require_channel(code)
                for code in self.ctx.codes(*RIB_DEFLECTION_CODES)
            ]
            peaks = [
                float(np.max(np.abs(channel.get_data(unit="mm"))))
                for channel in channels
            ]
            value = float(np.mean(peaks))
            channel = Channel(channels[0].code, pd.DataFrame([value]), "mm")
            evaluation = self.limits.evaluate(channel)
            rating = evaluation.get_limit_min_rating(interpolate=False)
            color = evaluation.get_limit_min_color()
            peak = float(np.max(peaks))
            if peak > 55:
                rating, color = -35.0, Limit_P.color
            elif peak > 50:
                rating = min(rating, -10.0)
                if rating == -10.0:
                    color = Limit_M.color
            return CriterionResult(
                channel=channel,
                value=value,
                rating=rating,
                color=color,
            )

    class Criterion_Rib_Deflection_Rate(Criterion):
        name = "Rib deflection rate"
        validate_ignore = {
            "limit_flags": "discrete demerits use successive upper bounds with interpolation disabled",
        }

        def define_limits(self) -> list[Limit]:
            codes = self.ctx.codes(*RIB_RATE_CODES)
            return [
                Limit_G(codes, lambda x: 8.2, y_unit="m/s", upper=True, rating=0),
                Limit_A(codes, lambda x: 9.8, y_unit="m/s", upper=True, rating=-2),
                Limit_M(codes, lambda x: 11.5, y_unit="m/s", upper=True, rating=-10),
                Limit_P(codes, lambda x: 11.5, y_unit="m/s", lower=True, rating=-35),
            ]

        def calculation(self) -> CriterionResult:
            channels = [
                self.require_channel(code)
                for code in self.ctx.codes(*RIB_DEFLECTION_CODES)
            ]
            rate_channels = [
                Channel(
                    channel.code,
                    pd.DataFrame(np.abs(channel.data), index=channel.data.index),
                    "m/s",
                )
                for channel in (raw.differentiate() for raw in channels)
            ]
            ratings = [
                self.limits.get_limit_min_rating(channel, interpolate=False)
                for channel in rate_channels
            ]
            channel = rate_channels[int(np.argmin(ratings))]
            value = float(
                max(
                    np.max(np.abs(channel.get_data(unit="m/s")))
                    for channel in rate_channels
                )
            )
            rating = min(ratings)
            color = self.limits.get_limit_min_color(channel)
            return CriterionResult(
                channel=channel,
                value=value,
                rating=rating,
                color=color,
            )

    class Criterion_Viscous_Criterion(Criterion):
        name = "Viscous criterion"
        validate_ignore = {
            "limit_flags": "discrete demerits use successive upper bounds with interpolation disabled",
        }

        def define_limits(self) -> list[Limit]:
            codes = self.ctx.codes(*RIB_VC_CODES)
            return [
                Limit_G(codes, lambda x: 1.0, y_unit="m/s", upper=True, rating=0),
                Limit_A(codes, lambda x: 1.2, y_unit="m/s", upper=True, rating=-2),
                Limit_M(codes, lambda x: 1.4, y_unit="m/s", upper=True, rating=-10),
                Limit_P(codes, lambda x: 1.4, y_unit="m/s", lower=True, rating=-35),
            ]

        def calculation(self) -> CriterionResult:
            channels = [
                self.require_channel(code)
                for code in self.ctx.codes(*RIB_DEFLECTION_CODES)
            ]
            vc_channels = []
            for channel in channels:
                raw_vc = calculate_vc(channel, scaling_factor=1.0, defo_constant=0.138)[
                    1
                ]
                vc_channels.append(
                    Channel(
                        raw_vc.code,
                        pd.DataFrame(np.abs(raw_vc.data), index=raw_vc.data.index),
                        "m/s",
                    )
                )
            if not vc_channels:
                raise ValueError("No viscous criterion channels available")
            ratings = [
                self.limits.get_limit_min_rating(channel, interpolate=False)
                for channel in vc_channels
            ]
            channel = vc_channels[int(np.argmin(ratings))]
            assert channel is not None
            channel = channel.convert_unit("m/s")
            value = float(np.max(np.abs(channel.get_data())))
            rating = min(ratings)
            color = self.limits.get_limit_min_color(channel)
            return CriterionResult(
                channel=channel,
                value=value,
                rating=rating,
                color=color,
            )

    def calculation(self) -> CriterionResult:
        rating = self.min_of_children()
        if self.shoulder_bottoming:
            rating = {
                0.0: -2.0,
                -2.0: -10.0,
                -10.0: -35.0,
                -35.0: -35.0,
            }[rating]
        color = {
            0.0: Limit_G.color,
            -2.0: Limit_A.color,
            -10.0: Limit_M.color,
            -35.0: Limit_P.color,
        }[rating]
        return CriterionResult(
            channel=None,
            value=rating,
            rating=rating,
            color=color,
        )

    criterion_rib_deflection = sub(Criterion_Rib_Deflection)
    criterion_rib_deflection_rate = sub(Criterion_Rib_Deflection_Rate)
    criterion_viscous_criterion = sub(Criterion_Viscous_Criterion)


class Criterion_Pelvis(Criterion):
    name = "Pelvis"
    validate_ignore = {
        "limit_flags": "discrete demerits use successive upper bounds with interpolation disabled",
    }

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}ACTBLE00??FOY?", "?{p}ILUMLE00??FOY?")
        return [
            Limit_G(codes, lambda x: 4.0, y_unit="kN", upper=True, rating=0),
            Limit_A(codes, lambda x: 5.0, y_unit="kN", upper=True, rating=-2),
            Limit_M(codes, lambda x: 6.0, y_unit="kN", upper=True, rating=-6),
            Limit_P(codes, lambda x: 6.0, y_unit="kN", lower=True, rating=-10),
        ]

    def calculation(self) -> CriterionResult:
        channels = [
            self.require_channel(code)
            for code in self.ctx.codes(
                "?{p}ACTBLE00??FOYB",
                "?{p}ILUMLE00??FOYB",
            )
        ]
        time = time_intersect(*channels)
        if not len(time):
            raise ValueError(
                "acetabulum and ilium force channels have no common time samples"
            )
        combined = np.sum(
            [
                np.maximum(channel.get_data(t=time, unit="kN"), 0.0)
                for channel in channels
            ],
            axis=0,
        )
        value = float(np.max(combined))
        channel = Channel(channels[0].code, pd.DataFrame(combined, index=time), "kN")
        evaluation = self.limits.evaluate(channel)
        rating = evaluation.get_limit_min_rating(interpolate=False)
        color = evaluation.get_limit_min_color()
        return CriterionResult(
            channel=channel,
            value=value,
            rating=rating,
            color=color,
        )


class Criterion_Head_Protection(Criterion):
    name = "Head protection"
    head_protection_system_equipped: Manual[
        bool,
        manual(
            True,
            source="high-speed video and postcrash inspection",
            doc="A side head-protection system is equipped for this seating position.",
        ),
    ]
    head_contained: Manual[
        bool,
        manual(
            True,
            source="high-speed video",
            doc="The head remains contained and protected by the side head-protection system.",
        ),
    ]
    direct_mdb_contact: Manual[
        bool,
        manual(
            False,
            source="high-speed video and physical evidence",
            doc="The head directly contacts the moving deformable barrier.",
        ),
    ]
    interior_contact: Manual[
        bool,
        manual(
            False,
            source="high-speed video and physical evidence",
            doc="The head contacts vehicle interior hard structure or bottoms out the airbag.",
        ),
    ]
    head_acceleration_over_70g: Manual[
        bool,
        manual(
            False,
            source="head resultant acceleration",
            doc="The resultant head acceleration exceeds 70 g during the relevant event.",
        ),
    ]

    def calculation(self) -> CriterionResult:
        if self.direct_mdb_contact or not self.head_contained:
            rating, color = -22.0, Limit_P.color
        elif not self.head_protection_system_equipped:
            rating, color = -10.0, Limit_M.color
        elif self.interior_contact and self.head_acceleration_over_70g:
            rating, color = -10.0, Limit_M.color
        elif self.interior_contact or self.head_acceleration_over_70g:
            rating, color = -2.0, Limit_A.color
        else:
            rating, color = 0.0, Limit_G.color
        value = -rating
        return CriterionResult(
            channel=None,
            value=value,
            rating=rating,
            color=color,
        )


class Criterion_Occupant(Criterion):
    name = "Occupant injury measures"
    role = Role.AGGREGATE
    aggregation = "sum"

    def calculation(self) -> CriterionResult:
        rating = self.sum_of_children()
        value = -rating
        return CriterionResult(
            channel=None,
            value=value,
            rating=rating,
            color=None,
        )

    criterion_head_neck = sub(Criterion_Head_Neck, role=Role.AGGREGATE)
    criterion_torso = sub(Criterion_Torso, role=Role.AGGREGATE)
    criterion_pelvis = sub(Criterion_Pelvis)
    criterion_head_protection = sub(Criterion_Head_Protection)


class Overall(Criterion):
    name = "Overall"
    role = Role.AGGREGATE
    source = "Injury measures and rating boundaries / Tables 1 and 3"
    aggregation = "sum"
    p_driver: Manual[str, P_DRIVER]
    p_rear_passenger: Manual[str, P_REAR_PASSENGER]

    def __init__(self, report: Report[Any], isomme: Isomme) -> None:
        super().__init__(report, isomme)
        self.prepare()

    def prepare(self) -> None:
        position = self.isomme.get_test_info("Driver position object 1")
        if position is not None:
            self.set_derived_input("p_driver", str(position).strip())
        self.set_derived_input("p_rear_passenger", "6" if self.p_driver == "1" else "4")

    class Criterion_Structure(Criterion):
        name = "Vehicle structure"
        b_pillar_to_seat_centerline_cm: Manual[
            float,
            manual(
                float(np.nan),
                unit="cm",
                source="postcrash intrusion measurement",
                doc="Minimum longitudinal B-pillar distance relative to the driver seat centerline.",
            ),
        ]
        door_opened: Manual[
            bool,
            manual(
                False,
                source="postcrash inspection",
                doc="A door opening occurred during the impact and requires a one-category downgrade.",
            ),
        ]
        integrity_failure: Manual[
            bool,
            manual(
                False,
                source="postcrash inspection",
                doc="Significant fuel leak, electrical compromise, smoke, fire, or battery thermal event.",
            ),
        ]

        def calculation(self) -> CriterionResult:
            distance = self.b_pillar_to_seat_centerline_cm
            if np.isnan(distance):
                rating = float(np.nan)
                return CriterionResult(
                    channel=None, value=distance, rating=rating, color=None
                )
            elif distance > 18.0:
                rating, color = 0.0, Limit_G.color
            elif distance >= 14.0:
                rating, color = -2.0, Limit_A.color
            elif distance >= 10.0:
                rating, color = -10.0, Limit_M.color
            else:
                rating, color = -22.0, Limit_P.color
            if self.integrity_failure:
                rating, color = -22.0, Limit_P.color
            elif self.door_opened:
                rating, color = {
                    0.0: (-2.0, Limit_A.color),
                    -2.0: (-10.0, Limit_M.color),
                    -10.0: (-22.0, Limit_P.color),
                    -22.0: (-22.0, Limit_P.color),
                }[rating]
            value = distance
            rating, color = rating, color
            return CriterionResult(
                channel=None,
                value=value,
                rating=rating,
                color=color,
            )

    def calculation(self) -> CriterionResult:
        rating = self.sum_of_children()
        value = -rating
        if value <= 8:
            color = Limit_G.color
        elif value <= 20:
            color = Limit_A.color
        elif value <= 34:
            color = Limit_M.color
        else:
            color = Limit_P.color
        return CriterionResult(
            channel=None,
            value=value,
            rating=rating,
            color=color,
        )

    criterion_driver = sub(
        Criterion_Occupant,
        name="Driver",
        at=from_input(P_DRIVER),
        role=Role.AGGREGATE,
    )
    criterion_rear_passenger = sub(
        Criterion_Occupant,
        name="Rear passenger",
        at=from_input(P_REAR_PASSENGER),
        role=Role.AGGREGATE,
    )
    criterion_structure = sub(Criterion_Structure)


class IIHS_Side_Impact(Report[Overall]):
    _name = "IIHS | Side Impact Crashworthiness"
    _protocol = PROTOCOL_SIDE_IMPACT_IV
    _protocols = (PROTOCOL_SIDE_IMPACT_IV,)
    Criterion_Overall = Overall

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._available_pages = (
            CoverPage(self),
            CriterionTablePage(
                            self,
                            name='Overall Rating',
                            title='Overall Rating',
                            spec=rating_table_spec_for(self).with_criteria(lambda report: {isomme: [report.overall(isomme), report.overall(isomme).criterion_driver.criterion_head_neck, report.overall(isomme).criterion_driver.criterion_torso, report.overall(isomme).criterion_driver.criterion_pelvis, report.overall(isomme).criterion_driver.criterion_head_protection, report.overall(isomme).criterion_rear_passenger.criterion_head_neck, report.overall(isomme).criterion_rear_passenger.criterion_torso, report.overall(isomme).criterion_rear_passenger.criterion_pelvis, report.overall(isomme).criterion_rear_passenger.criterion_head_protection, report.overall(isomme).criterion_structure] for isomme in report.isomme_list}),
                        ),
            CriterionTablePage(
                            self,
                            name='Driver Ratings',
                            title='Driver Ratings',
                            spec=rating_table_spec_for(self).with_criteria(lambda report: {isomme: [report.overall(isomme).criterion_driver.criterion_head_neck, report.overall(isomme).criterion_driver.criterion_torso, report.overall(isomme).criterion_driver.criterion_pelvis, report.overall(isomme).criterion_driver.criterion_head_protection, report.overall(isomme).criterion_driver] for isomme in report.isomme_list}),
                        ),
            CriterionValuesChartPage(
                            self,
                            spec=criterion_values_chart_spec_for(
                                self, name='Driver Values Chart', title='Driver Injury Values'
                            ).with_criteria(lambda report: {isomme: [report.overall(isomme).criterion_driver.criterion_head_neck.criterion_hic_15, report.overall(isomme).criterion_driver.criterion_head_neck.criterion_neck_tension, report.overall(isomme).criterion_driver.criterion_head_neck.criterion_neck_compression, report.overall(isomme).criterion_driver.criterion_torso.criterion_rib_deflection, report.overall(isomme).criterion_driver.criterion_torso.criterion_rib_deflection_rate, report.overall(isomme).criterion_driver.criterion_torso.criterion_viscous_criterion, report.overall(isomme).criterion_driver.criterion_pelvis] for isomme in report.isomme_list}),
                        ),
            CriterionTablePage(
                            self,
                            name='Driver Values Table',
                            title='Driver Injury Values',
                            spec=values_table_spec_for(self).with_criteria(lambda report: {isomme: [report.overall(isomme).criterion_driver.criterion_head_neck.criterion_hic_15, report.overall(isomme).criterion_driver.criterion_head_neck.criterion_neck_tension, report.overall(isomme).criterion_driver.criterion_head_neck.criterion_neck_compression, report.overall(isomme).criterion_driver.criterion_torso.criterion_rib_deflection, report.overall(isomme).criterion_driver.criterion_torso.criterion_rib_deflection_rate, report.overall(isomme).criterion_driver.criterion_torso.criterion_viscous_criterion, report.overall(isomme).criterion_driver.criterion_pelvis] for isomme in report.isomme_list}),
                        ),
            ChannelPlotPage(self, spec=driver_head_acceleration_spec_for(self)),
            HICPage(
                self,
                spec=hic_spec_for(
                    self,
                    name="Driver HIC15",
                    title="Driver HIC15",
                    timespan=15,
                ).with_position(
                    lambda report, isomme: report.overall(isomme).p_driver
                ).with_criterion(
                    lambda report, isomme: report.overall(
                        isomme
                    ).criterion_driver.criterion_head_neck.criterion_hic_15
                ),
            ),
            ChannelPlotPage(
                            self,
                            spec=channel_plot_spec_for(
                                self, name='Driver Neck Axial Load', title='Driver Neck Axial Load'
                            ).with_channels(lambda report: {isomme: [[f'?{report.overall(isomme).p_driver}NECKUP00??FOZB']] for isomme in report.isomme_list}),
                        ),
            ChannelPlotPage(
                            self,
                            spec=channel_plot_spec_for(
                                self, name='Driver Rib Deflection', title='Driver Rib Deflection'
                            ).with_channels(lambda report: {isomme: [[f'?{report.overall(isomme).p_driver}TRRILE01??DSYC', f'?{report.overall(isomme).p_driver}TRRILE02??DSYC', f'?{report.overall(isomme).p_driver}TRRILE03??DSYC'], [f'?{report.overall(isomme).p_driver}ABRILE01??DSYC', f'?{report.overall(isomme).p_driver}ABRILE02??DSYC']] for isomme in report.isomme_list}),
                        ),
            ChannelPlotPage(
                            self,
                            spec=channel_plot_spec_for(
                                self, name='Driver Rib Deflection Rate', title='Driver Rib Deflection Rate'
                            ).with_channels(lambda report: {isomme: [[f'?{report.overall(isomme).p_driver}TRRILE01??VEY?', f'?{report.overall(isomme).p_driver}TRRILE02??VEY?', f'?{report.overall(isomme).p_driver}TRRILE03??VEY?'], [f'?{report.overall(isomme).p_driver}ABRILE01??VEY?', f'?{report.overall(isomme).p_driver}ABRILE02??VEY?']] for isomme in report.isomme_list}),
                        ),
            ChannelPlotPage(
                            self,
                            spec=channel_plot_spec_for(
                                self, name='Driver Viscous Criterion', title='Driver Viscous Criterion'
                            ).with_channels(lambda report: {isomme: [[f'?{report.overall(isomme).p_driver}VCCRLE01??VEY?', f'?{report.overall(isomme).p_driver}VCCRLE02??VEY?', f'?{report.overall(isomme).p_driver}VCCRLE03??VEY?'], [f'?{report.overall(isomme).p_driver}VCARLE01??VEY?', f'?{report.overall(isomme).p_driver}VCARLE02??VEY?']] for isomme in report.isomme_list}),
                        ),
            ChannelPlotPage(
                            self,
                            spec=channel_plot_spec_for(
                                self, name='Driver Pelvis Force', title='Driver Pelvis Force'
                            ).with_channels(lambda report: {isomme: [[f'?{report.overall(isomme).p_driver}ACTBLE00??FOYB'], [f'?{report.overall(isomme).p_driver}ILUMLE00??FOYB']] for isomme in report.isomme_list}),
                        ),
            CriterionTablePage(
                            self,
                            name='Rear Passenger Ratings',
                            title='Rear Passenger Ratings',
                            spec=rating_table_spec_for(self).with_criteria(lambda report: {isomme: [report.overall(isomme).criterion_rear_passenger.criterion_head_neck, report.overall(isomme).criterion_rear_passenger.criterion_torso, report.overall(isomme).criterion_rear_passenger.criterion_pelvis, report.overall(isomme).criterion_rear_passenger.criterion_head_protection, report.overall(isomme).criterion_rear_passenger] for isomme in report.isomme_list}),
                        ),
            CriterionValuesChartPage(
                            self,
                            spec=criterion_values_chart_spec_for(
                                self, name='Rear Passenger Values Chart', title='Rear Passenger Injury Values'
                            ).with_criteria(lambda report: {isomme: [report.overall(isomme).criterion_rear_passenger.criterion_head_neck.criterion_hic_15, report.overall(isomme).criterion_rear_passenger.criterion_head_neck.criterion_neck_tension, report.overall(isomme).criterion_rear_passenger.criterion_head_neck.criterion_neck_compression, report.overall(isomme).criterion_rear_passenger.criterion_torso.criterion_rib_deflection, report.overall(isomme).criterion_rear_passenger.criterion_torso.criterion_rib_deflection_rate, report.overall(isomme).criterion_rear_passenger.criterion_torso.criterion_viscous_criterion, report.overall(isomme).criterion_rear_passenger.criterion_pelvis] for isomme in report.isomme_list}),
                        ),
            CriterionTablePage(
                            self,
                            name='Rear Passenger Values Table',
                            title='Rear Passenger Injury Values',
                            spec=values_table_spec_for(self).with_criteria(lambda report: {isomme: [report.overall(isomme).criterion_rear_passenger.criterion_head_neck.criterion_hic_15, report.overall(isomme).criterion_rear_passenger.criterion_head_neck.criterion_neck_tension, report.overall(isomme).criterion_rear_passenger.criterion_head_neck.criterion_neck_compression, report.overall(isomme).criterion_rear_passenger.criterion_torso.criterion_rib_deflection, report.overall(isomme).criterion_rear_passenger.criterion_torso.criterion_rib_deflection_rate, report.overall(isomme).criterion_rear_passenger.criterion_torso.criterion_viscous_criterion, report.overall(isomme).criterion_rear_passenger.criterion_pelvis] for isomme in report.isomme_list}),
                        ),
            ChannelPlotPage(
                            self,
                            spec=channel_plot_spec_for(
                                self, name='Rear Passenger Head Acceleration', title='Rear Passenger Head Acceleration'
                            ).with_channels(lambda report: {isomme: [[f'?{report.overall(isomme).p_rear_passenger}HEAD??????AC{axis}A'] for axis in 'XYZR'] for isomme in report.isomme_list}),
                        ),
            HICPage(
                self,
                spec=hic_spec_for(
                    self,
                    name="Rear Passenger HIC15",
                    title="Rear Passenger HIC15",
                    timespan=15,
                ).with_position(
                    lambda report, isomme: report.overall(
                        isomme
                    ).p_rear_passenger
                ).with_criterion(
                    lambda report, isomme: report.overall(
                        isomme
                    ).criterion_rear_passenger.criterion_head_neck.criterion_hic_15
                ),
            ),
            ChannelPlotPage(
                            self,
                            spec=channel_plot_spec_for(
                                self, name='Rear Passenger Neck Axial Load', title='Rear Passenger Neck Axial Load'
                            ).with_channels(lambda report: {isomme: [[f'?{report.overall(isomme).p_rear_passenger}NECKUP00??FOZB']] for isomme in report.isomme_list}),
                        ),
            ChannelPlotPage(
                            self,
                            spec=channel_plot_spec_for(
                                self, name='Rear Passenger Rib Deflection', title='Rear Passenger Rib Deflection'
                            ).with_channels(lambda report: {isomme: [[f'?{report.overall(isomme).p_rear_passenger}TRRILE01??DSYC', f'?{report.overall(isomme).p_rear_passenger}TRRILE02??DSYC', f'?{report.overall(isomme).p_rear_passenger}TRRILE03??DSYC'], [f'?{report.overall(isomme).p_rear_passenger}ABRILE01??DSYC', f'?{report.overall(isomme).p_rear_passenger}ABRILE02??DSYC']] for isomme in report.isomme_list}),
                        ),
            ChannelPlotPage(
                            self,
                            spec=channel_plot_spec_for(
                                self, name='Rear Passenger Rib Deflection Rate', title='Rear Passenger Rib Deflection Rate'
                            ).with_channels(lambda report: {isomme: [[f'?{report.overall(isomme).p_rear_passenger}TRRILE01??VEY?', f'?{report.overall(isomme).p_rear_passenger}TRRILE02??VEY?', f'?{report.overall(isomme).p_rear_passenger}TRRILE03??VEY?'], [f'?{report.overall(isomme).p_rear_passenger}ABRILE01??VEY?', f'?{report.overall(isomme).p_rear_passenger}ABRILE02??VEY?']] for isomme in report.isomme_list}),
                        ),
            ChannelPlotPage(
                            self,
                            spec=channel_plot_spec_for(
                                self, name='Rear Passenger Viscous Criterion', title='Rear Passenger Viscous Criterion'
                            ).with_channels(lambda report: {isomme: [[f'?{report.overall(isomme).p_rear_passenger}VCCRLE01??VEY?', f'?{report.overall(isomme).p_rear_passenger}VCCRLE02??VEY?', f'?{report.overall(isomme).p_rear_passenger}VCCRLE03??VEY?'], [f'?{report.overall(isomme).p_rear_passenger}VCARLE01??VEY?', f'?{report.overall(isomme).p_rear_passenger}VCARLE02??VEY?']] for isomme in report.isomme_list}),
                        ),
            ChannelPlotPage(
                            self,
                            spec=channel_plot_spec_for(
                                self, name='Rear Passenger Pelvis Force', title='Rear Passenger Pelvis Force'
                            ).with_channels(lambda report: {isomme: [[f'?{report.overall(isomme).p_rear_passenger}ACTBLE00??FOYB'], [f'?{report.overall(isomme).p_rear_passenger}ILUMLE00??FOYB']] for isomme in report.isomme_list}),
                        ),
        )
        self._selected_pages = list(self._available_pages)
