from __future__ import annotations

import logging
import os
import sys
import unittest

from pyisomme.report.describe import NONE, resolve_sources
from tests.test_validate import GOLDEN_DIR, attach, build, leaf


logging.basicConfig(level=logging.ERROR)

DESCRIBE_DIR = os.path.join(GOLDEN_DIR, "describe")
DESCRIBED = ("EuroNCAP_Frontal_50kmh", "EuroNCAP_Frontal_MPDB")


def describe_path(name: str) -> str:
    return os.path.join(DESCRIBE_DIR, f"{name}.md")


class TestDescribe(unittest.TestCase):
    def test_matches_golden(self) -> None:
        for name in DESCRIBED:
            with self.subTest(report=name):
                path = describe_path(name)
                if not os.path.exists(path):
                    self.fail(f"missing {path} — create it with "
                              f"`python -m tests.test_describe --regen`")
                with open(path, encoding="utf-8") as handle:
                    golden = handle.read()
                self.assertEqual(
                    golden.splitlines(), build(name).describe().splitlines(),
                    f"{name}'s definition changed. If that is intended, re-baseline with "
                    f"`python -m tests.test_describe --regen` and explain the diff.",
                )

    def test_source_is_inherited_down_the_tree(self) -> None:
        """A section declared on one criterion covers everything below it."""
        root = leaf([], source="§5")
        child = attach(root, "child", leaf([]))
        grandchild = attach(child, "grandchild", leaf([], source="§5.2.1"))
        attach(grandchild, "great", leaf([]))

        self.assertEqual(
            resolve_sources(root),
            {"": "§5",
             "child": "§5 (inherited)",
             "child/grandchild": "§5.2.1",
             "child/grandchild/great": "§5.2.1 (inherited)"},
        )

    def test_source_absent_everywhere(self) -> None:
        root = leaf([])
        attach(root, "child", leaf([]))
        self.assertEqual(set(resolve_sources(root).values()), {NONE})

    def test_covers_every_criterion(self) -> None:
        report = build("EuroNCAP_Frontal_50kmh")
        text = report.describe()
        for path, _ in report.overall(report.isomme_list[0]).walk():
            self.assertIn(f"`{path or 'Overall'}`", text)


# --------------------------------------------------------------------------- #
# baseline
# --------------------------------------------------------------------------- #

def _regen() -> int:
    os.makedirs(DESCRIBE_DIR, exist_ok=True)
    for name in DESCRIBED:
        text = build(name).describe()
        with open(describe_path(name), "w", encoding="utf-8") as handle:
            handle.write(text)
        print(f"  {describe_path(name)}: {len(text.splitlines())} lines")
    print("\nReview `git diff tests/golden/` before committing.")
    return 0


if __name__ == "__main__":
    if "--regen" in sys.argv:
        raise SystemExit(_regen())
    unittest.main()
