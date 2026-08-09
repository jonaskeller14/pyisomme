from __future__ import annotations

from pyisomme import Unit, g0
from pyisomme.isomme import Isomme
from pyisomme.report.page import Page_Cover, Page_Criterion_Values_Chart, Page_Criterion_Values_Table, Page_Plot_nxn
from pyisomme.limit import Limit
from pyisomme.report.report import Report
from pyisomme.report.criterion import Criterion, Role, sub
from pyisomme.report.ctx import from_input
from pyisomme.report.manual import Manual, manual
from pyisomme.report.un.limits import Limit_Fail, Limit_Pass
from pyisomme.report.un.protocols import protocol_r135_2016
from pyisomme.report.euro_ncap.side_pole import EuroNCAP_Side_Pole

import logging
import numpy as np
from typing import Any


logger = logging.getLogger(__name__)

P = manual("1", source="test report", doc=(
    "Channel-code position of the struck-side occupant — the only occupant "
    "the regulation assesses. Defaults to the 'Driver position object 1' "
    "test-info field when the test carries it."))


class Overall(Criterion):
    name = "Overall"
    role = Role.AGGREGATE
    p: Manual[str, P]

    def __init__(self, report: Report, isomme: Isomme) -> None:
        super().__init__(report, isomme)
        # Also at construction: the pages read `p` when the report is built.
        self.prepare()

    def prepare(self) -> None:
        """Take the struck-side position from the test info before the occupant reads it."""
        p = self.isomme.get_test_info("Driver position object 1")
        if p is not None:
            self.set_derived_input("p", str(p).strip())

    def calculation(self) -> None:
        self.rating = self.criterion_dummy.rating

    class Criterion_Dummy(Criterion):
        name = "Dummy"

        def calculation(self) -> None:
            self.rating = np.min([
                self.criterion_hic_36.rating,
                self.criterion_shoulder_lateral_force.rating,
                self.criterion_chest_resultant_compression.rating,
                self.criterion_abdomen_resultant_compression.rating,
                self.criterion_spine_t12_a3ms.rating,
                self.criterion_pubic_symphysis_force.rating,
            ])

        class Criterion_HIC_36(Criterion):
            name = "HIC 36"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}HICR0036??00RX", "?{p}HICRCG36??00RX")
                return [
                    Limit_Pass(codes, func=lambda x: 1000, y_unit=1, upper=True),
                    Limit_Fail(codes, func=lambda x: 1000, y_unit=1, lower=True),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(self.ctx.code("?{p}HICR0036??00RX"), self.ctx.code("?{p}HICRCG36??00RX"))
                self.value = self.channel.get_data()[0]
                self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Shoulder_Lateral_Force(Criterion):
            name = "Shoulder Lateral Force"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}SHLD0000??FOY?", "?{p}SHLDLE00??FOY?", "?{p}SHLDRI00??FOY?")
                return [
                    Limit_Fail(codes, func=lambda x: -3, y_unit="kN", upper=True),
                    Limit_Pass(codes, func=lambda x: -3, y_unit="kN", lower=True),
                    Limit_Pass(codes, func=lambda x: 3, y_unit="kN", upper=True),
                    Limit_Fail(codes, func=lambda x: 3., y_unit="kN", lower=True),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(self.ctx.code("?{p}SHLD0000??FOYB")).convert_unit("kN")
                self.value = self.channel.get_data()[np.argmax(np.abs(self.channel.get_data()))]
                self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Chest_Resultant_Compression(Criterion):
            name = "Chest Resultant Compression"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}TRRI??0[0123]??DSR?")
                return [
                    Limit_Fail(codes, func=lambda x: -55, y_unit="mm", upper=True),
                    Limit_Pass(codes, func=lambda x: -55, y_unit="mm", lower=True),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(self.ctx.code("?{p}TRRI??00??DSRB")).convert_unit("mm")
                self.value = np.min(self.channel.get_data())
                self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Abdomen_Resultant_Compression(Criterion):
            name = "Abdomen Resultant Compression"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}ABRI??0[012]??DSR?")
                return [
                    Limit_Fail(codes, func=lambda x: -65, y_unit="mm", upper=True),
                    Limit_Pass(codes, func=lambda x: -65, y_unit="mm", lower=True),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(self.ctx.code("?{p}ABRI??00??DSRB")).convert_unit("mm")
                self.value = np.min(self.channel.get_data())
                self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Spine_T12_a3ms(Criterion):
            name = "Spine T12 Acceleration a3ms"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("1{p}THSP123C??ACR?")
                return [
                    Limit_Pass(codes, func=lambda x: 75, y_unit=Unit(g0), upper=True),
                    Limit_Fail(codes, func=lambda x: 75, y_unit=Unit(g0), lower=True),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(self.ctx.code("1{p}THSP123C??ACRX")).convert_unit(Unit(g0))
                self.value = np.max(self.channel.get_data())
                self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                self.color = self.limits.get_limit_min_color(self.channel)

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

            def calculation(self) -> None:
                self.channel = self.require_channel(self.ctx.code("?{p}PUBC0000??FOYB")).convert_unit("kN")
                self.value = self.channel.get_data()[np.argmax(np.abs(self.channel.get_data()))]
                self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=True)
                self.color = self.limits.get_limit_min_color(self.channel)

        criterion_hic_36 = sub(Criterion_HIC_36)
        criterion_shoulder_lateral_force = sub(Criterion_Shoulder_Lateral_Force)
        criterion_chest_resultant_compression = sub(Criterion_Chest_Resultant_Compression)
        criterion_abdomen_resultant_compression = sub(Criterion_Abdomen_Resultant_Compression)
        criterion_spine_t12_a3ms = sub(Criterion_Spine_T12_a3ms)
        criterion_pubic_symphysis_force = sub(Criterion_Pubic_Symphysis_Force)

    criterion_dummy = sub(Criterion_Dummy, at=from_input(P), role=Role.AGGREGATE)


class UN_Side_Pole_R135(Report[Overall]):
    _name = "UN-R135 | Pole Side Impact at 32 km/h"
    _protocol = protocol_r135_2016
    _protocols = (protocol_r135_2016,)
    Criterion_Overall = Overall

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._available_pages = (
            Page_Cover(self),

            self.Page_Values_Chart(self),
            self.Page_Values_Table(self),
            self.Page_Head_Acceleration(self),
            self.Page_Shoulder_Lateral_Force(self),
            self.Page_Chest_Absolute_Compression(self),
            self.Page_Abdomen_Resultant_Compression(self),
            self.Page_Spine_T12_Acceleration(self),
            self.Page_Pubic_Symphysis_Force(self),
        )
        self._selected_pages = list(self._available_pages)

    class Page_Values_Chart(Page_Criterion_Values_Chart):
        report: UN_Side_Pole_R135
        name = "Values Chart"
        title = "Values"

        def __init__(self, report: UN_Side_Pole_R135) -> None:
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_dummy.criterion_hic_36,
                self.report.criterion_overall[isomme].criterion_dummy.criterion_shoulder_lateral_force,
                self.report.criterion_overall[isomme].criterion_dummy.criterion_chest_resultant_compression,
                self.report.criterion_overall[isomme].criterion_dummy.criterion_abdomen_resultant_compression,
                self.report.criterion_overall[isomme].criterion_dummy.criterion_spine_t12_a3ms,
                self.report.criterion_overall[isomme].criterion_dummy.criterion_pubic_symphysis_force,
            ] for isomme in self.report.isomme_list}

    class Page_Values_Table(Page_Criterion_Values_Table):
        report: UN_Side_Pole_R135
        name = "Values Table"
        title = "Values"

        def __init__(self, report: UN_Side_Pole_R135) -> None:
            super().__init__(report)

            self.criteria = {isomme: [
                self.report.criterion_overall[isomme].criterion_dummy.criterion_hic_36,
                self.report.criterion_overall[isomme].criterion_dummy.criterion_shoulder_lateral_force,
                self.report.criterion_overall[isomme].criterion_dummy.criterion_chest_resultant_compression,
                self.report.criterion_overall[isomme].criterion_dummy.criterion_abdomen_resultant_compression,
                self.report.criterion_overall[isomme].criterion_dummy.criterion_spine_t12_a3ms,
                self.report.criterion_overall[isomme].criterion_dummy.criterion_pubic_symphysis_force,
            ] for isomme in self.report.isomme_list}

    class Page_Head_Acceleration(EuroNCAP_Side_Pole.Page_Head_Acceleration):
        pass

    class Page_Shoulder_Lateral_Force(EuroNCAP_Side_Pole.Page_Shoulder_Lateral_Force):
        pass

    class Page_Chest_Absolute_Compression(Page_Plot_nxn):
        report: UN_Side_Pole_R135
        name: str = "Chest Absolute Compression"
        title: str = "Chest Absolute Compression"
        nrows: int = 3
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: UN_Side_Pole_R135) -> None:
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p}TRRILE01??DSRB"],
                                      [f"?{self.report.criterion_overall[isomme].p}TRRIRI01??DSRB"],
                                      [f"?{self.report.criterion_overall[isomme].p}TRRILE02??DSRB"],
                                      [f"?{self.report.criterion_overall[isomme].p}TRRIRI02??DSRB"],
                                      [f"?{self.report.criterion_overall[isomme].p}TRRILE03??DSRB"],
                                      [f"?{self.report.criterion_overall[isomme].p}TRRIRI04??DSRB"]] for isomme in self.report.isomme_list}

    class Page_Abdomen_Resultant_Compression(Page_Plot_nxn):
        report: UN_Side_Pole_R135
        name: str = "Abdomen Resultant Compression"
        title: str = "Abdomen Resultant Compression"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: UN_Side_Pole_R135) -> None:
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p}ABRILE01??DSRB"],
                                      [f"?{self.report.criterion_overall[isomme].p}ABRIRI01??DSRB"],
                                      [f"?{self.report.criterion_overall[isomme].p}ABRILE02??DSRB"],
                                      [f"?{self.report.criterion_overall[isomme].p}ABRIRI03??DSRB"]] for isomme in self.report.isomme_list}

    class Page_Spine_T12_Acceleration(Page_Plot_nxn):
        report: UN_Side_Pole_R135
        name: str = "Spine T12 Acceleration"
        title: str = "Spine T12 Acceleration"
        nrows: int = 2
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: UN_Side_Pole_R135) -> None:
            super().__init__(report)
            self.channels = {isomme: [[f"?{self.report.criterion_overall[isomme].p}THSP1200??AC{xyzr}C"] for xyzr in "XYZR"] for isomme in self.report.isomme_list}

    class Page_Pubic_Symphysis_Force(EuroNCAP_Side_Pole.Page_Pubic_Symphysis_Force):
        pass
