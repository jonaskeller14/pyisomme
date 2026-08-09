"""
What a criterion needs to know about *which* measurement it assesses.

:class:`Ctx` replaces the ``p`` threading through ~180 constructors (F15). A child
inherits its parent's context unless its ``sub(..., at=...)`` overrides it, and the
whole chain is resolved **lazily, at the start of** :meth:`Criterion.calculate` — which
is what makes a seating position set *after* construction take effect without rebuilding
anything.

**It is deliberately not an occupant object.** An earlier draft gave it ``position``,
``dummy`` and ``side``; that builds the occupant crash test into the framework, and
pyisomme's reports are not all occupant tests. Under ``euro_ncap/`` and ``iihs/`` alone,
144 criteria take a position and **11 take none** (door opening, the MPDB compatibility
modifiers reading the literal ``M?MBAR0OLC??VEX?``, the structural measurements), and
``Correlation.Criterion_Curve_Correlation`` is built from two ``Channel`` objects with no
position at all. So the core carries only what every report has — the report and the test
— plus a free mapping of **code-template fields**. ``{"p": "1"}`` is what a seating
position puts in it; a barrier, a trolley, a second test object or nothing at all are
equally valid, and none of them require a change here.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from string import Formatter
from types import MappingProxyType
from typing import TYPE_CHECKING, Protocol

from pyisomme.code import CODE_LENGTH, pattern_length
from pyisomme.errors import InvalidCodeError, MissingData
from pyisomme.report.manual import InputSpec, manual

if TYPE_CHECKING:
    from pyisomme.isomme import Isomme
    from pyisomme.report.criterion import Criterion
    from pyisomme.report.report import Report


__all__ = [
    "Ctx",
    "CtxSource",
    "FieldValue",
    "from_input",
    "where",
]

#: What a code-template field may hold: the **characters** it contributes to a channel
#: code. A seating position is one character of ``channel_codes.xml``'s ``Position``
#: element — ``"1"`` (front left) through ``"9"``, then ``"A"``–``"Z"`` for the lettered
#: seats — which is why it is a ``str`` and not an ``int``: ``?A…`` is a valid code and
#: ``?10…`` is not a code at all.
FieldValue = str

_FORMATTER = Formatter()


@dataclass(frozen=True)
class Ctx:
    """The report, the test, and the fields that fill a criterion's code templates."""

    report: Report
    isomme: Isomme
    fields: Mapping[str, FieldValue] = field(default_factory=lambda: MappingProxyType({}))

    def at(self, **fields: FieldValue) -> Ctx:
        """Derive a child context: ``ctx.at(p="3")``, ``ctx.at(object="M")``."""
        return replace(self, fields=MappingProxyType({**dict(self.fields), **fields}))

    def field(self, name: str, *, wanted_for: str | None = None) -> FieldValue:
        """
        One field, or :class:`MissingData` naming it.

        A placeholder with no field is a *missing input* like any other, so it renders
        as a clean ``Status.NA`` that says which field was wanted — never an
        ``AttributeError``, never a silent default.
        """
        try:
            return self.fields[name]
        except KeyError:
            known = f"known fields: {sorted(self.fields)}" if self.fields else "no fields are set"
            wanted = f" of {wanted_for!r}" if wanted_for else ""
            raise MissingData(
                name, message=f"no value for context field {name!r}{wanted} ({known})"
            ) from None

    def code(self, template: str) -> str:
        """
        ``"?{p}NECKUP00??MOY?"`` → ``"?1NECKUP00??MOY?"``, checked for length.

        A template with no placeholder passes through untouched, which is what lets a
        vehicle- or barrier-level criterion need no context at all. The result is an
        fnmatch code *pattern*, so ``?`` wildcards and ``[…]`` character classes are
        preserved and counted as one character each.
        """
        values: dict[str, FieldValue] = {}
        for _, name, _, _ in _FORMATTER.parse(template):
            if name is None:
                continue
            if not name:
                raise InvalidCodeError(
                    f"{template!r}: code templates must name their fields, e.g. '?{{p}}HEAD??00??ACRA'."
                )
            key = name.split(".")[0].split("[")[0]
            values[key] = self.field(key, wanted_for=template)

        code = template.format(**values)
        length = pattern_length(code)
        if length is not None and length != CODE_LENGTH:
            raise InvalidCodeError(
                f"{template!r} resolved to {code!r}, which matches codes of {length} "
                f"characters, but a channel code is {CODE_LENGTH}."
            )
        return code

    def codes(self, *templates: str) -> tuple[str, ...]:
        """:meth:`code` for several templates — the usual leaf spelling."""
        return tuple(self.code(template) for template in templates)


class CtxSource(Protocol):
    """
    What ``sub(..., at=...)`` takes: something that derives a child's context.

    The default (``at=None``) is "inherit the parent's unchanged". Two implementations
    cover every report today — :func:`where` for a field the protocol fixes and
    :func:`from_input` for one the user chooses. Anything else a report needs (a barrier,
    a trolley, the second test object of a correlation run) is another implementation of
    this protocol and requires **no change to the framework**.
    """

    def resolve(self, parent: Ctx, criterion: Criterion) -> Ctx:
        """Derive the criterion's context from its parent's."""
        ...


@dataclass(frozen=True)
class Where:
    """A :class:`CtxSource` of literal fields — see :func:`where`."""

    fields: Mapping[str, FieldValue]

    def resolve(self, parent: Ctx, criterion: Criterion) -> Ctx:
        return parent.at(**dict(self.fields))

    def __repr__(self) -> str:
        return f"where({', '.join(f'{k}={v!r}' for k, v in self.fields.items())})"


def where(**fields: FieldValue) -> CtxSource:
    """
    Fixed fields: ``sub(OLCModifier, at=where(object='M'))``.

    The simplest context source there is, and the one that covers every criterion whose
    context is a constant of the protocol rather than something the user chooses — the
    MPDB trolley, an occupant a protocol pins to one seat.
    """
    return Where(MappingProxyType(dict(fields)))


@dataclass(frozen=True)
class FromInput:
    """A :class:`CtxSource` reading a manual input — see :func:`from_input`."""

    #: The declaration itself (preferred) or its attribute name.
    input_name: str | manual
    field: str = "p"

    def _describe(self) -> str:
        if isinstance(self.input_name, str):
            return repr(self.input_name)
        doc = self.input_name.doc
        return f"the input declared with default {self.input_name.default!r}" + (
            f" ({doc})" if doc else ""
        )

    def resolve(self, parent: Ctx, criterion: Criterion) -> Ctx:
        spec = criterion.find_input_spec(self.input_name)
        if spec is None:
            raise MissingData(str(self.input_name), message=(
                f"no criterion at or above {criterion!r} declares {self._describe()}, "
                f"so field {self.field!r} is unknown."
            ))
        owner = criterion.find_input_owner(self.input_name)
        assert owner is not None  # find_input_spec resolved, so the owner exists
        return parent.at(**{self.field: getattr(owner, spec.name)})

    def reads(self, spec: InputSpec) -> bool:
        """Does this source read ``spec``? Used by ``validate``'s unused-input check."""
        if isinstance(self.input_name, str):
            return self.input_name == spec.name
        return self.input_name is spec.meta

    def __repr__(self) -> str:
        return f"from_input({self._describe()})"


def from_input(input_name: str | manual, *, field: str = "p") -> CtxSource:
    """
    Take a field from a manual input on the nearest ancestor that declares it.

    The general form of a *user-chosen* context, and the reason a position set after
    construction takes effect: the input is read at ``calculate()`` time, not baked in::

        P_DRIVER = manual("1", source="test report", doc="Position of the driver.")

        class Overall(Criterion):
            p_driver: Manual[str, P_DRIVER]
            driver = sub(Occupant, at=from_input(P_DRIVER))

    **Pass the declaration, not its name.** ``manual(...)`` hoisted to a module-level
    constant is referenced by both the annotation and the ``at=``, so the two cannot drift
    apart: a typo or a rename is a `mypy`/`ruff` error instead of a ``Status.NA`` nobody
    reads. The string form (``from_input("p_driver")``) still works and is the escape
    hatch for a declaration in another module.
    """
    return FromInput(input_name, field)
