from __future__ import annotations

import inspect
import re
import sys
from typing import TYPE_CHECKING
from collections.abc import Iterator

from pyisomme.report.validate.issue import Issue, IssueSeverity

if TYPE_CHECKING:
    from pyisomme.report.criterion import Criterion


def _module_source(cls: type) -> str | None:
    module = sys.modules.get(cls.__module__)
    if module is None:
        return None
    try:
        return inspect.getsource(module)
    except (OSError, TypeError):  # pragma: no cover - module without a source file
        return None


def check_unused_input(path: str, criterion: Criterion) -> Iterator[Issue]:
    """
    Every declared manual input is read somewhere.

    An input nobody reads is a promise the report does not keep: the user sets it,
    the assignment is accepted, and the score comes out as if they had not (F13's
    typo failure mode one level up). The search is over the whole module that
    declares it, because an input is often read from the criterion *above* it.
    """
    for name, spec in sorted(criterion.get_input_specs().items()):
        if spec.owner is not type(criterion):
            continue  # reported once, at the class that declares it
        source = _module_source(spec.owner)
        if source is None:
            continue
        if not re.search(rf"\.{re.escape(name)}\b", source):
            yield Issue("unused_input", IssueSeverity.WARNING, path,
                        f"manual input {name!r} is declared by "
                        f"{spec.owner.__qualname__} but never read in "
                        f"{spec.owner.__module__}.")
