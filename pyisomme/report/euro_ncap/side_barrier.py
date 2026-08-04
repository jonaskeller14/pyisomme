from __future__ import annotations

from pyisomme.isomme import Isomme
from pyisomme.report.page import Page_Cover
from pyisomme.report.report import Report
from pyisomme.report.criterion import Criterion
from pyisomme.report.manual import Manual, manual
from pyisomme.report.euro_ncap.frontal_50kmh import Criterion_HIC_15, Criterion_Head_a3ms
from pyisomme.report.euro_ncap.side_pole import EuroNCAP_Side_Pole
from pyisomme.report.euro_ncap.side_pole import Overall as Overall_Side_Pole
from pyisomme.report.euro_ncap.limits import Limit_G, Limit_P, Limit_C, Limit_M, Limit_A, Limit_W

import logging
import numpy as np
from typing import Any


logger = logging.getLogger(__name__)


class Overall(Criterion):
    name = "Overall"
    max_rating = 16.
    source = "§5"
    p: Manual[int, manual(1, source="test report", doc=(
        "Channel-code position of the struck-side occupant — the only occupant "
        "§5 assesses. Defaults to the 'Driver position object 1' test-info field "
        "when the test carries it."))]

    positioned_children = Overall_Side_Pole.positioned_children

    def __init__(self, report: Report, isomme: Isomme) -> None:
        super().__init__(report, isomme)

        p = isomme.get_test_info("Driver position object 1")
        if p is not None:
            self.set_derived_input("p", int(p))

        self.criterion_head = self.Criterion_Head(self.report, self.isomme, p=self.p)
        self.criterion_chest = self.Criterion_Chest(self.report, self.isomme, p=self.p)
        self.criterion_abdomen = self.Criterion_Abdomen(self.report, self.isomme, p=self.p)
        self.criterion_pelvis = self.Criterion_Pelvis(self.report, self.isomme, p=self.p)

        # §5.2.4 and §5.2.5 apply to side barrier and pole alike; §5.2.3's head
        # protection device penalty is pole-only and deliberately absent here.
        self.criterion_incorrect_airbag_deployment = Overall_Side_Pole.Criterion_IncorrectAirbagDeployment(report, isomme)
        self.criterion_door_opening_during_impact = Overall_Side_Pole.Criterion_DoorOpeningDuringImpact(report, isomme)

    def sync_position(self) -> None:
        """Same interim F15 rebuild as the pole report — see its ``sync_position``."""
        for attr in self.positioned_children:
            if getattr(self, attr).p != self.p:
                logger.info(f"{self}: rebuilding {attr} for position {self.p}")
                self.rebuild_child(attr, p=self.p)

    def calculation(self) -> None:
        self.sync_position()

        self.criterion_head.calculate()
        self.criterion_chest.calculate()
        self.criterion_abdomen.calculate()
        self.criterion_pelvis.calculate()

        self.rating = np.sum([
            self.criterion_head.rating,
            self.criterion_chest.rating,
            self.criterion_abdomen.rating,
            self.criterion_pelvis.rating
        ])
        self.rating = float(np.interp(self.rating, [0, 16], [0, 16], left=0, right=np.nan))

        # Modifier
        self.criterion_incorrect_airbag_deployment.calculate()
        self.criterion_door_opening_during_impact.calculate()

        self.rating += np.sum([
            self.criterion_incorrect_airbag_deployment.rating,
            self.criterion_door_opening_during_impact.rating,
        ])

        # A modifier must not drive the load case below zero.
        self.rating = float(np.max([0., self.rating]))

    class Criterion_Head(Criterion):
        name = "Head"
        max_rating = 4.
        #: Unlike the pole (§5.1.1.2) the barrier test scores HIC15 and the 3 ms
        #: exceedance on the same sliding scale as the frontal tests.
        source = "§5.1.1.1"

        def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
            super().__init__(report, isomme)

            self.p = p

            self.criterion_hic_15 = self.Criterion_HIC_15(self.report, self.isomme, p=self.p)
            self.criterion_head_acceleration = self.Criterion_Head_a3ms(self.report, self.isomme, p=self.p)

        def calculation(self) -> None:
            self.criterion_hic_15.calculate()
            self.criterion_head_acceleration.calculate()

            self.rating = np.min([
                self.criterion_hic_15.rating,
                self.criterion_head_acceleration.rating,
            ])

        class Criterion_HIC_15(Criterion_HIC_15):  # noqa: F811 - the nested name deliberately shadows the import
            pass

        class Criterion_Head_a3ms(Criterion_Head_a3ms):  # noqa: F811
            pass

    class Criterion_Chest(Criterion):
        name = "Chest"
        max_rating = 4.
        source = "§5.1.2"

        def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
            super().__init__(report, isomme)

            self.p = p

            self.criterion_chest_lateral_compression = self.Criterion_Chest_Lateral_Compression(self.report, self.isomme, p=self.p)
            self.criterion_chest_lateral_vc = self.Criterion_Chest_Lateral_VC(self.report, self.isomme, p=self.p)
            self.criterion_shoulder_lateral_force = self.Criterion_Shoulder_Lateral_Force(self.report, self.isomme, p=self.p)

        def calculation(self) -> None:
            self.criterion_chest_lateral_compression.calculate()
            self.criterion_chest_lateral_vc.calculate()
            self.criterion_shoulder_lateral_force.calculate()

            self.rating = np.min([
                self.criterion_chest_lateral_compression.rating,
                self.criterion_chest_lateral_vc.rating,
                self.criterion_shoulder_lateral_force.rating,
            ])

        class Criterion_Chest_Lateral_Compression(Criterion):
            #: §5.1.2 caps the barrier test at 50 mm; the pole test at 55 mm. Only
            #: the capping row differs from EuroNCAP_Side_Pole.
            name = "Chest Lateral Compression"

            def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                super().__init__(report, isomme)

                self.p = p

                self.extend_limit_list([
                    Limit_C([f"?{self.p}TRRI??0[0123]??DSY?"], func=lambda x: -50.000, y_unit="mm", upper=True),
                    Limit_P([f"?{self.p}TRRI??0[0123]??DSY?"], func=lambda x: -50.000, y_unit="mm"),
                    Limit_W([f"?{self.p}TRRI??0[0123]??DSY?"], func=lambda x: -42.667, y_unit="mm", upper=True),
                    Limit_M([f"?{self.p}TRRI??0[0123]??DSY?"], func=lambda x: -35.333, y_unit="mm", upper=True),
                    Limit_A([f"?{self.p}TRRI??0[0123]??DSY?"], func=lambda x: -28.000, y_unit="mm", upper=True),
                    Limit_G([f"?{self.p}TRRI??0[0123]??DSY?"], func=lambda x: -28.000, y_unit="mm", lower=True),
                ])

            def calculation(self) -> None:
                self.channel = self.require_channel(f"?{self.p}TRRI??00??DSYC").convert_unit("mm")
                self.value = np.min(self.channel.get_data())
                self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=True)
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Chest_Lateral_VC(Overall_Side_Pole.Criterion_Chest.Criterion_Chest_Lateral_VC):
            pass

        class Criterion_Shoulder_Lateral_Force(Overall_Side_Pole.Criterion_Chest.Criterion_Shoulder_Lateral_Force):
            pass

    class Criterion_Abdomen(Criterion):
        name = "Abdomen"
        max_rating = 4.
        source = "§5.1.3"

        def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
            super().__init__(report, isomme)

            self.p = p

            self.criterion_abdomen_lateral_compression = self.Criterion_Abdomen_Lateral_Compression(self.report, self.isomme, p=self.p)
            self.criterion_abdomen_lateral_vc = self.Criterion_Abdomen_Lateral_VC(self.report, self.isomme, p=self.p)

        def calculation(self) -> None:
            self.criterion_abdomen_lateral_compression.calculate()
            self.criterion_abdomen_lateral_vc.calculate()

            self.rating = np.min([
                self.criterion_abdomen_lateral_compression.rating,
                self.criterion_abdomen_lateral_vc.rating
            ])

        class Criterion_Abdomen_Lateral_Compression(Overall_Side_Pole.Criterion_Abdomen.Criterion_Abdomen_Lateral_Compression):
            pass

        class Criterion_Abdomen_Lateral_VC(Overall_Side_Pole.Criterion_Abdomen.Criterion_Abdomen_Lateral_VC):
            pass

    class Criterion_Pelvis(Criterion):
        name = "Pelvis"
        max_rating = 4.
        source = "§5.1.4"

        def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
            super().__init__(report, isomme)

            self.p = p

            self.criterion_pubic_symphysis_force = self.Criterion_Pubic_Symphysis_Force(self.report, self.isomme, p=self.p)

        def calculation(self) -> None:
            self.criterion_pubic_symphysis_force.calculate()

            self.rating = self.criterion_pubic_symphysis_force.rating

        class Criterion_Pubic_Symphysis_Force(Overall_Side_Pole.Criterion_Pelvis.Criterion_Pubic_Symphysis_Force):
            pass


class EuroNCAP_Side_Barrier(Report[Overall]):
    name = "Euro NCAP | Barrier Side Impact (AE-MDB) at 60 km/h"
    protocol = "9.3"
    protocols = {
        "9.3": "Version 9.3 (05.12.2023) [references/Euro-NCAP/euro-ncap-assessment-protocol-aop-v93.pdf]"
    }

    #: The report's criterion tree, defined at module level (see `Overall`).
    Criterion_Overall = Overall

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.pages = [
            Page_Cover(self),

            self.Page_Values_Chart(self),
            self.Page_Rating_Table(self),
            self.Page_Values_Table(self),
            self.Page_Head_Acceleration(self),
            self.Page_Shoulder_Lateral_Force(self),
            self.Page_Chest_Lateral_Compression(self),
            self.Page_Chest_Lateral_VC(self),
            self.Page_Abdomen_Lateral_Compression(self),
            self.Page_Abdomen_Lateral_VC(self),
            self.Page_Pubic_Symphysis_Force(self),
        ]

    class Page_Values_Chart(EuroNCAP_Side_Pole.Page_Values_Chart):
        pass

    class Page_Values_Table(EuroNCAP_Side_Pole.Page_Values_Table):
        pass

    class Page_Rating_Table(EuroNCAP_Side_Pole.Page_Rating_Table):
        pass

    class Page_Head_Acceleration(EuroNCAP_Side_Pole.Page_Head_Acceleration):
        pass

    class Page_Shoulder_Lateral_Force (EuroNCAP_Side_Pole.Page_Shoulder_Lateral_Force):
        pass

    class Page_Chest_Lateral_Compression(EuroNCAP_Side_Pole.Page_Chest_Lateral_Compression):
        pass

    class Page_Chest_Lateral_VC(EuroNCAP_Side_Pole.Page_Chest_Lateral_VC):
        pass

    class Page_Abdomen_Lateral_Compression(EuroNCAP_Side_Pole.Page_Abdomen_Lateral_Compression):
        pass

    class Page_Abdomen_Lateral_VC(EuroNCAP_Side_Pole.Page_Abdomen_Lateral_VC):
        pass

    class Page_Pubic_Symphysis_Force(EuroNCAP_Side_Pole.Page_Pubic_Symphysis_Force):
        pass
