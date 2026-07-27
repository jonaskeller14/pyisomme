"""
Fixture-free structural net over **every** registered report (plan step 3).

``tests/test_golden.py`` is richer — it carries computed values — but it needs the
untracked fixtures under ``data/`` and covers only three reports. This module
constructs each report from **empty** ``Isomme`` objects, so it needs no data at all
and can therefore run in CI, and it compares the *definition* layer that
``golden_utils.serialise`` already produces: every criterion path, its name and
class, every ``Limit`` row, and the page class list.

That is exactly the layer a structural refactor can break silently — a criterion
reparented, a limit row lost, a page dropped — which is what it was written for: the
step-3 move of each report's criterion tree from a nested ``Criterion_Overall`` to a
module-level ``Overall`` produced a one-line diff per report (the root class name) and
nothing else.

Re-baseline deliberately, like the goldens::

    .venv/Scripts/python.exe -m tests.test_report_structure --regen
    git diff tests/golden/report_structure.json

Step 12's ``Report.describe()`` supersedes this; fold it in there when it lands.
"""
from __future__ import annotations

import importlib
import json
import logging
import os
import sys
import unittest

import pyisomme
from tests import golden_utils


logging.basicConfig(level=logging.ERROR)

GOLDEN = os.path.join(os.path.dirname(__file__), "golden", "report_structure.json")

#: module path under ``pyisomme.report`` -> report class name -> number of Isommes.
#: Every report that defines its own ``Overall`` tree, whether or not it is in
#: ``REPORTS`` in ``pyisomme/__main__.py``. Reports needing two tests (correlation,
#: VTC) compare against ``isomme_list[0]``, so they must not be built with one.
REPORTS: list[tuple[str, str, int]] = [
    ("correlation.correlation", "Correlation", 2),
    ("euro_ncap.frontal_50kmh", "EuroNCAP_Frontal_50kmh", 2),
    ("euro_ncap.frontal_mpdb", "EuroNCAP_Frontal_MPDB", 2),
    ("euro_ncap.side_barrier", "EuroNCAP_Side_Barrier", 1),
    ("euro_ncap.side_farside", "EuroNCAP_Side_FarSide", 1),
    ("euro_ncap.side_farside_vtc", "EuroNCAP_Side_Farside_VTC", 2),
    ("euro_ncap.side_pole", "EuroNCAP_Side_Pole", 1),
    ("iihs.frontal_odb", "IIHS_Frontal_ODB", 1),
    ("iihs.frontal_small_overlap", "IIHS_Frontal_Small_Overlap", 1),
    ("un.frontal_50kmh_r137", "UN_Frontal_50kmh_R137", 1),
    ("un.frontal_56kmh_odb_r94", "UN_Frontal_56kmh_ODB_R94", 1),
    ("un.side_barrier_r95", "UN_Side_Barrier_R95", 1),
    ("un.side_pole_r135", "UN_Side_Pole_R135", 1),
]

#: Modules that define an ``Overall`` but are deliberately not snapshotted.
EXCLUDED: dict[str, str] = {
    "report": "the base Report's empty default tree, not a protocol report",
    "us_ncap.frontal_56kmh": "unfinished stub; construction raises NotImplementedError "
                             "(review Appendix A5, cleared as a stub in step 2)",
}


def build(dotted: str, name: str, n_isomme: int) -> dict:
    """Construct one report from empty Isommes and return its definition layer."""
    module = importlib.import_module(f"pyisomme.report.{dotted}")
    report = getattr(module, name)([pyisomme.Isomme(test_number=f"T{i}") for i in range(n_isomme)])
    return golden_utils.serialise(report)["definition"]


def produce() -> dict:
    return {name: build(dotted, name, n) for dotted, name, n in REPORTS}


class TestReportStructure(unittest.TestCase):
    def test_structure_matches_golden(self) -> None:
        if not os.path.exists(GOLDEN):
            self.fail(f"missing {GOLDEN} — create it with "
                      f"`python -m tests.test_report_structure --regen`")
        with open(GOLDEN, encoding="utf-8") as handle:
            golden = json.load(handle)
        current = produce()

        self.assertEqual(sorted(golden), sorted(current), "the set of reports changed")
        for name in sorted(current):
            with self.subTest(report=name):
                self.assertEqual(
                    golden[name], current[name],
                    f"{name}'s definition changed. If that is intended, re-baseline with "
                    f"`python -m tests.test_report_structure --regen` and explain the diff.",
                )

    def test_every_report_module_is_covered(self) -> None:
        """A new report module with its own ``Overall`` must be added to REPORTS."""
        import pathlib

        covered = {dotted for dotted, _, _ in REPORTS} | set(EXCLUDED)
        root = pathlib.Path(pyisomme.report.__file__).parent
        missing = []
        for path in sorted(root.rglob("*.py")):
            source = path.read_text(encoding="utf-8")
            if "\nclass Overall(Criterion):" not in source:
                continue
            dotted = ".".join(path.relative_to(root).with_suffix("").parts)
            if dotted not in covered:
                missing.append(dotted)
        self.assertEqual(missing, [], "report modules defining an `Overall` but not listed in REPORTS")


def _regen() -> int:
    data = produce()
    with open(GOLDEN, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=1, sort_keys=True)
        handle.write("\n")
    for name, definition in sorted(data.items()):
        limits = sum(len(node["limits"]) for node in definition["criteria"].values())
        print(f"  {name}: {len(definition['criteria'])} criteria, {limits} limit rows, "
              f"{len(definition['pages'])} pages")
    print(f"\n-> {GOLDEN}\nReview `git diff tests/golden/report_structure.json` before committing.")
    return 0


if __name__ == "__main__":
    if "--regen" in sys.argv:
        raise SystemExit(_regen())
    unittest.main()
