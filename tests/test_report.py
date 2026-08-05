"""Opt-in PowerPoint smoke tests for every concrete report.

Calculated values are covered by ``tests.test_golden``. PPTX generation is slow
and its binary output is not a useful default regression oracle, so this module
is skipped unless explicitly requested::

    PYISOMME_PPTX=1 .venv/Scripts/python.exe -m unittest tests.test_report
    PYISOMME_PPTX=euro_ncap_side_pole .venv/Scripts/python.exe -m unittest tests.test_report

Each report is exported in a fresh process to avoid the known Windows stack
overflow when all report trees are calculated in one interpreter. The generated
file is reopened and its slide count is checked against the report's page count.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from tests import golden_utils


PPTX_REQUEST = os.environ.get("PYISOMME_PPTX", "")


@unittest.skipUnless(PPTX_REQUEST, "PPTX export is opt-in; set PYISOMME_PPTX=1")
class TestReportPptx(unittest.TestCase):
    def test_requested_reports(self) -> None:
        if PPTX_REQUEST.lower() in {"1", "all", "true"}:
            stems = sorted(golden_utils.BUILDERS)
        else:
            requested = {stem.strip() for stem in PPTX_REQUEST.split(",") if stem.strip()}
            unknown = requested - set(golden_utils.BUILDERS)
            self.assertEqual(set(), unknown,
                             f"unknown report stem(s); available: {sorted(golden_utils.BUILDERS)}")
            stems = sorted(requested)

        output_dir = Path("out")
        output_dir.mkdir(exist_ok=True)
        for stem in stems:
            with self.subTest(report=stem):
                path = output_dir / f"{stem}.pptx"
                completed = subprocess.run(
                    [sys.executable, "-m", "tests.report_pptx_case", stem, str(path)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                counts = json.loads(completed.stdout)
                self.assertTrue(path.is_file())
                self.assertEqual(counts["pages"], counts["slides"])


if __name__ == "__main__":
    unittest.main()
