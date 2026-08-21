# test_golden.py
import json
import math
from pathlib import Path
from typing import Any

import pytest

from pyisomme.report import ALL_REPORTS
from pyisomme.utils import json_decode, json_encode
from tests.report.report_factory import REPORT_FACTORIES


def encode_dict_tree(data: Any) -> Any:
    """Recursively encode values in dicts, lists, and tuples."""
    if isinstance(data, dict):
        return {k: encode_dict_tree(v) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return [encode_dict_tree(v) for v in data]
    return json_encode(data)


def decode_dict_tree(data: Any) -> Any:
    """Recursively decode values in dicts and lists."""
    if isinstance(data, dict):
        return {k: decode_dict_tree(v) for k, v in data.items()}
    if isinstance(data, list):
        return [decode_dict_tree(v) for v in data]
    return json_decode(data)


def assert_tree_equal(actual: Any, expected: Any) -> None:
    """Recursively compare structures handling NaN equality and static typing."""

    # 1. Dictionary Handling
    if isinstance(actual, dict):
        assert isinstance(expected, dict), f"Type mismatch: dict vs {type(expected)}"
        assert actual.keys() == expected.keys(), (
            f"Key mismatch: {actual.keys()} != {expected.keys()}"
        )
        for key in actual:
            assert_tree_equal(actual[key], expected[key])

    # 2. Sequence Handling (List / Tuple)
    elif isinstance(actual, (list, tuple)):
        assert isinstance(expected, (list, tuple)), (
            f"Type mismatch: {type(actual)} vs {type(expected)}"
        )
        assert len(actual) == len(expected), (
            f"Length mismatch: {len(actual)} != {len(expected)}"
        )
        for act_item, exp_item in zip(actual, expected):
            assert_tree_equal(act_item, exp_item)

    # 3. Float Handling (NaN / Inf)
    elif isinstance(actual, float) and isinstance(expected, float):
        if math.isnan(actual) or math.isnan(expected):
            assert math.isnan(actual) and math.isnan(expected)
        else:
            assert actual == pytest.approx(expected)

    # 4. Scalar Fallback
    else:
        assert actual == expected


@pytest.fixture
def assert_golden_results(regen_golden):
    """
    Returns a function to compare data against a stored golden file.
    Updates the file if --regen-golden is present.
    """

    def _assert_or_update(golden_path: Path, json_results: dict) -> None:
        golden_path = Path(golden_path)

        # 1. Regenerate workflow
        if regen_golden or not golden_path.exists():
            golden_path.parent.mkdir(parents=True, exist_ok=True)
            golden_path.write_text(json.dumps(json_results, indent=2), encoding="utf-8")
            return

        # 2. Expected data
        expected_data_raw = json.loads(golden_path.read_text())
        expected_data = decode_dict_tree(expected_data_raw)

        actual_data = decode_dict_tree(json_results)

        # 3. Assert Equal
        assert_tree_equal(actual_data, expected_data)

    return _assert_or_update


@pytest.mark.parametrize("report_cls", ALL_REPORTS)
def test_report_results_golden(assert_golden_results, report_cls):
    report = REPORT_FACTORIES[report_cls]()
    report.calculate()

    assert_golden_results(
        Path(f"tests/golden/{report_cls.__name__}.json"),
        report.json_results(),
    )


def test_report_results_golden_preserves_criterion_tree():
    report = REPORT_FACTORIES[next(iter(ALL_REPORTS))]()
    report.calculate()

    test_results = next(iter(report.json_results().values()))
    assert "Overall" in test_results
    assert test_results["Overall"]["result"]["name"] == "Overall"
