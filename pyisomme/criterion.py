from pyisomme.isomme import Isomme
from pyisomme.limits import Limits

import numpy as np
import logging


class Criterion:
    name: str = None
    limits: Limits = None

    def __init__(self, report, isomme: Isomme):
        self.report = report
        self.isomme = isomme
        self.channel = {}
        self.value = np.nan
        self.rating = np.nan
        self.limits = Limits(name=report.name, limit_list=[])

    def extend_limit_list(self, limit_list: list):
        self.limits.limit_list.extend(limit_list)
        self.report.limits[self.isomme].limit_list.extend(limit_list)

    def calculate(self):
        try:
            self.calculation()
        except Exception as error_message:
            logging.error(f"{self}:{error_message}")

    def calculation(self):
        pass

    def get_limit_color(self, y_unit, x, x_unit):
        return self.limits.get_limit_color(y=self.value, y_unit=y_unit, x=x, x_unit=x_unit)

    def __repr__(self):
        return f"Criterion({self.name})"
