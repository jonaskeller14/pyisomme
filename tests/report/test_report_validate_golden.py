import json
from pathlib import Path

import pytest

from pyisomme.report import ALL_REPORTS
from tests.report.report_factory import REPORT_FACTORIES


@pytest.fixture
def assert_golden_validate(regen_golden):
    def assert_or_update(golden_path: Path, json_validate: dict) -> None:
        golden_path = Path(golden_path)

        # 1. Regenerate workflow
        if regen_golden or not golden_path.exists():
            golden_path.parent.mkdir(parents=True, exist_ok=True)
            golden_path.write_text(json.dumps(json_validate, indent=2))
            return

        # 2. Expected data
        expected_data = json.loads(golden_path.read_text())

        # 3. Assert Equal
        assert json_validate == expected_data

    return assert_or_update


def test_report_validate_golden(assert_golden_validate):
    json_validate = {
        report_cls.__name__: [
            str(issue) for issue in REPORT_FACTORIES[report_cls]().validate()
        ]
        for report_cls in ALL_REPORTS
    }

    assert_golden_validate(
        Path("tests/golden/validate.json"),
        json_validate,
    )
