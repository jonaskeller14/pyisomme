from pyisomme.isomme import Isomme
from pyisomme.limits import Limit, Limits

import numpy as np
import logging
from abc import abstractmethod


logger = logging.getLogger(__name__)


class Criterion:
    name: str = None
    limits: Limits = None

    def __init__(self, report, isomme: Isomme):
        self.report = report
        self.isomme = isomme
        self.channel = None
        self.value = np.nan
        self.rating = np.nan
        self.limits = Limits(name=report.name, limit_list=[])

    def extend_limit_list(self, limit_list: list[Limit]) -> None:
        self.limits.limit_list.extend(limit_list)
        self.report.limits[self.isomme].limit_list.extend(limit_list)

    def calculate(self) -> None:
        try:
            logger.debug(f"Calculate {self}")
            self.calculation()
        except Exception as error_message:
            logger.exception(f"{self}:{error_message}")

    @abstractmethod
    def calculation(self) -> None:
        pass

    def __repr__(self):
        return f"Criterion({self.name})"
