from pyisomme.report.page import Page_Cover
from pyisomme.report.report import Report
from pyisomme.report.criterion import Criterion
from pyisomme.report.us_ncap.calculate import *
from pyisomme.report.us_ncap.limits import *

import logging
import numpy as np


logger = logging.getLogger(__name__)


class USNCAP_Frontal_56kmh(Report):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pages = [
            Page_Cover(self),
        ]

    class Criterion_Overall(Criterion):
        name = "Overall"
        p_driver: int = 1
        p_passenger: int = 3

        def __init__(self, report, isomme):
            super().__init__(report, isomme)

            p_driver = isomme.get_test_info("Driver position object 1")
            if p_driver is not None:
                self.p_driver = int(p_driver)
            self.p_passenger = 1 if self.p_driver != 1 else self.p_passenger

            self.criterion_driver = self.Criterion_Driver(report, isomme, p=self.p_driver)
            self.criterion_passenger = self.Criterion_Passenger(report, isomme, p=self.p_passenger)

        def calculation(self) -> None:
            self.criterion_driver.calculate()
            self.criterion_passenger.calculate()

            self.rating = np.mean([
                self.criterion_driver.rating,
                self.criterion_passenger.rating,
            ])  # relative risk (RR)

        class Criterion_Driver(Criterion):
            name = "Driver"

            def __init__(self, report, isomme, p):
                super().__init__(report, isomme)

                self.p = p

                self.criterion_head = self.Criterion_Head(report, isomme, p=self.p)
                self.criterion_chest = self.Criterion_Chest(report, isomme, p=self.p)
                self.criterion_femur = self.Criterion_Femur(report, isomme, p=self.p)
                self.criterion_neck = self.Criterion_Neck(report, isomme, p=self.p)

            def calculation(self) -> None:
                self.criterion_head.calculate()
                self.criterion_chest.calculate()
                self.criterion_femur.calculate()
                self.criterion_neck.calculate()

                self.value = 1 - (1 - self.criterion_head.value) * (1 - self.criterion_chest.value) * (1 - self.criterion_femur.value) * (1 - self.criterion_neck.value)
                self.rating = self.value / 0.15  # relative risk (RR)

            class Criterion_Head(Criterion):
                name = "Head"

                def __init__(self, report, isomme, p):
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
                    self.channel = calculate_p_head_hic15_ais_3plus(self.isomme.get_channel(f"?{self.p}HEAD0000??ACRA", f"?{self.p}HEADCG00??ACRA"), dummy="H3")
                    self.value = np.max(self.channel.get_data())
                    self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=True)  # stars

            class Criterion_Chest(Criterion):
                pass

            class Criterion_Femur(Criterion):
                pass

            class Criterion_Neck(Criterion):
                pass