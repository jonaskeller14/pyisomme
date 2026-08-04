from __future__ import annotations

import logging
import sys
import typing
from dataclasses import dataclass
from difflib import get_close_matches
# ``Manual[float, manual(0.0, unit="mm")]`` reads as ``float`` to mypy/pyright.
# Imported under an alias rather than assigned (``Manual = Annotated``) because
# only the import form is recognised as a type alias by mypy.
from typing import Annotated as Manual
from typing import Any, Union, get_args, get_origin

import numpy as np


__all__ = [
    "InputSpec",
    "Manual",
    "declared_inputs",
    "manual",
    "settable_names",
    "suggest",
]

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class manual:
    """
    Metadata of a manual input, carried in a :data:`Manual` annotation.

    **Compared by identity, not by value** (``eq=False``). Two declarations that happen
    to read the same — every report's driver position is ``manual("1", source="test
    report", …)`` — are still two different declarations, and
    ``sub(..., at=from_input(P_DRIVER))`` has to resolve to *this* module's. Value
    equality would also make them interchangeable to ``typing.Annotated``, which caches
    ``Annotated[str, meta]`` on ``(type, meta)``: the second module to be imported would
    silently get the first one's annotation object.

    :param default: value used when nobody sets the input. Installed as the
        class attribute, so it must be immutable.
    :param unit: unit the value is expected in, e.g. ``"mm"``. Documentation
        only — no conversion happens.
    :param doc: one line telling the user what to fill in.
    :param source: where the value comes from — ``"video"``, ``"measurement"``,
        ``"test report"``, ``"judgement"``.
    """

    default: Any
    unit: str | None = None
    doc: str | None = None
    source: str | None = None


@dataclass(frozen=True)
class InputSpec:
    """A :class:`manual` declaration resolved against the class that owns it."""

    name: str
    type: Any
    owner: type
    #: The very :class:`manual` object the annotation carries. Kept so a declaration
    #: can be referenced *by object* instead of by name — see
    #: :meth:`Criterion.find_input_owner` and :func:`pyisomme.report.ctx.from_input`.
    #: Compared with ``is``, never ``==``: ``manual`` is a frozen dataclass, so two
    #: unrelated inputs with the same default and doc compare equal.
    meta: manual
    default: Any
    unit: str | None = None
    doc: str | None = None
    source: str | None = None

    def accepts(self, value: Any) -> bool:
        return _accepts(value, self.type)

    def type_name(self) -> str:
        return _type_name(self.type)


# --------------------------------------------------------------------------- #
# type checking
# --------------------------------------------------------------------------- #

def _accepts(value: Any, declared: Any) -> bool:
    """
    Is ``value`` acceptable for a field declared as ``declared``?

    Deliberately narrow: ``bool`` is *not* an ``int`` here, because the whole
    point is to reject ``submarining = "yes"``-style mistakes, and Python's
    ``isinstance(True, int)`` would wave through ``forward_excursion = True``.
    An ``int`` **is** accepted for a ``float`` field (the numeric tower).
    """
    if declared is Any or declared is None:
        return True
    origin = get_origin(declared)
    if origin is Union:
        return any(_accepts(value, arg) for arg in get_args(declared))
    if declared is type(None):
        return value is None
    if declared is bool:
        return isinstance(value, (bool, np.bool_))
    if declared is int:
        return isinstance(value, (int, np.integer)) and not isinstance(value, (bool, np.bool_))
    if declared is float:
        return (isinstance(value, (int, float, np.integer, np.floating))
                and not isinstance(value, (bool, np.bool_)))
    try:
        return isinstance(value, declared)
    except TypeError:  # pragma: no cover - exotic typing construct
        return True


def _type_name(declared: Any) -> str:
    if get_origin(declared) is Union:
        return " | ".join(_type_name(arg) for arg in get_args(declared))
    if declared is type(None):
        return "None"
    return getattr(declared, "__name__", str(declared))


# --------------------------------------------------------------------------- #
# declaration discovery
# --------------------------------------------------------------------------- #

#: Per-class cache. Keyed by the class object; classes live for the process.
_SPECS: dict[type, dict[str, InputSpec]] = {}
_SETTABLE: dict[type, frozenset[str]] = {}


def _resolve_annotation(owner: type, annotation: Any) -> tuple[Any, manual] | None:
    """Return ``(declared_type, manual)`` if ``annotation`` is a ``Manual[...]``."""
    if isinstance(annotation, str):
        # `from __future__ import annotations` makes every annotation a string, and
        # evaluating all of them would be wasteful, so filter first. Both spellings
        # count: the inline `Manual[bool, manual(False, …)]` and the
        # `Manual[str, P_DRIVER]` that references a hoisted declaration.
        if "manual(" not in annotation and "Manual[" not in annotation:
            return None
        module = sys.modules.get(owner.__module__)
        globalns = dict(vars(typing))
        globalns.update(getattr(module, "__dict__", {}))
        try:
            annotation = eval(annotation, globalns)  # noqa: S307 - our own annotations
        except Exception as error:
            logger.warning(f"{owner.__qualname__}: cannot resolve manual input annotation "
                           f"{annotation!r}: {error}")
            return None
    for item in getattr(annotation, "__metadata__", ()):
        if isinstance(item, manual):
            return get_args(annotation)[0], item
    return None


def declared_inputs(cls: type) -> dict[str, InputSpec]:
    """
    Every manual input ``cls`` declares or inherits, ``{name: spec}``.

    The first call for a class also installs each default as a class attribute
    on the class that declared it, so ``self.hard_contact`` reads work without
    any per-instance setup. Results are cached; annotations are only ever
    evaluated once.
    """
    cached = _SPECS.get(cls)
    if cached is not None:
        return cached

    specs: dict[str, InputSpec] = {}
    for owner in reversed(cls.__mro__):  # base classes first, so a subclass wins
        for name, annotation in vars(owner).get("__annotations__", {}).items():
            resolved = _resolve_annotation(owner, annotation)
            if resolved is None:
                continue
            declared_type, meta = resolved
            specs[name] = InputSpec(
                name=name,
                type=declared_type,
                owner=owner,
                meta=meta,
                default=meta.default,
                unit=meta.unit,
                doc=meta.doc,
                source=meta.source,
            )
            if name not in vars(owner):
                setattr(owner, name, meta.default)

    _SPECS[cls] = specs
    return specs


def settable_names(cls: type) -> frozenset[str]:
    """
    Attribute names an instance of ``cls`` may be assigned.

    Everything *declared* at class level counts — annotated framework fields
    (``value``, ``rating``, …), plain class attributes and manual inputs alike.
    A name that appears nowhere in the class body is, by construction, a typo.
    """
    cached = _SETTABLE.get(cls)
    if cached is not None:
        return cached

    names: set[str] = set(declared_inputs(cls))
    for owner in cls.__mro__:
        names.update(vars(owner))
        names.update(vars(owner).get("__annotations__", {}))
    names = {name for name in names if not name.startswith("__")}

    _SETTABLE[cls] = frozenset(names)
    return _SETTABLE[cls]


def suggest(name: str, candidates: frozenset[str]) -> str:
    """`` Did you mean 'submarining'?`` — or an empty string when nothing is close."""
    matches = get_close_matches(name, sorted(candidates), n=1, cutoff=0.7)
    return f" Did you mean {matches[0]!r}?" if matches else ""
