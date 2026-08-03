from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any
from collections.abc import Sequence

from pyisomme.limit import Limit
from pyisomme.report.validate import SAMPLE_X, blocks, derived_max_rating

if TYPE_CHECKING:
    from pyisomme.report.criterion import Criterion
    from pyisomme.report.report import Report


#: Rendered where a criterion declares nothing.
NONE = "—"


def _num(value: Any) -> str:
    """A float spelled the same way on every platform and run."""
    if value is None:
        return NONE
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        if math.isinf(value):
            return "inf" if value > 0 else "-inf"
    if isinstance(value, (int, float)):
        return f"{value:.10g}"
    return str(value)


def _cell(text: Any) -> str:
    """Escape a value so it cannot break out of a Markdown table cell."""
    return str(text).replace("|", "\\|").replace("\n", " ")


def _table(header: Sequence[str], rows: Sequence[Sequence[Any]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |",
             "| " + " | ".join("---" for _ in header) + " |"]
    lines += ["| " + " | ".join(_cell(cell) for cell in row) + " |" for row in rows]
    return lines


def _threshold(limit: Limit) -> str:
    """
    The limit's y value: one number for a constant, the sampled curve otherwise.

    Most rows are ``lambda x: 500.0``. The corridors (IIHS neck, the MPDB
    modifiers) are not, and collapsing those to ``f(0)`` would hide exactly the
    part of them a review needs to see.
    """
    try:
        values = [float(limit.func(x)) for x in SAMPLE_X]
    except Exception:
        return "<not sampleable>"
    if all(value == values[0] or (math.isnan(value) and math.isnan(values[0])) for value in values):
        return _num(values[0])
    return "x=" + ", ".join(f"{x:g}:{_num(value)}" for x, value in zip(SAMPLE_X, values))


def _flags(limit: Limit) -> str:
    return "upper" if limit.upper else "lower" if limit.lower else NONE


def _max_rating(criterion: Criterion) -> str:
    """
    The criterion's best achievable score.

    A leaf gets it for free from its own limit block, so only the aggregates —
    where the protocol's point budget lives and nothing else records it — have to
    declare one. The marker says which of the two the number is.
    """
    if criterion.max_rating is not None:
        return _num(criterion.max_rating)
    derived = derived_max_rating(criterion)
    return f"{_num(derived)} (from limits)" if derived is not None else NONE


def resolve_sources(overall: Criterion) -> dict[str, str]:
    """
    ``path -> rendered source`` for the whole tree, with **inheritance**.

    ``Criterion.source`` holds a *section* of the protocol document — the document
    itself is a report-level fact and is printed once in the header. A criterion
    that declares none shows its nearest ancestor's, marked ``(inherited)``, so
    declaring it on the root alone is a complete and honest answer: everything
    below is covered by that section until a narrower one is written down.

    Refining later is purely additive — no leaf ever has to repeat its parent.
    """
    resolved: dict[str, str | None] = {}
    rendered: dict[str, str] = {}
    for path, criterion in overall.walk():
        parent = path.rsplit("/", 1)[0] if "/" in path else ""
        inherited = resolved.get(parent) if path else None
        resolved[path] = criterion.source or inherited
        if criterion.source:
            rendered[path] = criterion.source
        elif inherited:
            rendered[path] = f"{inherited} (inherited)"
        else:
            rendered[path] = NONE
    return rendered


def describe_criterion(path: str, criterion: Criterion, source: str = NONE) -> list[str]:
    lines = [f"## `{path or 'Overall'}` — {criterion.name or NONE}", ""]
    lines += _table(
        ["class", "source", "max rating", "aggregation"],
        [[f"`{type(criterion).__name__}`",
          source,
          _max_rating(criterion),
          criterion.aggregation or NONE]],
    )

    for patterns, limits in blocks(criterion).items():
        lines += ["", f"Limits for `{'`, `'.join(patterns) or NONE}`:", ""]
        lines += _table(
            ["row", "threshold", "rating", "color", "flag", "y_unit", "linestyle"],
            [[limit.name or type(limit).__name__,
              _threshold(limit),
              _num(limit.rating),
              limit.color,
              _flags(limit),
              str(limit.y_unit),
              limit.linestyle] for limit in limits],
        )

    specs = {name: spec for name, spec in sorted(criterion.get_input_specs().items())
             if spec.owner is type(criterion)}
    if specs:
        lines += ["", "Manual inputs:", ""]
        lines += _table(
            ["input", "type", "default", "unit", "source", "doc"],
            [[name,
              spec.type_name(),
              _num(spec.default) if isinstance(spec.default, (int, float)) else repr(spec.default),
              spec.unit or NONE,
              spec.source or NONE,
              spec.doc or NONE] for name, spec in specs.items()],
        )

    return lines + [""]


def describe_report(report: Report) -> str:
    """
    ``report`` as Markdown.

    The tree is taken from the first test; every test carries the same
    definition, and the values that do differ between tests are results, which
    this deliberately does not show.
    """
    sources = resolve_sources(report.overall(report.isomme_list[0])) if report.isomme_list else {}

    lines = [f"# {type(report).__name__}", ""]
    lines += _table(
        ["property", "value"],
        [["name", report.name or NONE],
         ["protocol", report.protocol or NONE],
         ["protocols", ", ".join(sorted(report.protocols)) or NONE],
         ["overall criterion", f"`{report.Criterion_Overall.__name__}`"],
         ["pages", ", ".join(type(page).__name__ for page in report.pages) or NONE]],
    )
    lines.append("")

    if report.isomme_list:
        for path, criterion in report.overall(report.isomme_list[0]).walk():
            lines += describe_criterion(path, criterion, sources[path])

    return "\n".join(lines).rstrip() + "\n"
