"""
Import smoke test for the whole ``pyisomme.report`` package (plan Step 1).

Needs **no fixture data**, so it is the one report test that can run in CI. It
catches two distinct kinds of breakage the golden tests cannot see:

1. a module under ``pyisomme/report/`` that does not import at all;
2. a subpackage that imports fine but is not re-exported by
   ``pyisomme/report/__init__.py``, so ``pyisomme.report.<name>`` raises
   ``AttributeError`` for a user who only did ``import pyisomme``.

Known breakage is listed explicitly below rather than silently tolerated.
"""
from __future__ import annotations

import importlib
import os
import pkgutil
import subprocess
import sys
import unittest

import pyisomme.report


REPORT_DIR = os.path.dirname(pyisomme.report.__file__)

# --------------------------------------------------------------------------- #
# Known-broken modules. Every entry must name the defect and the step that owns
# it. Shrinking this list is part of Step 2's acceptance criteria.
# --------------------------------------------------------------------------- #
BROKEN_MODULES: set = set()

# Subpackages that exist on disk but `pyisomme/report/__init__.py` does not import,
# so they are not reachable as attributes of `pyisomme.report`.
MISSING_REEXPORTS: set = set()


def iter_report_modules() -> list[str]:
    """Every module name under ``pyisomme/report/``, recursively."""
    names = []
    for module_info in pkgutil.walk_packages([REPORT_DIR], prefix="pyisomme.report."):
        names.append(module_info.name)
    return sorted(names)


class TestReportModuleImports(unittest.TestCase):
    def test_every_module_imports(self):
        failures = []
        for name in iter_report_modules():
            if name in BROKEN_MODULES:
                continue
            try:
                importlib.import_module(name)
            except Exception as error:
                failures.append(f"{name}: {type(error).__name__}: {error}")
        self.assertEqual([], failures, "modules under pyisomme/report/ failed to import:\n" + "\n".join(failures))

    def test_broken_modules_are_still_broken(self):
        """
        Guard against a stale skip list: if one of these starts importing, the
        entry must be removed rather than left to rot.
        """
        unexpectedly_fine = []
        for name in sorted(BROKEN_MODULES):
            try:
                importlib.import_module(name)
            except Exception:
                continue
            unexpectedly_fine.append(name)
        self.assertEqual(
            [], unexpectedly_fine,
            "these now import fine — remove them from BROKEN_MODULES:\n" + "\n".join(unexpectedly_fine),
        )

    def test_module_walk_found_something(self):
        names = iter_report_modules()
        self.assertGreater(len(names), 20, f"pkgutil walk found suspiciously few modules: {names}")


class TestReportSubpackageReexports(unittest.TestCase):
    """
    `pyisomme/report/__init__.py` must expose every protocol subpackage.

    A `pkgutil` module walk does *not* catch this: the modules import fine, they
    are simply not bound as attributes of `pyisomme.report`.

    Each check runs in a **fresh interpreter**, because importing a submodule
    binds it onto its parent package as a side effect — so once any other test in
    this process has touched `pyisomme.report.correlation.correlation`, the
    attribute exists and an in-process check silently passes.
    """

    def subpackages_on_disk(self) -> list[str]:
        return sorted(
            entry for entry in os.listdir(REPORT_DIR)
            if os.path.isdir(os.path.join(REPORT_DIR, entry)) and not entry.startswith("__")
        )

    @staticmethod
    def reachable_in_fresh_interpreter(name: str) -> bool:
        result = subprocess.run(
            [sys.executable, "-c", f"import pyisomme; print(hasattr(pyisomme.report, {name!r}))"],
            capture_output=True, text=True,
        )
        return result.stdout.strip().splitlines()[-1] == "True" if result.stdout.strip() else False

    def test_every_subpackage_is_reachable_as_an_attribute(self):
        missing = [
            name for name in self.subpackages_on_disk()
            if name not in MISSING_REEXPORTS and not self.reachable_in_fresh_interpreter(name)
        ]
        self.assertEqual(
            [], missing,
            "subpackages not re-exported by pyisomme/report/__init__.py:\n" + "\n".join(missing),
        )

    def test_missing_reexports_list_is_not_stale(self):
        now_present = [
            name for name in sorted(MISSING_REEXPORTS)
            if self.reachable_in_fresh_interpreter(name)
        ]
        self.assertEqual(
            [], now_present,
            "these are re-exported now — remove them from MISSING_REEXPORTS:\n" + "\n".join(now_present),
        )


if __name__ == "__main__":
    unittest.main()
