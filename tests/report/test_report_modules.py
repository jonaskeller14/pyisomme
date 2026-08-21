"""Import smoke test for the whole ``pyisomme.report`` package."""

from __future__ import annotations

import importlib
import os
import pkgutil

import pyisomme.report

REPORT_DIR = os.path.dirname(pyisomme.report.__file__)


def iter_report_modules() -> list[str]:
    """Every module name under ``pyisomme/report/``, recursively."""
    names = []
    for module_info in pkgutil.walk_packages([REPORT_DIR], prefix="pyisomme.report."):
        names.append(module_info.name)
    return sorted(names)


class TestReportModuleImports:
    def test_every_module_imports(self):
        failures = []
        for name in iter_report_modules():
            try:
                importlib.import_module(name)
            except Exception as error:
                failures.append(f"{name}: {type(error).__name__}: {error}")
        assert [] == failures, (
            "modules under pyisomme/report/ failed to import:\n" + "\n".join(failures)
        )
