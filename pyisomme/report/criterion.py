from __future__ import annotations

from pyisomme.isomme import Isomme
from pyisomme.channel import Channel
from pyisomme.limits import Limit, Limits
from pyisomme.errors import MissingData, Status

import numpy as np
import logging
from abc import abstractmethod


logger = logging.getLogger(__name__)


class Criterion:
    name: str | None = None
    limits: Limits
    channel: Channel | None = None
    value: float = np.nan
    rating: float = np.nan
    color: str | tuple | None = None
    status: Status = Status.PENDING
    na_reason: MissingData | None = None

    def __init__(self, report, isomme: Isomme):
        self.report = report
        self.isomme = isomme
        self.limits = Limits(name=report.name, limit_list=[])

    def extend_limit_list(self, limit_list: list[Limit]) -> None:
        self.limits.limit_list.extend(limit_list)
        self.report.limits[self.isomme].limit_list.extend(limit_list)

    def require(self, value, *what):
        """
        Return ``value`` unless it is ``None``, in which case raise :class:`MissingData`.

        Use this to turn "an expected input is absent" into a graceful *n/a* outcome
        instead of a downstream ``AttributeError``. ``what`` describes the missing input
        (e.g. a channel code pattern or info label) for the report.
        """
        if value is None:
            raise MissingData(*what)
        return value

    def require_channel(self, *code_patterns: str, **kwargs) -> Channel:
        """
        Like ``self.isomme.get_channel(...)`` but raise :class:`MissingData` (naming the
        requested patterns) instead of returning ``None`` when no channel is available.

        The requested patterns *are* the criterion's input requirement, so there is no
        separate requirement list to keep in sync.
        """
        channel = self.isomme.get_channel(*code_patterns, **kwargs)
        if channel is None:
            raise MissingData(*code_patterns)
        return channel

    def require_test_info(self, *labels: str):
        """Fetch a test-info field, raising :class:`MissingData` if it is absent."""
        value = self.isomme.get_test_info(*labels)
        if value is None:
            raise MissingData(*labels)
        return value

    def calculate(self) -> None:
        try:
            logger.debug(f"Calculate {self}")
            self.calculation()
            self.status = Status.OK
        except MissingData as missing:
            # Expected: this test simply does not contain the required input.
            self.status = Status.NA
            self.na_reason = missing
            logger.info(f"{self}: n/a ({missing})")
        except Exception as error_message:
            # Unexpected: a real bug or corrupt input. Surface it loudly.
            self.status = Status.ERROR
            logger.exception(f"{self}:{error_message}")

    @abstractmethod
    def calculation(self) -> None:
        pass

    def __repr__(self):
        return f"Criterion({self.name if self.name is not None else self.__class__.__name__})"

    def get_subcriterion(self, *criterion_types: type[Criterion]) -> Criterion | None:
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

    def get_subcriteria(self, *criterion_types: type[Criterion]) -> list[Criterion]:
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
