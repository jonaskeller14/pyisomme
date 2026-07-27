from __future__ import annotations

from pyisomme.isomme import Isomme
from pyisomme.channel import Channel
from pyisomme.limits import Limit, Limits
from pyisomme.errors import MissingData, Status
from pyisomme.report.manual import InputSpec, declared_inputs, settable_names, suggest

import numpy as np
import logging
from abc import abstractmethod
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from pyisomme.report.report import Report


logger = logging.getLogger(__name__)

T = TypeVar("T")

class Undeclared:
    """
    Declared value type of :meth:`Criterion.__setattr__` — never instantiated.

    A type checker consults ``__setattr__`` **only** for names the class does not
    declare; a declared attribute is still checked against its own annotation. So
    an *uninhabited* value type leaves every legitimate assignment alone and turns
    ``criterion.hard_contct = False`` into a static error — where ``Any`` would
    widen every assignment to ``Any`` and undo step 3's static catch.

    ``NoReturn``/``Never`` would do the same job; this exists only so the error
    reads ``variable has type "Undeclared"`` rather than the opaque ``"Never"``.
    The annotation is never evaluated at runtime.
    """


class Criterion:
    name: str | None = None
    limits: Limits
    channel: Channel | None = None
    value: float = np.nan
    rating: float = np.nan
    color: str | tuple | None = None
    status: Status = Status.PENDING
    na_reason: MissingData | None = None
    report: Report
    isomme: Isomme
    p: int

    def __init__(self, report: Report, isomme: Isomme) -> None:
        self.report = report
        self.isomme = isomme
        self.limits = Limits(name=report.name, limit_list=[])

    def __setattr__(self, name: str, value: Undeclared) -> None:
        """
        Reject assignments to names this criterion does not declare (F13).

        A manual input set with a typo used to create a fresh attribute nobody
        reads, so the report calculated with the *default* and produced a clean,
        plausible, wrong score. Here it fails at the moment of assignment.
        Subcriteria are exempt because they are attached dynamically in
        ``__init__``, and ``_``-prefixed names are left to the implementation.

        The ``value: Undeclared`` annotation keeps step 3's *static* catch of
        ``criterion.hard_contct = False`` alive — see :class:`Undeclared`.
        """
        if not name.startswith("_") and not isinstance(value, Criterion):
            cls = type(self)
            settable = settable_names(cls)
            if name not in settable:
                raise AttributeError(
                    f"{cls.__name__} has no settable attribute {name!r}."
                    f"{suggest(name, settable)}"
                )
            spec = declared_inputs(cls).get(name)
            if spec is not None:
                if not spec.accepts(value):
                    raise TypeError(
                        f"{cls.__name__}.{name} expects {spec.type_name()}, "
                        f"got {type(value).__name__} ({value!r})."
                    )
                # Remember that this input was set from outside, so that a
                # derived default never overwrites it (see set_derived_input).
                self.__dict__.setdefault("_inputs_set", set()).add(name)
        object.__setattr__(self, name, value)

    # -- manual inputs ------------------------------------------------------ #

    def get_input_specs(self) -> dict[str, InputSpec]:
        """Every manual input this criterion declares or inherits."""
        return declared_inputs(type(self))

    def input_is_set(self, name: str) -> bool:
        """
        Was this manual input assigned from outside?

        ``False`` while it still holds its declared default *or* a value the
        report derived itself — the distinction a derivation needs, and one that
        comparing against the default cannot make (a user may well set an input
        to exactly its default, and mean it).
        """
        return name in self.__dict__.get("_inputs_set", ())

    def set_derived_input(self, name: str, value: Any) -> None:
        """
        Fill a manual input the user has *not* set — a value the report can work
        out for itself, e.g. the front-passenger position implied by ``p_driver``
        on a right-hand-drive test, or a position read out of the test info.

        A no-op once the user has assigned the input: a derivation refines the
        default, it never overrules a hand-set value. Idempotent, so it may be
        re-run at the top of every ``calculate()`` — pass the value for the
        *current* state rather than only writing in the branch that deviates,
        otherwise an earlier derivation survives the state that produced it.
        """
        specs = declared_inputs(type(self))
        if name not in specs:
            raise AttributeError(
                f"{type(self).__name__} has no manual input {name!r}."
                f"{suggest(name, frozenset(specs))}"
            )
        if self.input_is_set(name):
            return
        setattr(self, name, value)
        self.__dict__["_inputs_set"].discard(name)

    def iter_inputs(self, path: str = "") -> Iterator[tuple[str, Criterion, InputSpec]]:
        """
        Yield ``(path, criterion, spec)`` for every manual input in this subtree.

        ``path`` is the attribute chain from here, e.g.
        ``criterion_driver/criterion_head/hard_contact``.
        """
        for name, spec in sorted(self.get_input_specs().items()):
            yield (f"{path}/{name}" if path else name), self, spec
        for attr, child in self.get_children():
            yield from child.iter_inputs(f"{path}/{attr}" if path else attr)

    def get_children(self) -> list[tuple[str, Criterion]]:
        """``(attribute name, subcriterion)`` pairs, ``dir()``-ordered (step 7 changes this)."""
        children = []
        for attr in sorted(dir(self)):
            if attr.startswith("__"):
                continue
            try:
                child = getattr(self, attr)
            except Exception:  # pragma: no cover - defensive: a property may raise
                continue
            if isinstance(child, Criterion):
                children.append((attr, child))
        return children

    def walk(self) -> Iterator[Criterion]:
        """This criterion and every criterion below it."""
        yield self
        for _, child in self.get_children():
            yield from child.walk()

    def rebuild_child(self, attr: str, *args: Any, **kwargs: Any) -> None:
        """
        Reconstruct the subcriterion at ``attr``, preserving its manual inputs.

        Interim fix for F15: a few criteria are *constructed* with a position
        (``p=``), which is baked into their limits' code patterns, so a position
        set after construction cannot simply be re-read — the subtree has to be
        rebuilt. Step 7's lazy ``Ctx`` removes the need for this.

        The old subtree's limits are dropped from the report-level list (they
        were added there by :meth:`extend_limit_list`) so the rebuild does not
        leave duplicate limit bars in the plots.
        """
        old = getattr(self, attr)
        assert isinstance(old, Criterion), f"{attr} is not a subcriterion"

        # Carried over as ``(path, value, set by the user)`` — a value the old
        # subtree only *derived* must stay derived, or the rebuild would freeze
        # it and the next derivation could no longer correct it.
        overrides = [
            (input_path, getattr(criterion, spec.name), criterion.input_is_set(spec.name))
            for input_path, criterion, spec in old.iter_inputs()
            if criterion.input_is_set(spec.name) or getattr(criterion, spec.name) != spec.default
        ]

        stale = {id(limit) for criterion in old.walk() for limit in criterion.limits.limit_list}
        report_limits = self.report.limits[self.isomme].limit_list
        report_limits[:] = [limit for limit in report_limits if id(limit) not in stale]

        new = type(old)(self.report, self.isomme, *args, **kwargs)
        setattr(self, attr, new)
        for input_path, value, was_set in overrides:
            *parents, name = input_path.split("/")
            target: Criterion = new
            for parent in parents:
                target = getattr(target, parent)
            if was_set:
                setattr(target, name, value)
            else:
                target.set_derived_input(name, value)

    def extend_limit_list(self, limit_list: list[Limit]) -> None:
        self.limits.limit_list.extend(limit_list)
        self.report.limits[self.isomme].limit_list.extend(limit_list)

    def require(self, value: T | None, *what: Any) -> T:
        """
        Return ``value`` unless it is ``None``, in which case raise :class:`MissingData`.

        Use this to turn "an expected input is absent" into a graceful *n/a* outcome
        instead of a downstream ``AttributeError``. ``what`` describes the missing input
        (e.g. a channel code pattern or info label) for the report.
        """
        if value is None:
            raise MissingData(*what)
        return value

    def require_channel(self, *code_patterns: str, isomme: Isomme | None = None, **kwargs: Any) -> Channel:
        """
        Like ``self.isomme.get_channel(...)`` but raise :class:`MissingData` (naming the
        requested patterns) instead of returning ``None`` when no channel is available.

        The requested patterns *are* the criterion's input requirement, so there is no
        separate requirement list to keep in sync.

        ``isomme`` selects a different test than the criterion's own — used by the
        correlation-style reports that compare against a reference test.
        """
        source = self.isomme if isomme is None else isomme
        channel = source.get_channel(*code_patterns, **kwargs)
        if channel is None:
            raise MissingData(*code_patterns)
        return channel

    def require_test_info(self, *labels: str) -> str:
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

    def __repr__(self) -> str:
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
