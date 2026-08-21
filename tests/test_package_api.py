"""Regression tests for the documented top-level package API."""

from __future__ import annotations

import pyisomme


def test_top_level_domain_model_and_report_exports() -> None:
    assert pyisomme.Channel
    assert pyisomme.Correlation_ISO18571
    assert pyisomme.Isomme
    assert pyisomme.report.IIHS_Side_Impact
