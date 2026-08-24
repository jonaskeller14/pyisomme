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

import logging
from typing import Any

import numpy as np

from pyisomme.calculate import calculate_p_head_hic15_ais_3plus
from pyisomme.isomme import Isomme
from pyisomme.limit import Limit
from pyisomme.report.criterion import Criterion, Role, sub
from pyisomme.report.criterion_result import CriterionResult
from pyisomme.report.ctx import from_input
from pyisomme.report.manual import Manual, manual
from pyisomme.report.report import Report
from pyisomme.report.us_ncap.limits import Limit_1, Limit_2, Limit_3, Limit_4, Limit_5

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


class Overall(Criterion):
    name = "Overall"
    p_driver: Manual[str, P_DRIVER]
    p_passenger: Manual[str, P_PASSENGER]

    def __init__(self, report: Report[Any], isomme: Isomme) -> None:
        super().__init__(report, isomme)
        # Also at construction: the pages read the positions when the report is built.
        self.prepare()

    def prepare(self) -> None:
        """Take the positions from the test info before the occupants read them."""
        p_driver = self.isomme.get_test_info("Driver position object 1")
        if p_driver is not None:
            self.set_derived_input("p_driver", str(p_driver).strip())
        self.set_derived_input("p_passenger", "1" if self.p_driver != "1" else "3")

    def calculation(self) -> CriterionResult:
        # Criterion_Passenger is referenced but never defined -- one of the two reasons
        # this report is a stub (see module docstring). Kept visible rather than deleted;
        # once it exists it is wired beside the driver with
        #     criterion_passenger = sub(Criterion_Passenger, role=Role.AGGREGATE,
        #                               at=from_input(P_PASSENGER))
        rating = self.mean_of_children()  # relative risk (RR)
        return CriterionResult(
            channel=None,
            value=rating,
            rating=rating,
            color=None,
        )

    class Criterion_Driver(Criterion):
        name = "Driver"
        role = Role.AGGREGATE

        def calculation(self) -> CriterionResult:
            value = 1 - (1 - Criterion.value_of(self.criterion_head)) * (
                1 - Criterion.value_of(self.criterion_chest)
            ) * (1 - Criterion.value_of(self.criterion_femur)) * (
                1 - Criterion.value_of(self.criterion_neck)
            )
            rating = value / 0.15  # relative risk (RR)
            return CriterionResult(
                channel=None,
                value=value,
                rating=rating,
                color=None,
            )

        class Criterion_Head(Criterion):
            name = "Head"

            def define_limits(self) -> list[Limit]:
                return [
                    Limit_5(
                        ("????????????????",), func=lambda x: 0.67 * 0.15, upper=True
                    ),
                    Limit_4(
                        ("????????????????",), func=lambda x: 1.00 * 0.15, upper=True
                    ),
                    Limit_3(
                        ("????????????????",), func=lambda x: 1.33 * 0.15, upper=True
                    ),
                    Limit_2(
                        ("????????????????",), func=lambda x: 2.67 * 0.15, upper=True
                    ),
                    Limit_1(
                        ("????????????????",), func=lambda x: 2.67 * 0.15, lower=True
                    ),
                ]

            def calculation(self) -> CriterionResult:
                channel = calculate_p_head_hic15_ais_3plus(
                    self.require_channel(
                        self.ctx.code("?{p}HEAD0000??ACRA"),
                        self.ctx.code("?{p}HEADCG00??ACRA"),
                    ),
                    dummy="H3",
                )
                value = np.max(channel.get_data())
                rating = self.limits.get_limit_min_rating(
                    channel, interpolate=True
                )  # stars
                return CriterionResult(
                    channel=channel,
                    value=value,
                    rating=rating,
                    color=None,
                )

        # Chest/femur/neck are empty `pass` placeholders: they have no calculation().
        # The other reason this report is a stub.
        class Criterion_Chest(Criterion):
            pass

        class Criterion_Femur(Criterion):
            pass

        class Criterion_Neck(Criterion):
            pass

        criterion_head = sub(Criterion_Head)
        criterion_chest = sub(Criterion_Chest)  # type: ignore[type-abstract]
        criterion_femur = sub(Criterion_Femur)  # type: ignore[type-abstract]
        criterion_neck = sub(Criterion_Neck)  # type: ignore[type-abstract]

    criterion_driver = sub(
        Criterion_Driver, at=from_input(P_DRIVER), role=Role.AGGREGATE
    )


class USNCAP_Frontal_56kmh(Report[Overall]):
    Criterion_Overall = Overall

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError(
            "USNCAP_Frontal_56kmh is an unfinished stub: Criterion_Passenger is not "
            "defined and the driver's chest/femur/neck criteria are empty. See the "
            "module docstring."
        )
