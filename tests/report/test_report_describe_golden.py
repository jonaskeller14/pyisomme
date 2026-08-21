from pathlib import Path

import pytest

from pyisomme.report import ALL_REPORTS
from tests.report.report_factory import REPORT_FACTORIES


@pytest.fixture
def assert_golden_describe(regen_golden):
    """
    Returns a function to compare data against a stored golden file.
    Updates the file if --regen-golden is present.
    """

    def _assert_or_update(golden_path: Path, description: str) -> None:
        golden_path = Path(golden_path)

        # 1. Regenerate workflow
        if regen_golden or not golden_path.exists():
            golden_path.parent.mkdir(parents=True, exist_ok=True)
            golden_path.write_text(description, encoding="utf-8")
            return

        # 2. Expected data
        expected_description = golden_path.read_text(encoding="utf-8")

        # 3. Assert Equal
        assert description == expected_description

    return _assert_or_update


@pytest.mark.parametrize("report_cls", ALL_REPORTS)
def test_report_describe_golden(assert_golden_describe, report_cls):
    report = REPORT_FACTORIES[report_cls]()
    report.calculate()

    assert_golden_describe(
        Path(f"tests/golden/describe/{report_cls.__name__}.md"),
        report.describe(),
    )
