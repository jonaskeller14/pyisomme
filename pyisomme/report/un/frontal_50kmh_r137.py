from __future__ import annotations

import logging
from typing import Any

import numpy as np

from pyisomme.isomme import Isomme
from pyisomme.limit import Limit
from pyisomme.report.criterion import Criterion, Role, sub
from pyisomme.report.ctx import from_input
from pyisomme.report.euro_ncap.frontal_50kmh import EuroNCAP_Frontal_50kmh
from pyisomme.report.euro_ncap.frontal_mpdb import EuroNCAP_Frontal_MPDB
from pyisomme.report.manual import Manual, manual
from pyisomme.report.page import (
    Page_Cover,
    Page_Criterion_Rating_Table,
    Page_Criterion_Values_Chart,
    Page_Criterion_Values_Table,
)
from pyisomme.report.report import Report
from pyisomme.report.un.limits import Limit_Fail, Limit_Pass
from pyisomme.report.un.protocols import PROTOCOL_R137_2016, PROTOCOL_R137_2023
from pyisomme.unit import Unit, g0

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


# TODO(step-10): the four criteria the driver and the passenger share. Lifted out of
#   `Overall.Criterion_Driver` because a `sub()` in a class body can only name what is
#   already bound, and `Overall` is not bound inside its own body. Step 10's shared
#   criteria library is where these belong.


class Criterion_HPC36(Criterion):
    name = "Head Performance Criterion (HPC 36)"
    head_contact: Manual[
        bool,
        manual(
            True,
            source="video",
            doc=(
                "Was head contact observed? Without it HPC 36 is not assessed and passes."
            ),
        ),
    ]

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}HICR0036??00RX", "?{p}HICRCG36??00RX")
        return [
            Limit_Pass(codes, func=lambda x: 1000, y_unit=1, upper=True),
            Limit_Fail(codes, func=lambda x: 1000, y_unit=1, lower=True),
        ]

    def calculation(self) -> None:
        if self.head_contact:
            self.channel = self.require_channel(
                self.ctx.code("?{p}HICR0036??00RX"), self.ctx.code("?{p}HICRCG36??00RX")
            )
            self.value = self.channel.get_data()[0]
            self.rating = self.limits.get_limit_min_rating(
                self.channel, interpolate=False
            )
            self.color = self.limits.get_limit_min_color(self.channel)
        else:
            self.rating = True
            self.color = Limit_Pass.color


class Criterion_Head_a3ms(Criterion):
    name = "Head a3ms"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}HEAD003C??ACR?", "?{p}HEADCG3C??ACR?")
        return [
            Limit_Pass(codes, func=lambda x: 80, y_unit=Unit(g0), upper=True),
            Limit_Fail(codes, func=lambda x: 80, y_unit=Unit(g0), lower=True),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(
            self.ctx.code("?{p}HEAD003C??ACRX"), self.ctx.code("?{p}HEADCG3C??ACRX")
        )
        self.value = self.channel.get_data(unit=g0)[0]
        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
        self.color = self.limits.get_limit_min_color(self.channel)


class Criterion_Neck_My_extension(Criterion):
    name = "Neck My extension"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}NECKUP00??MOY?")
        return [
            Limit_Pass(codes, func=lambda x: -57, y_unit="Nm", lower=True),
            Limit_Fail(codes, func=lambda x: -57, y_unit="Nm", upper=True),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(self.ctx.code("?{p}NECKUP00??MOYB"))
        self.value = np.min(self.channel.get_data(unit="Nm"))
        self.rating = self.limits.get_limit_min_rating(self.channel)
        self.color = self.limits.get_limit_min_color(self.channel)


class Criterion_Chest_VC(Criterion):
    name = "Chest VC"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}VCCR000[03]??VEX?")
        return [
            Limit_Fail(codes, func=lambda x: -1, y_unit="m/s", upper=True),
            Limit_Pass(codes, func=lambda x: -1, y_unit="m/s", lower=True),
            Limit_Pass(codes, func=lambda x: 1, y_unit="m/s", upper=True),
            Limit_Fail(codes, func=lambda x: 1, y_unit="m/s", lower=True),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(
            self.ctx.code("?{p}VCCR0003??VEXC"), self.ctx.code("?{p}VCCR0000??VEXC")
        ).convert_unit("m/s")
        self.value = np.min(self.channel.get_data())
        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
        self.color = self.limits.get_limit_min_color(self.channel)


class Overall(Criterion):
    report: UN_Frontal_50kmh_R137
    name = "Overall"
    role = Role.AGGREGATE
    p_driver: Manual[str, P_DRIVER]
    p_passenger: Manual[str, P_PASSENGER]

    def __init__(self, report: Report, isomme: Isomme) -> None:
        super().__init__(report, isomme)
        # Also at construction: the pages read the positions when the report is built.
        self.prepare()

    def prepare(self) -> None:
        """Settle both positions before the occupants' ``from_input()`` context reads them."""
        p_driver = self.isomme.get_test_info("Driver position object 1")
        if p_driver is not None:
            self.set_derived_input("p_driver", str(p_driver).strip())
        self.set_derived_input("p_passenger", "1" if self.p_driver != "1" else "3")

    def calculation(self) -> None:
        self.rating = np.min(
            [self.criterion_driver.rating, self.criterion_passenger.rating]
        )

    class Criterion_Driver(Criterion):
        name = "Driver"
        role = Role.AGGREGATE

        def calculation(self) -> None:
            self.rating = np.min(
                [
                    self.criterion_hpc36.rating,
                    self.criterion_head_a3ms.rating,
                    self.criterion_neck_fz_tension.rating,
                    self.criterion_neck_fx_shear.rating,
                    self.criterion_neck_my_extension.rating,
                    self.criterion_chest_deflection.rating,
                    self.criterion_chest_vc.rating,
                    self.criterion_femur_compression.rating,
                ]
            )

        class Criterion_Neck_Fz_tension(Criterion):
            name = "Neck Fz tension"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}NECKUP00??FOZ?")
                return [
                    Limit_Pass(codes, func=lambda x: 3.3, y_unit="kN", upper=True),
                    Limit_Fail(codes, func=lambda x: 3.3, y_unit="kN", lower=True),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(
                    self.ctx.code("?{p}NECKUP00??FOZA")
                ).convert_unit("kN")
                self.value = np.max(self.channel.get_data())
                self.rating = self.limits.get_limit_min_rating(self.channel)
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Neck_Fx_shear(Criterion):
            name = "Neck Fx shear"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}NECKUP00??FOX?")
                return [
                    Limit_Fail(codes, func=lambda x: 3.1, y_unit="kN", lower=True),
                    Limit_Pass(codes, func=lambda x: 3.1, y_unit="kN", upper=True),
                    Limit_Pass(codes, func=lambda x: -3.1, y_unit="kN", lower=True),
                    Limit_Fail(codes, func=lambda x: -3.1, y_unit="kN", upper=True),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(
                    self.ctx.code("?{p}NECKUP00??FOXA")
                ).convert_unit("kN")
                self.value = self.channel.get_data(unit="kN")[
                    np.argmax(np.abs(self.channel.get_data()))
                ]
                self.rating = self.limits.get_limit_min_rating(self.channel)
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Chest_Deflection(Criterion):
            name = "Chest Deflection"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}CHST000[03]??DSX?")
                return [
                    Limit_Fail(codes, func=lambda x: -42, y_unit="mm", upper=True),
                    Limit_Pass(codes, func=lambda x: -42, y_unit="mm", lower=True),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(
                    self.ctx.code("?{p}CHST0000??DSXC")
                ).convert_unit("mm")
                self.value = np.min(self.channel.get_data())
                self.rating = self.limits.get_limit_min_rating(
                    self.channel, interpolate=False
                )
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Femur_Compression(Criterion):
            name = "Femur Compression"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}FEMR??00??FOZ?")
                return [
                    Limit_Fail(
                        codes,
                        func=lambda x: -9.07,
                        y_unit="kN",
                        x_unit="ms",
                        upper=True,
                    ),
                    Limit_Pass(
                        codes,
                        func=lambda x: -9.07,
                        y_unit="kN",
                        x_unit="ms",
                        lower=True,
                    ),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(
                    self.ctx.code("?{p}FEMR0000??FOZB")
                ).convert_unit("kN")
                self.value = self.limits.get_limit_min_y(self.channel)
                self.rating = self.limits.get_limit_min_rating(
                    self.channel, interpolate=False
                )
                self.color = self.limits.get_limit_min_color(self.channel)

        criterion_hpc36 = sub(Criterion_HPC36)
        criterion_head_a3ms = sub(Criterion_Head_a3ms)
        criterion_neck_fz_tension = sub(Criterion_Neck_Fz_tension)
        criterion_neck_fx_shear = sub(Criterion_Neck_Fx_shear)
        criterion_neck_my_extension = sub(Criterion_Neck_My_extension)
        criterion_chest_deflection = sub(Criterion_Chest_Deflection)
        criterion_chest_vc = sub(Criterion_Chest_VC)
        criterion_femur_compression = sub(Criterion_Femur_Compression)

    class Criterion_Passenger(Criterion):
        report: UN_Frontal_50kmh_R137
        name = "Passenger"
        role = Role.AGGREGATE

        def calculation(self) -> None:
            self.rating = np.min(
                [
                    self.criterion_hpc36.rating,
                    self.criterion_head_a3ms.rating,
                    self.criterion_neck_fz_tension.rating,
                    self.criterion_neck_fx_shear.rating,
                    self.criterion_neck_my_extension.rating,
                    self.criterion_chest_deflection.rating,
                    self.criterion_chest_vc.rating,
                    self.criterion_femur_compression.rating,
                ]
            )

        class Criterion_Neck_Fz_tension(Criterion):
            name = "Neck Fz tension"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}NECKUP00??FOZ?")
                return [
                    Limit_Pass(codes, func=lambda x: 2.9, y_unit="kN", upper=True),
                    Limit_Fail(codes, func=lambda x: 2.9, y_unit="kN", lower=True),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(
                    self.ctx.code("?{p}NECKUP00??FOZA")
                ).convert_unit("kN")
                self.value = np.max(self.channel.get_data())
                self.rating = self.limits.get_limit_min_rating(
                    self.channel, interpolate=False
                )
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Neck_Fx_shear(Criterion):
            name = "Neck Fx shear"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}NECKUP00??FOX?")
                return [
                    Limit_Fail(codes, func=lambda x: 2.9, y_unit="kN", lower=True),
                    Limit_Pass(codes, func=lambda x: 2.9, y_unit="kN", upper=True),
                    Limit_Pass(codes, func=lambda x: -2.9, y_unit="kN", lower=True),
                    Limit_Fail(codes, func=lambda x: -2.9, y_unit="kN", upper=True),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(
                    self.ctx.code("?{p}NECKUP00??FOXA")
                ).convert_unit("kN")
                self.value = self.channel.get_data(unit="kN")[
                    np.argmax(np.abs(self.channel.get_data()))
                ]
                self.rating = self.limits.get_limit_min_rating(
                    self.channel, interpolate=False
                )
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Chest_Deflection(Criterion):
            name = "Chest Deflection"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}CHST000[03]??DSX?")
                return [
                    Limit_Fail(
                        codes,
                        func=lambda x: (
                            -42 if self.report.protocol == "22.06.2016" else -34
                        ),
                        y_unit="mm",
                        upper=True,
                    ),
                    Limit_Pass(
                        codes,
                        func=lambda x: (
                            -42 if self.report.protocol == "22.06.2016" else -34
                        ),
                        y_unit="mm",
                        lower=True,
                    ),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(
                    self.ctx.code("?{p}CHST0000??DSXC")
                ).convert_unit("mm")
                self.value = np.min(self.channel.get_data())
                self.rating = self.limits.get_limit_min_rating(
                    self.channel, interpolate=False
                )
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Femur_Compression(Criterion):
            name = "Femur Compression"

            def define_limits(self) -> list[Limit]:
                codes = self.ctx.codes("?{p}FEMR??00??FOZ?")
                return [
                    Limit_Fail(
                        codes, func=lambda x: -7, y_unit="kN", x_unit="ms", upper=True
                    ),
                    Limit_Pass(
                        codes, func=lambda x: -7, y_unit="kN", x_unit="ms", lower=True
                    ),
                ]

            def calculation(self) -> None:
                self.channel = self.require_channel(
                    self.ctx.code("?{p}FEMR0000??FOZB")
                ).convert_unit("kN")
                self.value = self.limits.get_limit_min_y(self.channel)
                self.rating = self.limits.get_limit_min_rating(
                    self.channel, interpolate=False
                )
                self.color = self.limits.get_limit_min_color(self.channel)

        criterion_hpc36 = sub(Criterion_HPC36)
        criterion_head_a3ms = sub(Criterion_Head_a3ms)
        criterion_neck_fz_tension = sub(Criterion_Neck_Fz_tension)
        criterion_neck_fx_shear = sub(Criterion_Neck_Fx_shear)
        criterion_neck_my_extension = sub(Criterion_Neck_My_extension)
        criterion_chest_deflection = sub(Criterion_Chest_Deflection)
        criterion_chest_vc = sub(Criterion_Chest_VC)
        criterion_femur_compression = sub(Criterion_Femur_Compression)

    criterion_driver = sub(
        Criterion_Driver, at=from_input(P_DRIVER), role=Role.AGGREGATE
    )
    criterion_passenger = sub(
        Criterion_Passenger, role=Role.AGGREGATE, at=from_input(P_PASSENGER)
    )


class UN_Frontal_50kmh_R137(Report[Overall]):
    _name = "UN-R137 | Frontal-Impact against Rigid Wall with 100 % Overlap at 50 km/h"
    _protocol = PROTOCOL_R137_2023
    _protocols = (PROTOCOL_R137_2016, PROTOCOL_R137_2023)
    Criterion_Overall = Overall

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._available_pages = (
            Page_Cover(self),
            self.Page_Rating_Table(self),
            self.Page_Driver_Result_Values_Chart(self),
            self.Page_Driver_Values_Table(self),
            self.Page_Driver_Head_Acceleration(self),
            self.Page_Driver_Neck_Load(self),
            self.Page_Driver_Chest_Deflection(self),
            self.Page_Driver_Femur_Axial_Force(self),
            self.Page_Passenger_Result_Values_Chart(self),
            self.Page_Passenger_Values_Table(self),
            self.Page_Passenger_Head_Acceleration(self),
            self.Page_Passenger_Neck_Load(self),
            self.Page_Passenger_Chest_Deflection(self),
            self.Page_Passenger_Femur_Axial_Force(self),
        )
        self._selected_pages = list(self._available_pages)

    class Page_Rating_Table(Page_Criterion_Rating_Table):
        report: UN_Frontal_50kmh_R137
        name = "Rating"
        title = "Rating"
        cell_text = staticmethod(lambda criterion: f"{criterion.rating:.0f}")

        def __init__(self, report: UN_Frontal_50kmh_R137) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[isomme].criterion_driver,
                    self.report.criterion_overall[isomme].criterion_passenger,
                    self.report.criterion_overall[isomme],
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Driver_Result_Values_Chart(Page_Criterion_Values_Chart):
        report: UN_Frontal_50kmh_R137
        name = "Driver Result Values Chart"
        title = "Driver Result"

        def __init__(self, report: UN_Frontal_50kmh_R137) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_hpc36,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_head_a3ms,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_neck_fz_tension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_neck_fx_shear,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_neck_my_extension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_chest_deflection,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_chest_vc,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_femur_compression,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Driver_Values_Table(Page_Criterion_Values_Table):
        report: UN_Frontal_50kmh_R137
        name = "Driver Values Table"
        title = "Driver Values"

        def __init__(self, report: UN_Frontal_50kmh_R137) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_hpc36,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_head_a3ms,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_neck_fz_tension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_neck_fx_shear,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_neck_my_extension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_chest_deflection,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_chest_vc,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_driver.criterion_femur_compression,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Driver_Head_Acceleration(
        EuroNCAP_Frontal_50kmh.Page_Driver_Head_Acceleration
    ):
        pass

    class Page_Driver_Neck_Load(EuroNCAP_Frontal_50kmh.Page_Driver_Neck_Load):
        pass

    class Page_Driver_Chest_Deflection(
        EuroNCAP_Frontal_50kmh.Page_Driver_Chest_Deflection
    ):
        pass

    class Page_Driver_Femur_Axial_Force(
        EuroNCAP_Frontal_50kmh.Page_Driver_Femur_Axial_Force
    ):
        pass

    class Page_Passenger_Result_Values_Chart(Page_Criterion_Values_Chart):
        report: UN_Frontal_50kmh_R137
        name = "Passenger Result Values Chart"
        title = "Passenger Result"

        def __init__(self, report: UN_Frontal_50kmh_R137) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_hpc36,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_head_a3ms,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_neck_fz_tension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_neck_fx_shear,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_neck_my_extension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_chest_deflection,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_chest_vc,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_femur_compression,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Passenger_Values_Table(Page_Criterion_Values_Table):
        report: UN_Frontal_50kmh_R137
        name: str = "Passenger Values Table"
        title: str = "Passenger Values"

        def __init__(self, report: UN_Frontal_50kmh_R137) -> None:
            super().__init__(report)

            self.criteria = {
                isomme: [
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_hpc36,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_head_a3ms,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_neck_fz_tension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_neck_fx_shear,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_neck_my_extension,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_chest_deflection,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_chest_vc,
                    self.report.criterion_overall[
                        isomme
                    ].criterion_passenger.criterion_femur_compression,
                ]
                for isomme in self.report.isomme_list
            }

    class Page_Passenger_Head_Acceleration(
        EuroNCAP_Frontal_MPDB.Page_Passenger_Head_Acceleration
    ):
        pass

    class Page_Passenger_Neck_Load(EuroNCAP_Frontal_MPDB.Page_Passenger_Neck_Load):
        pass

    class Page_Passenger_Chest_Deflection(
        EuroNCAP_Frontal_MPDB.Page_Passenger_Chest_Deflection
    ):
        pass

    class Page_Passenger_Femur_Axial_Force(
        EuroNCAP_Frontal_MPDB.Page_Passenger_Femur_Axial_Force
    ):
        pass
