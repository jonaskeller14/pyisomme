"""
Shared machinery for the golden-file safety net (refactor plan, Step 1).

The net has two layers, because the available fixtures only populate part of any
report:

* **definition** — criterion paths, names and every attached ``Limit``. Entirely
  independent of measurement data, so it stays fully populated even where every
  value is ``nan``. Compared *exactly*: a moved threshold or a dropped criterion
  is a failure that must be re-baselined deliberately.
* **results** — per-``Isomme`` ``value`` / ``rating`` / ``color`` / ``status``.
  Compared with **no-regression** semantics: whatever is known today must stay
  identical, but a criterion that is ``nan`` today may start producing a number
  (that is an improvement, not a failure). See :func:`compare`.

Regenerate with ``.venv/Scripts/python.exe -m tests.golden_regen``.
"""
from __future__ import annotations

import json
import math
import os
from typing import Any, Callable

import numpy as np

import pyisomme
from pyisomme.report.criterion import Criterion
from pyisomme.report.report import Report


GOLDEN_DIR = os.path.join(os.path.dirname(__file__), "golden")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

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
    Yield ``(path, criterion)`` for the whole tree, ``dir()``-ordered.

    Step 7 replaces ``dir()`` discovery with declaration order. That changes the
    *order* of this list but not its content, and the golden files are keyed by
    path, so ordering is deliberately irrelevant here.
    """
    nodes = [(path or "Overall", criterion)]
    for attr in sorted(dir(criterion)):
        if attr.startswith("__"):
            continue
        try:
            child = getattr(criterion, attr)
        except Exception:  # pragma: no cover - defensive: properties may raise
            continue
        if isinstance(child, Criterion):
            nodes += walk(child, f"{path}/{attr}" if path else attr)
    return nodes


def serialise_limit(limit) -> dict:
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


def serialise(report: Report) -> dict:
    """Serialise a *calculated* report into its golden representation."""
    first = report.isomme_list[0]
    definition = {
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

    results = {}
    for isomme in report.isomme_list:
        results[str(isomme.test_number)] = {
            path: {
                "value": encode(criterion.value),
                "rating": encode(criterion.rating),
                "color": encode(criterion.color),
                "status": criterion.status.name,
            }
            for path, criterion in walk(report.criterion_overall[isomme])
        }

    return {
        "report": type(report).__name__,
        "definition": definition,
        "results": results,
    }


# --------------------------------------------------------------------------- #
# comparison
# --------------------------------------------------------------------------- #

def compare(golden: dict, current: dict) -> tuple[list[str], list[str]]:
    """
    Compare a stored golden against a freshly serialised report.

    Returns ``(regressions, improvements)``. Only *regressions* fail a test:

    * definition — any difference at all (thresholds and structure must be
      re-baselined on purpose);
    * results — a known value/rating/color changing, disappearing, or a status
      moving down :data:`STATUS_RANK`;

    while a ``nan`` becoming a number, or an ``ERROR`` becoming ``NA``/``OK``,
    counts as an improvement and is reported but tolerated.
    """
    regressions: list[str] = []
    improvements: list[str] = []

    # -- definition: exact ------------------------------------------------- #
    gold_def, cur_def = golden["definition"], current["definition"]
    if gold_def["pages"] != cur_def["pages"]:
        regressions.append(
            f"definition/pages changed:\n    golden : {gold_def['pages']}\n    current: {cur_def['pages']}"
        )

    gold_criteria, cur_criteria = gold_def["criteria"], cur_def["criteria"]
    for path in sorted(set(gold_criteria) - set(cur_criteria)):
        regressions.append(f"definition: criterion disappeared: {path}")
    for path in sorted(set(cur_criteria) - set(gold_criteria)):
        improvements.append(f"definition: new criterion: {path}")
    for path in sorted(set(gold_criteria) & set(cur_criteria)):
        gold_node, cur_node = gold_criteria[path], cur_criteria[path]
        if gold_node["name"] != cur_node["name"]:
            regressions.append(
                f"definition: {path}: name {gold_node['name']!r} -> {cur_node['name']!r}"
            )
        if gold_node["limits"] != cur_node["limits"]:
            regressions.append(
                f"definition: {path}: limits changed "
                f"({len(gold_node['limits'])} -> {len(cur_node['limits'])} rows)\n"
                f"    golden : {json.dumps(gold_node['limits'])[:400]}\n"
                f"    current: {json.dumps(cur_node['limits'])[:400]}"
            )

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

    return regressions, improvements


# --------------------------------------------------------------------------- #
# fixtures and report builders
# --------------------------------------------------------------------------- #

def _read(*parts: str, pattern: str | None = None):
    path = os.path.join(DATA_DIR, *parts)
    return pyisomme.Isomme().read(path, pattern) if pattern else pyisomme.Isomme().read(path)


def build_euro_ncap_frontal_50kmh() -> Report:
    """Mirrors ``tests.test_report.TestReport.test_EuroNCAP_Frontal_50kmh`` (minus the export)."""
    v1 = _read("iso-mme-org", "MME 1.6 Testdata short", "AK3T02FO", pattern="[!B][013]*")
    v2 = _read("nhtsa", "14084", pattern="[!B][013]*")
    for channel in v1.channels + v2.channels:
        if channel.code.main_location == "NECK" and channel.code.fine_location_3 in ("00", "??"):
            channel.set_code(fine_location_3="H3")
    return pyisomme.report.euro_ncap.frontal_50kmh.EuroNCAP_Frontal_50kmh([v1, v2])


def build_euro_ncap_side_barrier() -> Report:
    """
    Mirrors ``tests.test_report.TestReport.test_EuroNCAP_Side_Barrier`` (minus the export).

    The synthetic channels come from ``create_sample``, which is deterministic
    (``linspace``/``sin``, no RNG), so this report is reproducible even though the
    fixture does not carry the side-impact instrumentation.
    """
    v1 = _read("iso-mme-org", "MME 1.6 Testdata short", "AK3T02FO", pattern="[!B][013]*")
    v1.extend([
        pyisomme.create_sample("11SHLDLE00WSFOY0", y_range=(-4, 3), unit="kN"),
        pyisomme.create_sample("11SHLDRI00WSFOY0", y_range=(1, 2), unit="kN"),
        pyisomme.create_sample("11TRRILE01WSDSYP", y_range=(-30, 0), unit="mm"),
        pyisomme.create_sample("11TRRILE02WSDSYP", y_range=(-30, 0), unit="mm"),
        pyisomme.create_sample("11TRRILE03WSDSYP", y_range=(-30, 0), unit="mm"),
        pyisomme.create_sample("11ABRILE01WSDSYP", y_range=(-30, 0), unit="mm"),
        pyisomme.create_sample("11ABRILE02WSDSYP", y_range=(-30, 0), unit="mm"),
        pyisomme.create_sample("11PUBC0000WSFOYB", y_range=(-3., 0), unit="kN"),
    ])
    return pyisomme.report.euro_ncap.side_barrier.EuroNCAP_Side_Barrier([v1])


def build_euro_ncap_frontal_mpdb() -> Report:
    """
    Mirrors ``tests.test_report.TestReport.test_EuroNCAP_Frontal_MPDB`` (minus the export).

    Added in Step 2, once the unguarded ``calculate_olc`` in ``Page_OLC_Trolley``
    (progress item D1) stopped breaking construction. None of these fixtures carries
    a trolley (``M?MBAR…VEXA``) channel, so the OLC page is empty here.
    """
    v1 = _read("iso-mme-org", "MME 1.6 Testdata short", "AK3T02FO", pattern="[!B][013]*")
    v2 = _read("nhtsa", "14084", pattern="[!B][013]*")
    v3 = _read("nhtsa", "09203", pattern="[!B][013]*")
    for channel in v3.channels:
        if channel.code.main_location == "TIBI" and channel.code.fine_location_3 in ("00", "??"):
            channel.set_code(fine_location_3="TH")
    return pyisomme.report.euro_ncap.frontal_mpdb.EuroNCAP_Frontal_MPDB([v3, v2, v1])


#: Golden-file stem -> builder. Deliberately small: covers a frontal tree
#: (64 criteria, 172 limits), a side tree (13 criteria, 48 limits, 100 % rating
#: coverage) and the MPDB tree.
BUILDERS: dict[str, Callable[[], Report]] = {
    "euro_ncap_frontal_50kmh": build_euro_ncap_frontal_50kmh,
    "euro_ncap_frontal_mpdb": build_euro_ncap_frontal_mpdb,
    "euro_ncap_side_barrier": build_euro_ncap_side_barrier,
}


def golden_path(stem: str) -> str:
    return os.path.join(GOLDEN_DIR, f"{stem}.json")


def produce(stem: str) -> dict:
    """Construct, calculate and serialise the report behind ``stem``."""
    report = BUILDERS[stem]()
    report.calculate()
    return serialise(report)


def load(stem: str) -> dict:
    with open(golden_path(stem), encoding="utf-8") as file:
        return json.load(file)


def store(stem: str, data: dict) -> None:
    os.makedirs(GOLDEN_DIR, exist_ok=True)
    with open(golden_path(stem), "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, sort_keys=True)
        file.write("\n")
