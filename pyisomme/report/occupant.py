"""
Seating as a context source — the occupant layer, **not** part of the framework.

:class:`~pyisomme.report.ctx.Ctx` deliberately knows nothing about occupants (see there:
11 criteria under ``euro_ncap/`` and ``iihs/`` have no position at all, and the
correlation report is built from channels). Seating is one implementation of
:class:`~pyisomme.report.ctx.CtxSource`, and it lives here, beside the reports that need
it. ``euro_ncap``, ``un``, ``iihs`` and ``us_ncap`` all seat dummies the same way, so it
is one shared module rather than a copy per protocol package::

    class Overall(Criterion):
        p_driver: Manual[int, manual(1, …)]
        p_front_passenger: Manual[int, manual(3, …)]

        driver          = sub(Occupant, at=seat(Seat.DRIVER), name="Driver")
        front_passenger = sub(Occupant, at=seat(Seat.FRONT_PASSENGER), name="Front Passenger")

The resolution reads the ``p_…`` **manual inputs that already exist** on the nearest
ancestor declaring them, so it is not a second source of truth: step 4's public API
(``report.overall(v1).p_driver = 3``, ``get_inputs()``/``set_inputs()``) keeps working
unchanged, and because the context is resolved lazily at the start of ``calculate()``, a
position set after construction now takes effect with nothing to rebuild.

A seat that no ancestor declares is a missing input like any other: a clean
``Status.NA`` naming the input, never an ``AttributeError`` and never a silent default.
For an occupant whose position is fixed by the protocol rather than chosen by the user
(the Far-Side occupant pinned to ``p=1``), use ``at=where(p=1)`` instead — no manual
input, nothing to resolve.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from pyisomme.errors import MissingData
from pyisomme.report.ctx import Ctx, CtxSource

if TYPE_CHECKING:
    from pyisomme.report.criterion import Criterion


__all__ = [
    "Seat",
    "SeatSource",
    "seat",
]


class Seat(Enum):
    """
    A seat in the vehicle, named the way the protocols do.

    The value is the suffix of the manual input holding the position, so
    :attr:`DRIVER` reads ``p_driver``.
    """

    DRIVER = "driver"
    FRONT_PASSENGER = "front_passenger"
    REAR_PASSENGER = "rear_passenger"

    def __str__(self) -> str:
        return self.value.replace("_", " ")


@dataclass(frozen=True)
class SeatSource:
    """A :class:`~pyisomme.report.ctx.CtxSource` resolving a seat — see :func:`seat`."""

    seat: Seat
    #: Code-template field the position is written to. ``"?{p}HEAD??00??ACRA"``.
    field: str = "p"
    #: Manual input holding the position. Defaults to ``p_<seat>``.
    input_name: str | None = None

    @property
    def name(self) -> str:
        return self.input_name or f"p_{self.seat.value}"

    def resolve(self, parent: Ctx, criterion: Criterion) -> Ctx:
        owner = criterion.find_input_owner(self.name)
        if owner is None:
            raise MissingData(self.name, message=(
                f"no criterion at or above {criterion!r} declares the manual input "
                f"{self.name!r}, so the {self.seat} position is unknown."
            ))
        return parent.at(**{self.field: getattr(owner, self.name)})

    def __repr__(self) -> str:
        return f"seat({self.seat.name})"


def seat(which: Seat, *, field: str = "p", input_name: str | None = None) -> CtxSource:
    """
    Resolve a seat to a position read from the tree's ``p_…`` manual inputs.

    :param which: the seat.
    :param field: code-template field to fill, ``"p"`` for a standard channel code.
    :param input_name: manual input to read, if it is not ``p_<seat>``.
    """
    return SeatSource(which, field, input_name)
