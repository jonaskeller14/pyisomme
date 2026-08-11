from __future__ import annotations

import inspect
import re
import sys
from typing import TYPE_CHECKING
from collections.abc import Iterator

from pyisomme.report.ctx import FromInput
from pyisomme.report.validate.issue import Issue, IssueSeverity

if TYPE_CHECKING:
    from pyisomme.report.criterion import Criterion
    from pyisomme.report.manual import InputSpec


def _module_source(cls: type) -> str | None:
    module = sys.modules.get(cls.__module__)
    if module is None:
        return None
    try:
        return inspect.getsource(module)
    except (OSError, TypeError):  # pragma: no cover - module without a source file
        return None


def _read_by_a_context_source(criterion: Criterion, spec: InputSpec) -> bool:
    """
    Is ``spec`` what some ``sub(X, at=from_input(...))`` below ``criterion`` reads?

    Since step 8 this is how a seating position reaches the criteria that use it: the
    framework reads the input through the context source, not through any line of the
    report, so such an input is read just as surely as ``self.hard_contact`` is.

    Asked of the *tree* rather than of the module text, which is both exact and the only
    thing that still works now that a context source names the declaration **object**
    (``from_input(P_DRIVER)``) instead of repeating its name in a string.
    """
    return any(
        isinstance(node.ctx_source, FromInput) and node.ctx_source.reads(spec)
        for _, node in criterion.walk()
    )


def check_unused_input(path: str, criterion: Criterion) -> Iterator[Issue]:
    """
    Every declared manual input is read somewhere.

    An input nobody reads is a promise the report does not keep: the user sets it,
    the assignment is accepted, and the score comes out as if they had not (F13's
    typo failure mode one level up). The search is over the whole module that
    declares it, because an input is often read from the criterion *above* it — plus
    :func:`_read_by_a_context_source` for the ones the framework reads.
    """
    for name, spec in sorted(criterion.get_input_specs().items()):
        if spec.owner is not type(criterion):
            continue  # reported once, at the class that declares it
        if _read_by_a_context_source(criterion, spec):
            continue
        source = _module_source(spec.owner)
        if source is None:
            continue
        if not re.search(rf"\.{re.escape(name)}\b", source):
            yield Issue(
                "unused_input",
                IssueSeverity.WARNING,
                path,
                f"manual input {name!r} is declared by "
                f"{spec.owner.__qualname__} but never read in "
                f"{spec.owner.__module__}.",
            )
