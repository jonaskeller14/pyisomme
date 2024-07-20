from __future__ import annotations

from pyisomme.isomme import Isomme
from pyisomme.channel import Channel
from pyisomme.limits import Limit, Limits

import numpy as np
import logging
from abc import abstractmethod


logger = logging.getLogger(__name__)


class Criterion:
    name: str
    limits: Limits = None
    channel: Channel | None = None
    value: float = np.nan
    rating: float = np.nan
    color: str | tuple = None
    status: bool = None

    def __init__(self, report, isomme: Isomme):
        self.report = report
        self.isomme = isomme
        self.limits = Limits(name=report.name, limit_list=[])

    def extend_limit_list(self, limit_list: list[Limit]) -> None:
        self.limits.limit_list.extend(limit_list)
        self.report.limits[self.isomme].limit_list.extend(limit_list)

    def calculate(self) -> None:
        try:
            logger.debug(f"Calculate {self}")
            self.calculation()
            self.status = True
        except Exception as error_message:
            logger.exception(f"{self}:{error_message}")
            self.status = False

    @abstractmethod
    def calculation(self) -> None:
        pass

    def __repr__(self):
        return f"Criterion({self.name})"

    def get_subcriterion(self, *criterion_types: Criterion) -> Criterion | None:
        for criterion_type in criterion_types:
            if isinstance(self, criterion_type):
                return self
            all_subcriteria = [getattr(self, attr) for attr in dir(self) if isinstance(getattr(self, attr), Criterion)]
            for subcriterion in all_subcriteria:
                if isinstance(subcriterion, criterion_type):
                    return subcriterion
                subsubcriterion = subcriterion.get_subcriterion(criterion_type)
                if subsubcriterion is not None:
                    return subsubcriterion
        return None

    def get_subcriteria(self, *criterion_types: Criterion) -> list[Criterion]:
        subcriteria = []
        for criterion_type in criterion_types:
            if isinstance(self, criterion_type):
                subcriteria.append(self)
            all_subcriteria = [getattr(self, attr) for attr in dir(self) if isinstance(getattr(self, attr), Criterion)]
            for subcriterion in all_subcriteria:
                if isinstance(subcriterion, criterion_type):
                    subcriteria.append(subcriterion)
                subcriteria += subcriterion.get_subcriteria(criterion_type)
        return subcriteria
