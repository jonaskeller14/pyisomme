from __future__ import annotations

from pyisomme import Unit, g0
from pyisomme.isomme import Isomme
from pyisomme.report.page import Page_Cover, Page_Criterion_Values_Chart, Page_Criterion_Values_Table, Page_Plot_nxn
from pyisomme.report.report import Report
from pyisomme.report.criterion import Criterion
from pyisomme.report.un.limits import Limit_Fail, Limit_Pass
from pyisomme.report.euro_ncap.side_pole import EuroNCAP_Side_Pole

import logging
import numpy as np
from typing import Any


logger = logging.getLogger(__name__)


class Overall(Criterion):
    name = "Overall"
    # TODO(input): make this a manual input as in EuroNCAP_Side_Pole/Side_Barrier —
    #   declare `p: Manual[int, manual(1, ...)]`, derive it from the
    #   "Driver position object 1" test info, and add the sync_position()/
    #   rebuild_child() pair, so the struck-side occupant is not pinned to position 1.
    p: int = 1

    def __init__(self, report: Report, isomme: Isomme) -> None:
        super().__init__(report, isomme)

        p = isomme.get_test_info("Driver position object 1")
        if p is not None:
            self.p = int(p)

        self.criterion_dummy = self.Criterion_Dummy(report, isomme, p=self.p)

    def calculation(self) -> None:
        self.criterion_dummy.calculate()

        self.rating = self.criterion_dummy.rating

    class Criterion_Dummy(Criterion):
        name = "Dummy"

        def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
            super().__init__(report, isomme)

            self.p = p

            self.criterion_hic_36 = self.Criterion_HIC_36(report, isomme, p=self.p)
            self.criterion_shoulder_lateral_force = self.Criterion_Shoulder_Lateral_Force(report, isomme, p=self.p)
            self.criterion_chest_resultant_compression = self.Criterion_Chest_Resultant_Compression(report, isomme, p=self.p)
            self.criterion_abdomen_resultant_compression = self.Criterion_Abdomen_Resultant_Compression(report, isomme, p=self.p)
            self.criterion_spine_t12_a3ms = self.Criterion_Spine_T12_a3ms(report, isomme, p=self.p)
            self.criterion_pubic_symphysis_force = self.Criterion_Pubic_Symphysis_Force(report, isomme, p=self.p)


        def calculation(self) -> None:
            self.criterion_hic_36.calculate()
            self.criterion_shoulder_lateral_force.calculate()
            self.criterion_chest_resultant_compression.calculate()
            self.criterion_abdomen_resultant_compression.calculate()
            self.criterion_spine_t12_a3ms.calculate()
            self.criterion_pubic_symphysis_force.calculate()

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

            def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                super().__init__(report, isomme)

                self.p = p

                self.extend_limit_list([
                    Limit_Pass([f"?{self.p}HICR0036??00RX", f"?{self.p}HICRCG36??00RX"], func=lambda x: 1000, y_unit=1, upper=True),
                    Limit_Fail([f"?{self.p}HICR0036??00RX", f"?{self.p}HICRCG36??00RX"], func=lambda x: 1000, y_unit=1, lower=True),
                ])

            def calculation(self) -> None:
                self.channel = self.require_channel(f"?{self.p}HICR0036??00RX", f"?{self.p}HICRCG36??00RX")
                self.value = self.channel.get_data()[0]
                self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Shoulder_Lateral_Force(Criterion):
            name = "Shoulder Lateral Force"

            def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                super().__init__(report, isomme)

                self.p = p

                self.extend_limit_list([
                    Limit_Fail([f"?{self.p}SHLD0000??FOY?", f"?{self.p}SHLDLE00??FOY?", f"?{self.p}SHLDRI00??FOY?"], func=lambda x: -3, y_unit="kN", upper=True),
                    Limit_Pass([f"?{self.p}SHLD0000??FOY?", f"?{self.p}SHLDLE00??FOY?", f"?{self.p}SHLDRI00??FOY?"], func=lambda x: -3, y_unit="kN", lower=True),
                    Limit_Pass([f"?{self.p}SHLD0000??FOY?", f"?{self.p}SHLDLE00??FOY?", f"?{self.p}SHLDRI00??FOY?"], func=lambda x: 3, y_unit="kN", upper=True),
                    Limit_Fail([f"?{self.p}SHLD0000??FOY?", f"?{self.p}SHLDLE00??FOY?", f"?{self.p}SHLDRI00??FOY?"], func=lambda x: 3., y_unit="kN", lower=True),
                ])

            def calculation(self) -> None:
                self.channel = self.require_channel(f"?{self.p}SHLD0000??FOYB").convert_unit("kN")
                self.value = self.channel.get_data()[np.argmax(np.abs(self.channel.get_data()))]
                self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Chest_Resultant_Compression(Criterion):
            name = "Chest Resultant Compression"

            def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                super().__init__(report, isomme)

                self.p = p

                self.extend_limit_list([
                    Limit_Fail([f"?{self.p}TRRI??0[0123]??DSR?"], func=lambda x: -55, y_unit="mm", upper=True),
                    Limit_Pass([f"?{self.p}TRRI??0[0123]??DSR?"], func=lambda x: -55, y_unit="mm", lower=True),
                ])

            def calculation(self) -> None:
                self.channel = self.require_channel(f"?{self.p}TRRI??00??DSRB").convert_unit("mm")
                self.value = np.min(self.channel.get_data())
                self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Abdomen_Resultant_Compression(Criterion):
            name = "Abdomen Resultant Compression"

            def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                super().__init__(report, isomme)

                self.p = p

                self.extend_limit_list([
                    Limit_Fail([f"?{self.p}ABRI??0[012]??DSR?"], func=lambda x: -65, y_unit="mm", upper=True),
                    Limit_Pass([f"?{self.p}ABRI??0[012]??DSR?"], func=lambda x: -65, y_unit="mm", lower=True),
                ])

            def calculation(self) -> None:
                self.channel = self.require_channel(f"?{self.p}ABRI??00??DSRB").convert_unit("mm")
                self.value = np.min(self.channel.get_data())
                self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Spine_T12_a3ms(Criterion):
            name = "Spine T12 Acceleration a3ms"

            def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                super().__init__(report, isomme)

                self.p = p

                self.extend_limit_list([
                    Limit_Pass([f"1{self.p}THSP123C??ACR?"], func=lambda x: 75, y_unit=Unit(g0), upper=True),
                    Limit_Fail([f"1{self.p}THSP123C??ACR?"], func=lambda x: 75, y_unit=Unit(g0), lower=True),
                ])

            def calculation(self) -> None:
                self.channel = self.require_channel(f"1{self.p}THSP123C??ACRX").convert_unit(Unit(g0))
                self.value = np.max(self.channel.get_data())
                self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
                self.color = self.limits.get_limit_min_color(self.channel)

        class Criterion_Pubic_Symphysis_Force(Criterion):
            name = "Pubic Symphysis Force"

            def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                super().__init__(report, isomme)

                self.p = p

                self.extend_limit_list([
                    Limit_Fail([f"?{self.p}PUBC0000??FOY?"], func=lambda x: -3.36, y_unit="kN", upper=True),
                    Limit_Pass([f"?{self.p}PUBC0000??FOY?"], func=lambda x: -3.36, y_unit="kN", lower=True),
                    Limit_Pass([f"?{self.p}PUBC0000??FOY?"], func=lambda x: 3.36, y_unit="kN", upper=True),
                    Limit_Fail([f"?{self.p}PUBC0000??FOY?"], func=lambda x: 3.36, y_unit="kN", lower=True),
                ])

            def calculation(self) -> None:
                self.channel = self.require_channel(f"?{self.p}PUBC0000??FOYB").convert_unit("kN")
                self.value = self.channel.get_data()[np.argmax(np.abs(self.channel.get_data()))]
                self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=True)
                self.color = self.limits.get_limit_min_color(self.channel)


class UN_Side_Pole_R135(Report[Overall]):
    name = "UN-R135 | Pole Side Impact at 32 km/h"
    protocol = "05.02.2016"
    protocols = {
        "05.02.2016": "Revision 1 (05.02.2016) [references/UN-R135/B04.hcu736002y3cij636z760633yex36763590547033.pdf]"
    }

    #: The report's criterion tree, defined at module level (see `Overall`).
    Criterion_Overall = Overall

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.pages = [
            Page_Cover(self),

            self.Page_Values_Chart(self),
            self.Page_Values_Table(self),
            self.Page_Head_Acceleration(self),
            self.Page_Shoulder_Lateral_Force(self),
            self.Page_Chest_Absolute_Compression(self),
            self.Page_Abdomen_Resultant_Compression(self),
            self.Page_Spine_T12_Acceleration(self),
            self.Page_Pubic_Symphysis_Force(self),
        ]

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
