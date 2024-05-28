import logging
import numpy as np

from pyisomme.report import Report
from pyisomme.criterion import Criterion
from pyisomme.limits import Limit


logger = logging.getLogger(__name__)


class EuroNCAP_Frontal_50kmh(Report):
    name = "Euro NCAP | Frontal-Impact against MPDB with 50 % Overlap at 50/50 km/h"

    def __init__(self, isomme_list: list, title: str) -> None:
        super().__init__(isomme_list, title)
        self.pages = []

    class Criterion_Master(Criterion):
        name: str = "Master"
        p_driver: int = 1
        p_passenger: int = 3

        def __init__(self, report, isomme):
            super().__init__(report, isomme)

            p_driver = isomme.get_test_info("Driver position object 1")
            if p_driver is not None:
                self.p_driver = p_driver

            self.p_passenger = 1 if p_driver != 1 else self.p_passenger

            self.criterion_driver = self.Criterion_Driver(report, isomme)
            self.criterion_passenger = self.Criterion_Passenger(report, isomme)

        def calculation(self):
            logger.info("Calculate Driver")
            self.criterion_driver.calculate()
            logger.info("Calculate Passenger")
            self.criterion_passenger.calculate()

            self.rating = np.sum([
                np.min([self.criterion_driver.criterion_head_neck.rating, self.criterion_passenger.criterion_head_neck.rating]),
                #TODO
            ])

            # TODO: compatibilry
            # TODO: Modifier

        class Criterion_Driver(Criterion):
            class Criterion_Head_Neck(Criterion):
                class Criterion_Head(Criterion):
                    pass
                class Criterion_Neck(Criterion):
                    pass

            class Criterion_Chest_Abdomen(Criterion):
                class Criterion_Chest(Criterion):
                    pass
                class Criterion_Abdomen(Criterion):
                    pass



        class Criterion_Passenger(Criterion):
            class Criterion_Head_Neck(Criterion):
                class Criterion_Head(Criterion):
                    pass
                class Criterion_Neck(Criterion):
                    class Criterion_Fx_Shear(Criterion):
                        def __init__(self, report, isomme, p):
                            super().__init__(report, isomme)

                            self.p = p

                            self.extend_limit_list([
                                Limit([f"1{self.p}NECKUP00??FOX?"], func=lambda x: np.interp(x, [0, 25, 35, 45], [1.9, 1.2, 1.2, 1.1], left=1.9, right=1.1), y_unit="kN", x_unit="ms", name="4 Points", color="green", upper=True),
                                # TODO
                            ])




