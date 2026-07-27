"""
US-NCAP frontal impact at 56 km/h — **unfinished stub, not usable yet.**

What exists: the driver head criterion (HIC15 → AIS3+ risk) with its star limits.
What is missing: ``Criterion_Passenger`` is referenced but never defined, and the
driver's chest/femur/neck criteria are empty placeholders. Constructing the report
therefore raises :class:`NotImplementedError` rather than a confusing
``AttributeError`` deep inside the criterion tree.

The report is deliberately absent from ``REPORTS`` in ``pyisomme/__main__.py`` and
is out of scope for the report refactor (plan Step 2, review Appendix A5).
"""

from __future__ import annotations
from pyisomme.calculate import calculate_p_head_hic15_ais_3plus
from pyisomme.isomme import Isomme
from pyisomme.report.report import Report
from pyisomme.report.criterion import Criterion
from pyisomme.report.us_ncap.limits import Limit_1, Limit_2, Limit_3, Limit_4, Limit_5

import logging
import numpy as np
from typing import Any


logger = logging.getLogger(__name__)


class USNCAP_Frontal_56kmh(Report["USNCAP_Frontal_56kmh.Criterion_Overall"]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError(
            "USNCAP_Frontal_56kmh is an unfinished stub: Criterion_Passenger is not "
            "defined and the driver's chest/femur/neck criteria are empty. See the "
            "module docstring."
        )

    class Criterion_Overall(Criterion):
        name = "Overall"
        p_driver: int = 1
        p_passenger: int = 3

        def __init__(self, report: Report, isomme: Isomme) -> None:
            super().__init__(report, isomme)

            p_driver = isomme.get_test_info("Driver position object 1")
            if p_driver is not None:
                self.p_driver = int(p_driver)
            self.p_passenger = 1 if self.p_driver != 1 else self.p_passenger

            self.criterion_driver = self.Criterion_Driver(report, isomme, p=self.p_driver)
            # Criterion_Passenger is referenced but never defined -- one of the two reasons
            # this report is a stub (see module docstring). Kept visible rather than deleted.
            self.criterion_passenger = self.Criterion_Passenger(report, isomme, p=self.p_passenger)  # type: ignore[attr-defined]

        def calculation(self) -> None:
            self.criterion_driver.calculate()
            self.criterion_passenger.calculate()

            self.rating = np.mean([
                self.criterion_driver.rating,
                self.criterion_passenger.rating,
            ])  # relative risk (RR)

        class Criterion_Driver(Criterion):
            name = "Driver"

            def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                super().__init__(report, isomme)

                self.p = p

                self.criterion_head = self.Criterion_Head(report, isomme, p=self.p)
                # Chest/femur/neck are empty `pass` placeholders: they have no calculation()
                # and do not accept `p`. The other reason this report is a stub.
                self.criterion_chest = self.Criterion_Chest(report, isomme, p=self.p)  # type: ignore[abstract, call-arg]
                self.criterion_femur = self.Criterion_Femur(report, isomme, p=self.p)  # type: ignore[abstract, call-arg]
                self.criterion_neck = self.Criterion_Neck(report, isomme, p=self.p)  # type: ignore[abstract, call-arg]

            def calculation(self) -> None:
                self.criterion_head.calculate()
                self.criterion_chest.calculate()
                self.criterion_femur.calculate()
                self.criterion_neck.calculate()

                self.value = 1 - (1 - self.criterion_head.value) * (1 - self.criterion_chest.value) * (1 - self.criterion_femur.value) * (1 - self.criterion_neck.value)
                self.rating = self.value / 0.15  # relative risk (RR)

            class Criterion_Head(Criterion):
                name = "Head"

                def __init__(self, report: Report, isomme: Isomme, p: int) -> None:
                    super().__init__(report, isomme)

                    self.p = p

                    self.extend_limit_list([
                        Limit_5(["????????????????"], func=lambda x: 0.67 * 0.15, upper=True),
                        Limit_4(["????????????????"], func=lambda x: 1.00 * 0.15, upper=True),
                        Limit_3(["????????????????"], func=lambda x: 1.33 * 0.15, upper=True),
                        Limit_2(["????????????????"], func=lambda x: 2.67 * 0.15, upper=True),
                        Limit_1(["????????????????"], func=lambda x: 2.67 * 0.15, lower=True),
                    ])

                def calculation(self) -> None:
                    self.channel = calculate_p_head_hic15_ais_3plus(self.require_channel(f"?{self.p}HEAD0000??ACRA", f"?{self.p}HEADCG00??ACRA"), dummy="H3")
                    self.value = np.max(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=True)  # stars

            class Criterion_Chest(Criterion):
                pass

            class Criterion_Femur(Criterion):
                pass

            class Criterion_Neck(Criterion):
                pass
