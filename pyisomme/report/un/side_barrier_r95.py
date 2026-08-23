from __future__ import annotations

import logging
from typing import Any

import numpy as np

from pyisomme.isomme import Isomme
from pyisomme.limit import Limit
from pyisomme.report.criterion import Criterion, Role, sub
from pyisomme.report.ctx import from_input
from pyisomme.report.euro_ncap.side_pole import EuroNCAP_Side_Pole
from pyisomme.report.manual import Manual, manual
from pyisomme.report.page import (
    Page_Cover,
    Page_Criterion_Values_Chart,
    Page_Criterion_Values_Table,
    Page_Plot_nxn,
)
from pyisomme.report.report import Report
from pyisomme.report.un.frontal_50kmh_r137 import (
    Criterion_HPC36 as Criterion_HPC36_R137,
)
from pyisomme.report.un.limits import Limit_Fail, Limit_Pass
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

    def calculation(self) -> None:
        self.rating = self.criterion_dummy.rating

    class Criterion_Dummy(Criterion):
        name = "Dummy"
        role = Role.AGGREGATE

        def calculation(self) -> None:
            self.rating = np.min(
                [
                    self.criterion_hpc36.rating,
                    self.criterion_chest_lateral_deflection.rating,
                    self.criterion_chest_lateral_vc.rating,
                    self.criterion_pubic_symphysis_force.rating,
                    self.criterion_abdomen_force.rating,
                ]
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

            def calculation(self) -> None:
                self.channel = self.require_channel(
                    self.ctx.code("?{p}RIBSLE00??DSYC")
                ).convert_unit("mm")
                self.value = np.min(self.channel.get_data())
                self.rating = self.limits.get_limit_min_rating(
                    self.channel, interpolate=False
                )
                self.color = self.limits.get_limit_min_color(self.channel)

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

            def calculation(self) -> None:
                self.channel = self.require_channel(
                    self.ctx.code("?{p}VCCRLE00??VEYC")
                ).convert_unit("m/s")
                self.value = np.min(self.channel.get_data())
                self.rating = self.limits.get_limit_min_rating(
                    self.channel, interpolate=False
                )
                self.color = self.limits.get_limit_min_color(self.channel)

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

            def calculation(self) -> None:
                self.channel = self.require_channel(
                    self.ctx.code("?{p}ABDOLE00??FOYB")
                ).convert_unit("kN")
                self.value = np.min(self.channel.get_data())
                self.rating = self.limits.get_limit_min_rating(
                    self.channel, interpolate=False
                )
                self.color = self.limits.get_limit_min_color(self.channel)

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
            Page_Cover(self),
            self.Page_Values_Chart(self),
            self.Page_Values_Table(self),
            self.Page_Head_Acceleration(self),
            self.Page_Chest_Lateral_Deflection(self),
            self.Page_Chest_Lateral_VC(self),
            self.Page_Pubic_Symphysis_Force(self),
            self.Page_Abdomen_Force(self),
        )
        self._selected_pages = list(self._available_pages)

    class Page_Values_Chart(Page_Criterion_Values_Chart):
        report: UN_Side_Barrier_R95
        name = "Values Chart"
        title = "Values"

        def __init__(self, report: UN_Side_Barrier_R95) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_dummy.criterion_hpc36,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_dummy.criterion_chest_lateral_deflection,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_dummy.criterion_chest_lateral_vc,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_dummy.criterion_pubic_symphysis_force,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_dummy.criterion_abdomen_force,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Values_Table(Page_Criterion_Values_Table):
        report: UN_Side_Barrier_R95
        name = "Values Table"
        title = "Values"

        def __init__(self, report: UN_Side_Barrier_R95) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_dummy.criterion_hpc36,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_dummy.criterion_chest_lateral_deflection,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_dummy.criterion_chest_lateral_vc,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_dummy.criterion_pubic_symphysis_force,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_dummy.criterion_abdomen_force,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Head_Acceleration(EuroNCAP_Side_Pole.Page_Head_Acceleration):
        pass

    class Page_Chest_Lateral_Deflection(Page_Plot_nxn):
        report: UN_Side_Barrier_R95
        name: str = "Chest Lateral Deflection"
        title: str = "Chest Lateral Deflection"
        nrows: int = 3
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: UN_Side_Barrier_R95) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{self.report.criterion_overall[isomme].p}RIBSLEUP??DSYC"],
                    [f"?{self.report.criterion_overall[isomme].p}RIBSRIUP??DSYC"],
                    [f"?{self.report.criterion_overall[isomme].p}RIBSLEMI??DSYC"],
                    [f"?{self.report.criterion_overall[isomme].p}RIBSRIMI??DSYC"],
                    [f"?{self.report.criterion_overall[isomme].p}RIBSLELO??DSYC"],
                    [f"?{self.report.criterion_overall[isomme].p}RIBSRILO??DSYC"],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Chest_Lateral_VC(Page_Plot_nxn):
        report: UN_Side_Barrier_R95
        name: str = "Chest Lateral VC"
        title: str = "Chest Lateral VC"
        nrows: int = 3
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: UN_Side_Barrier_R95) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{self.report.criterion_overall[isomme].p}VCCRLEUP??VEYC"],
                    [f"?{self.report.criterion_overall[isomme].p}VCCRRIUP??VEYC"],
                    [f"?{self.report.criterion_overall[isomme].p}VCCRLEMI??VEYC"],
                    [f"?{self.report.criterion_overall[isomme].p}VCCRRIMI??VEYC"],
                    [f"?{self.report.criterion_overall[isomme].p}VCCRLELO??VEYC"],
                    [f"?{self.report.criterion_overall[isomme].p}VCCRRILO??VEYC"],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Pubic_Symphysis_Force(EuroNCAP_Side_Pole.Page_Pubic_Symphysis_Force):
        pass

    class Page_Abdomen_Force(Page_Plot_nxn):
        report: UN_Side_Barrier_R95
        name: str = "Abdomen Force"
        title: str = "Abdomen Force"
        nrows: int = 3
        ncols: int = 2
        sharey: bool = True

        def __init__(self, report: UN_Side_Barrier_R95) -> None:
            super().__init__(report)
            self.channels = {
                isomme: [
                    [f"?{self.report.criterion_overall[isomme].p}ABDOLEFR??FOYB"],
                    [f"?{self.report.criterion_overall[isomme].p}ABDORIFR??FOYB"],
                    [f"?{self.report.criterion_overall[isomme].p}ABDOLEMI??FOYB"],
                    [f"?{self.report.criterion_overall[isomme].p}ABDORIMI??FOYB"],
                    [f"?{self.report.criterion_overall[isomme].p}ABDOLERE??FOYB"],
                    [f"?{self.report.criterion_overall[isomme].p}ABDORIRE??FOYB"],
                ]
                for isomme in self.report.isomme_list
            }
