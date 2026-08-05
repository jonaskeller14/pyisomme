"""
Shared machinery for the golden-file safety net (refactor plan, Step 1).

This is the calculated-results layer: per-``Isomme`` ``value`` / ``rating`` /
``color`` / ``status`` plus the public ``print_results()`` rendering. Values are
compared with **no-regression** semantics: whatever is known today must stay
identical, but a criterion that is ``nan`` today may start producing a number.

The fixture-free, engineer-readable definition contract lives separately in
``tests/test_describe.py``. Keeping those concerns separate avoids storing the
same criterion/Limit definition in Markdown and JSON.

Regenerate with ``.venv/Scripts/python.exe -m tests.golden_regen``.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
import math
import os
import subprocess
import sys
from typing import Any

import numpy as np

from pyisomme.limit import Limit
from pyisomme.report.criterion import Criterion
from pyisomme.report.meta_report import MetaReport
from pyisomme.report.report import Report
from tests.report_registry import BY_STEM, build_euro_ncap_synthetic, build_synthetic


GOLDEN_DIR = os.path.join(os.path.dirname(__file__), "golden")
#: x positions at which every ``Limit.func`` is sampled to make it comparable.
LIMIT_SAMPLE_X = (0.0, 0.001, 0.01, 0.05, 0.1, 0.5, 1.0)

#: Relative tolerance for float comparison of values and ratings.
RTOL = 1e-9

#: How bad a :class:`~pyisomme.errors.Status` is. A criterion may only ever move
#: *up* this scale; moving down is a regression.
STATUS_RANK = {"ERROR": 0, "PENDING": 1, "NA": 2, "OK": 3}


# --------------------------------------------------------------------------- #
# scalar encoding
# --------------------------------------------------------------------------- #

def is_nan(value: Any) -> bool:
    return isinstance(value, float) and math.isnan(value)


def encode(value: Any) -> Any:
    """Make a criterion/limit scalar JSON-safe without losing nan/inf identity."""
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
        return value
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        if math.isinf(value):
            return "inf" if value > 0 else "-inf"
        return value
    if isinstance(value, (tuple, list, np.ndarray)):
        return [encode(item) for item in value]
    return repr(value)


def decode(value: Any) -> Any:
    """Inverse of :func:`encode` for the three special float spellings."""
    if value == "nan":
        return float("nan")
    if value == "inf":
        return float("inf")
    if value == "-inf":
        return float("-inf")
    return value


def equal(a: Any, b: Any) -> bool:
    """Compare two decoded scalars; ``nan`` equals ``nan`` (G9 — the nans are expected)."""
    a, b = decode(a), decode(b)
    if is_nan(a) and is_nan(b):
        return True
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if math.isinf(a) or math.isinf(b):
            return a == b
        return math.isclose(a, b, rel_tol=RTOL, abs_tol=0.0)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b


# --------------------------------------------------------------------------- #
# tree walking
# --------------------------------------------------------------------------- #

def walk(criterion: Criterion, path: str = "") -> list[tuple[str, Criterion]]:
    """
    ``(path, criterion)`` for the whole tree, with the root named ``"Overall"``.

    Thin wrapper over :meth:`Criterion.walk`, which is ``dir()``-ordered. Step 7
    replaces ``dir()`` discovery with declaration order; that changes the *order*
    of this list but not its content, and the golden files are keyed by path, so
    ordering is deliberately irrelevant here.
    """
    return [(node_path or "Overall", node) for node_path, node in criterion.walk(path)]


def serialise_limit(limit: Limit) -> dict:
    samples = []
    for x in LIMIT_SAMPLE_X:
        try:
            samples.append(encode(limit.func(x)))
        except Exception as error:  # pragma: no cover - a limit func that cannot be sampled
            samples.append(f"<error: {type(error).__name__}>")
    return {
        "name": limit.name,
        "code_patterns": list(limit.code_patterns or []),
        # A9: `rating` has no default, so an under-specified Limit has no attribute at all.
        "rating": encode(getattr(limit, "rating", None)),
        "color": encode(limit.color),
        "linestyle": limit.linestyle,
        "lower": limit.lower,
        "upper": limit.upper,
        "x_unit": str(limit.x_unit),
        "y_unit": str(limit.y_unit),
        "func_samples": samples,
    }


def serialise_definition(report: Report) -> dict:
    """The exact, measurement-independent report definition."""
    first = report.isomme_list[0]
    return {
        "pages": [type(page).__name__ for page in report.pages],
        "criteria": {
            path: {
                "name": criterion.name,
                "class": type(criterion).__name__,
                "limits": [serialise_limit(limit) for limit in criterion.limits.limit_list],
            }
            for path, criterion in walk(report.criterion_overall[first])
        },
    }


def _tree_results(report: Report) -> dict:
    return {
        str(isomme.test_number): {
            path: {
                "value": encode(criterion.value),
                "rating": encode(criterion.rating),
                "color": encode(criterion.color),
                "status": criterion.status.name,
            }
            for path, criterion in walk(report.criterion_overall[isomme])
        }
        for isomme in report.isomme_list
    }


def serialise_results(report: Report) -> dict:
    """Full-precision calculated results plus the public text rendering."""
    if isinstance(report, MetaReport):
        results = {
            f"{type(subreport).__name__}:{test}": tree
            for subreport in report.reports
            for test, tree in _tree_results(subreport).items()
        }
        results[type(report).__name__] = {
            "Overall": {"value": encode(report.rating), "rating": encode(report.rating),
                        "color": None, "status": "OK"},
            **{
                f"ratings/{label}": {"value": encode(points), "rating": encode(points),
                                      "color": None, "status": "OK"}
                for label, points in report.ratings.items()
            },
        }
    else:
        results = _tree_results(report)

    output = StringIO()
    with redirect_stdout(output):
        report.print_results()
    return {"report": type(report).__name__,
            "results": results,
            "print_results": output.getvalue().splitlines()}


def serialise(report: Report) -> dict:
    """Combined representation retained for definition-oriented test helpers."""
    return {**serialise_results(report), "definition": serialise_definition(report)}


# --------------------------------------------------------------------------- #
# comparison
# --------------------------------------------------------------------------- #

def compare(golden: dict, current: dict) -> tuple[list[str], list[str]]:
    """
    Compare a stored golden against a freshly serialised report.

    Returns ``(regressions, improvements)``. Only *regressions* fail a test:

    * results — a known value/rating/color changing, disappearing, or a status
      moving down :data:`STATUS_RANK`;
    * ``print_results`` — any output change, because ordering and formatting are
      part of the public rendering contract;

    while a ``nan`` becoming a number, or an ``ERROR`` becoming ``NA``/``OK``,
    counts as an improvement and is reported but tolerated.
    """
    regressions: list[str] = []
    improvements: list[str] = []

    # -- results: no-regression -------------------------------------------- #
    gold_results, cur_results = golden["results"], current["results"]
    for test in sorted(set(gold_results) - set(cur_results)):
        regressions.append(f"results: test disappeared: {test}")
    for test in sorted(set(gold_results) & set(cur_results)):
        gold_tree, cur_tree = gold_results[test], cur_results[test]
        for path in sorted(set(gold_tree) - set(cur_tree)):
            regressions.append(f"results[{test}]: criterion disappeared: {path}")
        for path in sorted(set(gold_tree) & set(cur_tree)):
            gold_node, cur_node = gold_tree[path], cur_tree[path]

            for field in ("value", "rating"):
                gold_val, cur_val = gold_node[field], cur_node[field]
                if is_nan(decode(gold_val)):
                    if not is_nan(decode(cur_val)):
                        improvements.append(f"results[{test}]: {path}.{field}: nan -> {cur_val}")
                elif not equal(gold_val, cur_val):
                    regressions.append(f"results[{test}]: {path}.{field}: {gold_val} -> {cur_val}")

            gold_color, cur_color = gold_node["color"], cur_node["color"]
            if gold_color is None:
                if cur_color is not None:
                    improvements.append(f"results[{test}]: {path}.color: None -> {cur_color}")
            elif not equal(gold_color, cur_color):
                regressions.append(f"results[{test}]: {path}.color: {gold_color} -> {cur_color}")

            gold_rank = STATUS_RANK.get(gold_node["status"], -1)
            cur_rank = STATUS_RANK.get(cur_node["status"], -1)
            if cur_rank < gold_rank:
                regressions.append(
                    f"results[{test}]: {path}.status: {gold_node['status']} -> {cur_node['status']}"
                )
            elif cur_rank > gold_rank:
                improvements.append(
                    f"results[{test}]: {path}.status: {gold_node['status']} -> {cur_node['status']}"
                )

    if golden.get("print_results") != current.get("print_results"):
        regressions.append("print_results output changed")

    return regressions, improvements


# --------------------------------------------------------------------------- #
# report builders
# --------------------------------------------------------------------------- #

BUILDERS = {stem: (lambda spec=spec: build_synthetic(spec)) for stem, spec in BY_STEM.items()}
BUILDERS["euro_ncap"] = build_euro_ncap_synthetic


def golden_path(stem: str) -> str:
    return os.path.join(GOLDEN_DIR, f"{stem}.json")


def produce(stem: str) -> dict:
    """Construct, calculate and serialise the report behind ``stem``."""
    report = BUILDERS[stem]()
    report.calculate()
    return serialise_results(report)


def produce_isolated(stem: str) -> dict:
    """Produce one golden in a fresh process (avoids the known 13-report stack overflow)."""
    completed = subprocess.run(
        [sys.executable, "-m", "tests.golden_case", stem],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def load(stem: str) -> dict:
    with open(golden_path(stem), encoding="utf-8") as file:
        return json.load(file)


def store(stem: str, data: dict) -> None:
    os.makedirs(GOLDEN_DIR, exist_ok=True)
    with open(golden_path(stem), "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, sort_keys=True)
        file.write("\n")
