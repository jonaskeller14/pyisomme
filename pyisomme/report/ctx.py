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
— plus a free mapping of **code-template fields**. ``{"p": 1}`` is what the occupant
helper in :mod:`pyisomme.report.occupant` puts in it; a barrier, a trolley, a second test
object or nothing at all are equally valid, and none of them require a change here.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from string import Formatter
from types import MappingProxyType
from typing import TYPE_CHECKING, Protocol, Union

from pyisomme.code import CODE_LENGTH, pattern_length
from pyisomme.errors import InvalidCodeError, MissingData

if TYPE_CHECKING:
    from pyisomme.isomme import Isomme
    from pyisomme.report.criterion import Criterion
    from pyisomme.report.report import Report


__all__ = [
    "Ctx",
    "CtxSource",
    "FieldValue",
    "where",
]

#: What a code-template field may hold. A position is an ``int`` (``"?{p}HEAD…"``), a
#: test object a ``str`` (``"{object}?MBAR0OLC??VEX?"``).
FieldValue = Union[str, int]

_NO_FIELDS: Mapping[str, FieldValue] = MappingProxyType({})
_FORMATTER = Formatter()


@dataclass(frozen=True)
class Ctx:
    """The report, the test, and the fields that fill a criterion's code templates."""

    report: Report
    isomme: Isomme
    fields: Mapping[str, FieldValue] = _NO_FIELDS  # fields, e.g. ``{"p": 1}``

    def at(self, **fields: FieldValue) -> Ctx:
        """Derive a child context: ``ctx.at(p=3)``, ``ctx.at(object="M")``."""
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

    def codes(self, *templates: str) -> list[str]:
        """:meth:`code` for several templates — the usual leaf spelling."""
        return [self.code(template) for template in templates]


class CtxSource(Protocol):
    """
    What ``sub(..., at=...)`` takes: something that derives a child's context.

    The default (``at=None``) is "inherit the parent's unchanged". Occupant seating is
    *one* implementation, living in :mod:`pyisomme.report.occupant` beside the reports
    that need it — not in :mod:`pyisomme.report.criterion`. Anything else a report needs
    (a barrier, a trolley, the second test object of a correlation run) is another
    implementation of this protocol and requires **no change to the framework**.
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
    MPDB trolley, the Far-Side occupant that is pinned to ``p=1``.
    """
    return Where(MappingProxyType(dict(fields)))
