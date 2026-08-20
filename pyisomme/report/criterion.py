from __future__ import annotations

import itertools
import logging
from abc import abstractmethod
from collections.abc import Iterator, Sequence
from enum import Enum
from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast, overload

import numpy as np

from pyisomme.channel import Channel
from pyisomme.errors import MissingData, Status
from pyisomme.isomme import Isomme
from pyisomme.limit import Limit
from pyisomme.limits import Limits
from pyisomme.report.ctx import Ctx, CtxSource
from pyisomme.report.manual import (
    InputSpec,
    declared_inputs,
    manual,
    settable_names,
    suggest,
)

if TYPE_CHECKING:
    from pyisomme.report.report import Report


logger = logging.getLogger(__name__)

T = TypeVar("T")
C = TypeVar("C", bound="Criterion")

_ORDER = itertools.count()


class Role(Enum):
    RESULT = "result"  # measures something itself
    AGGREGATE = "aggregate"  # measures nothing itself; derives from its children's
    MODIFIER = "modifier"  # an adjustment applied *on top of* the aggregated score

    def __str__(self) -> str:
        return self.value


#: The roles that make up a node's headline score — everything except the modifiers,
#: which are added on top of it. The default of the aggregation helpers.
SCORING_ROLES = (Role.RESULT, Role.AGGREGATE)


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


class sub(Generic[C]):
    """
    A declared subcriterion — the one place a child is wired.
    :param cls: the child's class. Inner classes stay nested and must be defined
        *above* the ``sub()`` line that references them.
    :param name: display name, overriding the child class's own ``name``.
    :param at: a :class:`~pyisomme.report.ctx.CtxSource` deriving the child's context.
        ``None`` inherits the parent's unchanged.
    :param role: see :class:`Role`. ``None`` keeps whatever the child class declares.
    """

    attr: str

    def __init__(
        self,
        cls: type[C],
        *,
        name: str | None = None,
        at: CtxSource | None = None,
        role: Role | None = None,
    ) -> None:
        self.cls = cls
        self.display_name = name
        self.at = at
        self.role = role
        self.order = next(_ORDER)

    def __set_name__(self, owner: type[Criterion], attr: str) -> None:
        self.attr = attr
        # A fresh dict per owner, seeded from the base classes': a subclass must be able
        # to add or replace a child without mutating the class it inherits from.
        inherited = getattr(owner, "_declared_children", {})
        previous = inherited.get(attr)
        if previous is not None:
            # Overriding an inherited child keeps its place in the protocol. A subclass
            # that only refines one region should not reorder the whole tree.
            self.order = previous.order
        owner._declared_children = {**inherited, attr: self}

    def build(self, parent: Criterion) -> C:
        """Construct the child and attach it to ``parent``."""
        child = self.cls(parent.report, parent.isomme)
        child._parent = parent
        child._ctx_source = self.at
        if self.display_name is not None:
            child.name = self.display_name
        if self.role is not None:
            child.role = self.role
        return child

    @overload
    def __get__(self, obj: None, owner: type[Criterion]) -> sub[C]: ...

    @overload
    def __get__(self, obj: Criterion, owner: type[Criterion]) -> C: ...

    def __get__(self, obj: Criterion | None, owner: type[Criterion]) -> sub[C] | C:
        if obj is None:
            return self
        try:
            return cast("C", obj._children[self.attr])
        except (
            KeyError
        ):  # pragma: no cover - a subclass that never ran Criterion.__init__
            raise AttributeError(
                f"{type(obj).__name__}.{self.attr} was never built — did "
                f"{type(obj).__name__}.__init__ forget to call super().__init__()?"
            ) from None

    def __repr__(self) -> str:
        return f"sub({self.cls.__name__})"


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
    role: Role = Role.RESULT
    skip_missing: str | None = None  # --> NaN-tolerant aggregation

    # Validation:
    source: str | None = None
    max_rating: float | None = None
    aggregation: str | None = None
    validate_ignore: dict[str, str] = {}

    #: ``{attribute: sub}`` for every child declared with :class:`sub`, filled by
    #: ``sub.__set_name__``. Never mutated in place — see there.
    _declared_children: dict[str, sub] = {}
    #: The framework-owned children, ``{attribute: criterion}``. Annotated but not
    #: assigned: a class-level ``{}`` would be shared by every criterion in the process.
    #: Always reach it through :meth:`_child_map`, which creates it on first use.
    _children: dict[str, Criterion]
    _parent: Criterion | None = None
    #: This criterion's ``at=``, or ``None`` to inherit the parent's context unchanged.
    _ctx_source: CtxSource | None = None

    def __init__(self, report: Report, isomme: Isomme) -> None:
        self.report = report
        self.isomme = isomme
        self.limits = Limits(name=report.name, limit_list=[])

        # Tree is built, so it is complete and mutable before calculate()
        children = self._child_map()
        for spec in sorted(
            type(self)._declared_children.values(), key=lambda spec: spec.order
        ):
            children[spec.attr] = spec.build(self)

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
        for node_path, criterion in self.walk(path):
            for name, spec in sorted(criterion.get_input_specs().items()):
                yield (f"{node_path}/{name}" if node_path else name), criterion, spec

    def _child_map(self) -> dict[str, Criterion]:
        """The framework-owned children, ``{attribute: criterion}`` in insertion order."""
        children: dict[str, Criterion] = self.__dict__.setdefault("_children", {})
        return children

    def get_children(self) -> list[tuple[str, Criterion]]:
        """
        ``(attribute name, subcriterion)`` pairs in **protocol order**.

        Framework-owned children first — those declared with :class:`sub` (declaration
        order) and those attached with :meth:`add_child` (insertion order) — then the
        ones a not-yet-migrated ``__init__`` assigned as plain attributes, in the order
        it assigned them. This is what replaces the ``dir()`` walk (F6, A11, A12): both
        halves now come out in the order the protocol lists them rather than
        alphabetically, so :meth:`walk`, ``print_results()`` and ``describe()`` follow
        the document.

        The trailing ``dir()`` sweep is a safety net for a criterion held on the class
        rather than the instance; it finds nothing in any report today.
        """
        children = list(self._child_map().items())
        seen = {attr for attr, _ in children}

        for attr, value in list(vars(self).items()):  # legacy: assigned in __init__
            if attr.startswith("_") or attr in seen or not isinstance(value, Criterion):
                continue
            children.append((attr, value))
            seen.add(attr)

        for attr in sorted(dir(type(self))):  # safety net, see docstring
            # Read off the *class*: a property would have to be evaluated (and `parent`
            # would then look like a child), a `sub` is already covered above.
            value = getattr(type(self), attr, None)
            if attr.startswith("_") or attr in seen or not isinstance(value, Criterion):
                continue
            children.append((attr, value))
            seen.add(attr)

        return children

    def add_child(self, name: str, criterion: Criterion) -> None:
        """
        Attach a child the class does not declare — the escape hatch for a tree whose
        shape depends on the data (the correlation report's per-channel list, F6/A12).

        Dynamically added children are calculated by :meth:`calculate` exactly like
        declared ones, and appear after them in :meth:`get_children`.
        """
        criterion._parent = self
        self._child_map()[name] = criterion

    @property
    def parent(self) -> Criterion | None:
        return self._parent

    def ancestors(self) -> Iterator[Criterion]:
        """This criterion's parent, its parent, … up to the root. Nearest first."""
        node = self._parent
        while node is not None:
            yield node
            node = node._parent

    def find_input_owner(self, key: str | manual) -> Criterion | None:
        """
        The nearest criterion at or above this one that declares the manual input.

        ``key`` is either the attribute *name* or the :class:`~pyisomme.report.manual.manual`
        **object** the declaration carries. The object form is what lets a ``sub(...,
        at=from_input(P_DRIVER))`` reference the declaration itself instead of repeating
        its name in a string, so a typo or a rename is a static error rather than a
        ``Status.NA`` at calculate time.

        Matching on the object is by **identity**: ``manual`` is a frozen dataclass, so
        two unrelated inputs that happen to share a default and a doc compare equal.
        """
        for node in itertools.chain([self], self.ancestors()):
            specs = node.get_input_specs()
            if isinstance(key, str):
                if key in specs:
                    return node
            elif any(spec.meta is key for spec in specs.values()):
                return node
        return None

    def find_input_spec(self, key: str | manual) -> InputSpec | None:
        """The :class:`InputSpec` :meth:`find_input_owner` would resolve ``key`` to."""
        owner = self.find_input_owner(key)
        if owner is None:
            return None
        specs = owner.get_input_specs()
        if isinstance(key, str):
            return specs.get(key)
        return next((spec for spec in specs.values() if spec.meta is key), None)

    # -- context ------------------------------------------------------------ #

    @property
    def ctx_source(self) -> CtxSource | None:
        """This criterion's ``at=``, or ``None`` when it inherits its parent's context."""
        return self._ctx_source

    @property
    def ctx(self) -> Ctx:
        """
        Which measurement this criterion assesses — see :class:`~pyisomme.report.ctx.Ctx`.

        Resolved on demand and never cached: the root builds a bare context, every other
        node inherits its parent's and applies its own ``at=``. That laziness *is* the
        F15 fix — a seating position set after construction is honoured by the criteria
        and by their limits with nothing to rebuild, because nothing was baked in at
        construction time.
        """
        parent = self._parent
        base = parent.ctx if parent is not None else Ctx(self.report, self.isomme)
        return (
            base if self._ctx_source is None else self._ctx_source.resolve(base, self)
        )

    def code(self, template: str) -> str:
        """``self.ctx.code(template)`` — the spelling a criterion body uses."""
        return self.ctx.code(template)

    def walk(self, path: str = "") -> Iterator[tuple[str, Criterion]]:
        """
        ``(path, criterion)`` for this criterion and every criterion below it,
        depth-first, parent before children.

        ``path`` is the attribute chain from here — the same spelling
        :meth:`iter_inputs` uses, so an input path is always its criterion's path
        plus the input name. The root yields ``path`` itself, ``""`` by default.
        """
        yield path, self
        for attr, child in self.get_children():
            yield from child.walk(f"{path}/{attr}" if path else attr)

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

    def require_channel(
        self, *code_patterns: str, isomme: Isomme | None = None, **kwargs: Any
    ) -> Channel:
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

    def extend_limit_list(self, limit_list: list[Limit]) -> None:
        self.limits.limit_list.extend(limit_list)
        self.report.limits[self.isomme].limit_list.extend(limit_list)

    def define_limits(self) -> list[Limit]:
        """
        This criterion's limit rows, built from its :attr:`ctx`.
        Override it instead of calling :meth:`extend_limit_list` from ``__init__``: the
        framework calls it at the start of every :meth:`calculate` (see
        :meth:`apply_limits`)
        """
        return []

    def apply_limits(self) -> None:
        """
        Rebuild this criterion's limits from :meth:`define_limits`, replacing the
        previous rows in both the criterion's own list and the report-level one the
        plots read.

        A no-op unless the class overrides :meth:`define_limits`, so a not-yet-migrated
        criterion that builds its rows in ``__init__`` keeps them.
        """
        if type(self).define_limits is Criterion.define_limits:
            return
        stale = {id(limit) for limit in self.limits.limit_list}
        if stale:
            report_limits = self.report.limits[self.isomme].limit_list
            report_limits[:] = [
                limit for limit in report_limits if id(limit) not in stale
            ]
            self.limits.limit_list.clear()
        self.extend_limit_list(self.define_limits())

    def build_limits(self) -> None:
        for _, criterion in self.walk():
            criterion.apply_limits()

    def prepare(self) -> None:
        """Run before this criterion's children are calculated. Does nothing by default."""

    def calculate(self) -> None:
        try:
            logger.debug(f"Calculate {self}")
            self.prepare()
            self.apply_limits()
            for name, child in list(self._child_map().items()):
                logger.debug(f"Calculate {self}.{name}")
                child.calculate()
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

    # -- aggregation -------------------------------------------------------- #

    def children_by_role(self, *roles: Role) -> list[Criterion]:
        """
        This criterion's children with any of ``roles``, in protocol order.

        Defaults to the scoring roles (``RESULT`` + ``AGGREGATE``), i.e. everything the
        headline aggregation is made of, excluding the modifiers that are added on top.
        """
        wanted = roles or SCORING_ROLES
        return [child for _, child in self.get_children() if child.role in wanted]

    def ratings_of_children(self, *roles: Role) -> list[float]:
        return [child.rating for child in self.children_by_role(*roles)]

    def _empty(self, what: str, roles: Sequence[Role]) -> float:
        wanted = ", ".join(str(role) for role in (roles or SCORING_ROLES))
        logger.warning(f"{self}: {what} over no children (roles: {wanted}) — nan.")
        return float(np.nan)

    def min_of_children(self, *roles: Role) -> float:
        """Worst child rating — the usual body-region rule. NaN propagates."""
        ratings = self.ratings_of_children(*roles)
        return float(np.min(ratings)) if ratings else self._empty("min", roles)

    def max_of_children(self, *roles: Role) -> float:
        """Best child rating. NaN propagates."""
        ratings = self.ratings_of_children(*roles)
        return float(np.max(ratings)) if ratings else self._empty("max", roles)

    def sum_of_children(self, *roles: Role) -> float:
        """Child ratings added up — the usual occupant rule. NaN propagates."""
        return float(np.sum(self.ratings_of_children(*roles)))

    def mean_of_children(self, *roles: Role, skip_missing: str | None = None) -> float:
        """Mean child rating. NaN propagates **unless** ``skip_missing`` is given."""
        ratings = self.ratings_of_children(*roles)
        if not ratings:
            return self._empty("mean", roles)
        if skip_missing is None:
            return float(np.mean(ratings))
        present = [rating for rating in ratings if not np.isnan(rating)]
        if len(present) != len(ratings):
            self.skip_missing = skip_missing
            logger.info(
                f"{self}: {len(ratings) - len(present)} of {len(ratings)} children "
                f"missing, skipped ({skip_missing})."
            )
        return float(np.mean(present)) if present else float(np.nan)

    def modifiers_sum(self) -> float:
        return self.sum_of_children(Role.MODIFIER)

    def __repr__(self) -> str:
        return f"Criterion({self.name if self.name is not None else self.__class__.__name__})"

    def get_subcriterion(self, *criterion_types: type[Criterion]) -> Criterion | None:
        """
        The first criterion in this subtree (this one included) of any of
        ``criterion_types``, in protocol order — ``None`` if there is none.
        """
        return next(iter(self.get_subcriteria(*criterion_types)), None)

    def get_subcriteria(self, *criterion_types: type[Criterion]) -> list[Criterion]:
        """
        Every criterion in this subtree (this one included) of any of
        ``criterion_types``, depth-first in protocol order.

        Uses the ordered children list rather than ``dir()`` (F6, A11), so the result
        follows the protocol instead of the alphabet.
        """
        return [
            criterion
            for _, criterion in self.walk()
            if isinstance(criterion, criterion_types)
        ]
