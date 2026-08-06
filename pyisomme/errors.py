from __future__ import annotations

import enum


__all__ = [
    "PyisommeError",
    "MalformedFileError",
    "InvalidCodeError",
    "UnitError",
    "MissingData",
    "UnsupportedCalculationError",
    "Status",
]


class PyisommeError(Exception):
    """Base class for all pyisomme-specific errors."""


class MalformedFileError(PyisommeError):
    """
    An input file (.mme/.chn/.001/...) is structurally broken or unparseable.

    This is a hard failure: the data cannot be trusted, so callers should fail loudly
    rather than silently produce a wrong channel.
    """


class InvalidCodeError(PyisommeError, ValueError):
    """
    A valid 16-character ISO-MME channel code was required but not provided.

    Subclasses :class:`ValueError` so existing ``except ValueError`` sites keep working.
    """


class UnitError(PyisommeError):
    """Incompatible, unknown, or missing physical units."""


class MissingData(PyisommeError):
    """
    An expected input was absent (e.g. a required channel or test-info field).

    This represents genuinely incomplete test data, **not** a bug. Report code catches it
    and renders the affected criterion as "n/a", naming exactly what was missing.

    The requested identifiers are kept in :attr:`what` so the report can report *which*
    input was missing without any separately-declared requirement list.
    """

    def __init__(self, *what: object, message: str | None = None):
        self.what: tuple[object, ...] = what
        if message is not None:
            text = message
        elif what:
            text = "missing required input data: " + ", ".join(f"'{w}'" for w in what)
        else:
            text = "required input data is missing"
        super().__init__(text)


class UnsupportedCalculationError(PyisommeError, NotImplementedError):
    """A derived quantity is not defined for the supplied input configuration.

    Channel providers treat this as an unavailable synthesis path and may try another
    provider or return no channel. Direct callers still receive an explicit error.
    """


class Status(enum.Enum):
    """
    Outcome of a criterion (or any computed result).

    - :attr:`PENDING`  — not calculated yet (default before ``calculate()`` runs).
    - :attr:`OK`       — value computed successfully.
    - :attr:`NA`       — a required input was absent (expected; render as "n/a").
    - :attr:`ERROR`    — an unexpected failure/bug (surface loudly).
    """

    PENDING = "pending"
    OK = "ok"
    NA = "n/a"
    ERROR = "error"

    @property
    def is_ok(self) -> bool:
        return self is Status.OK

    @property
    def is_na(self) -> bool:
        return self is Status.NA

    @property
    def is_error(self) -> bool:
        return self is Status.ERROR

    def __str__(self) -> str:
        return self.value
