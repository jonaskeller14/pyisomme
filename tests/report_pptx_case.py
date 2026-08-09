"""Child-process entry point for one opt-in PPTX smoke test."""
from __future__ import annotations

import json
import logging
import sys

from pptx import Presentation

from tests import golden_utils


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    report = golden_utils.BUILDERS[sys.argv[1]]()
    report.calculate().export_pptx(sys.argv[2])
    presentation = Presentation(sys.argv[2])
    json.dump({"pages": len(report.selected_pages), "slides": len(presentation.slides)}, sys.stdout)
