from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pyisomme.__main__ import CODE_FIELDS, build_parser, main
from pyisomme.channel import Channel
from pyisomme.isomme import Isomme


@dataclass(frozen=True)
class CliFiles:
    root: Path
    mme: Path
    second_mme: Path


def make_isomme(test_number: str, scale: float) -> Isomme:
    time = np.array([0.0, 0.001, 0.002])
    return Isomme(
        test_number=test_number,
        test_info=[],
        channel_info=[],
        channels=[
            Channel(
                "11HEAD000000ACXP",
                pd.DataFrame([1.0, 2.0, 3.0], index=time),
                "g",
                info=[("Reference channel", "implicit")],
            ),
            Channel(
                "13CHST000000DSXP",
                pd.DataFrame(np.array([4.0, 5.0, 6.0]) * scale, index=time),
                "m",
                info=[("Reference channel", "implicit")],
            ),
            Channel(
                "14HEAD000000ACXP",
                pd.DataFrame([7.0, 8.0, 9.0], index=time),
                "g",
                info=[("Reference channel", "implicit")],
            ),
        ],
    )


@pytest.fixture
def cli_files(tmp_path: Path) -> CliFiles:
    mme = tmp_path / "CLI.mme"
    second_mme = tmp_path / "second" / "CLI2.mme"
    second_mme.parent.mkdir()
    make_isomme("CLI", 1.0).write(mme)
    make_isomme("CLI2", 2.0).write(second_mme)
    return CliFiles(tmp_path, mme, second_mme)


@pytest.fixture
def run_cli(capsys: pytest.CaptureFixture[str]) -> Callable[..., str]:
    def _run(*arguments: str) -> str:
        main(list(arguments))
        return capsys.readouterr().out

    return _run


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def required_channel(isomme: Isomme, pattern: str) -> Channel:
    channel = isomme.get_channel(pattern)
    assert channel is not None
    return channel


def test_help_exposes_set_convert_and_all_fields(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Ensure the CLI help documents all supported mutation fields and commands."""
    parser = build_parser()
    with pytest.raises(SystemExit, match="0"):
        parser.parse_args(["set", "--help"])
    help_text = capsys.readouterr().out
    assert "Quote wildcard patterns" in help_text
    for field in ("unit", *CODE_FIELDS):
        assert field in help_text

    with pytest.raises(SystemExit, match="0"):
        parser.parse_args(["convert", "--help"])
    assert "numerically convert" in capsys.readouterr().out


def test_code_fields_are_dispatched_and_unmatched_channel_is_unchanged(
    cli_files: CliFiles, run_cli: Callable[..., str]
) -> None:
    """Verify each code field updates the selected channel without touching others."""
    values = {
        "main_location": "ABCD",
        "fine_location_1": "AA",
        "fine_location_2": "BB",
        "fine_location_3": "CC",
        "physical_dimension": "DD",
        "direction": "R",
        "filter_class": "X",
        "position": "2",
        "test_object": "2",
    }
    for field, value in values.items():
        pattern = "12*" if field == "test_object" else "11*"
        run_cli("set", str(cli_files.mme), field, value, "-c", pattern)

    result = Isomme().read(cli_files.mme)
    changed = result.get_channel(
        "22ABCDAABBCCDDRX",
        filter=False,
        calculate=False,
        differentiate=False,
        integrate=False,
    )
    assert changed is not None
    assert (
        result.get_channel(
            "13CHST000000DSXP",
            filter=False,
            calculate=False,
            differentiate=False,
            integrate=False,
        )
    ) is not None
    assert set(values) == set(CODE_FIELDS)


def test_multiple_patterns_relabel_units_without_converting_values(
    cli_files: CliFiles, run_cli: Callable[..., str]
) -> None:
    """Ensure set relabels every matching unit while preserving signal values."""
    before = {
        str(channel.code): channel.get_data().copy()
        for channel in Isomme().read(cli_files.mme).channels
    }
    output = run_cli("set", str(cli_files.mme), "unit", "um", "-c", "11*", "13CHST*")

    result = Isomme().read(cli_files.mme)
    assert str(required_channel(result, "11*").unit) == "um"
    assert str(required_channel(result, "13CHST*").unit) == "um"
    assert str(required_channel(result, "14*").unit) == "g0"
    for channel in result.channels:
        np.testing.assert_array_equal(channel.get_data(), before[str(channel.code)])
    assert "Matched 2 channel(s); changed 2." in output

    output = run_cli("set", str(cli_files.mme), "unit", "um", "-c", "11*", "13CHST*")
    assert "Matched 2 channel(s); changed 0." in output


def test_round_trip_updates_chn_and_channel_header(
    cli_files: CliFiles, run_cli: Callable[..., str]
) -> None:
    """Ensure code changes are persisted in both ISO-MME channel metadata files."""
    run_cli("set", str(cli_files.mme), "fine_location_3", "H3", "-c", "13CHST*")
    chn = (cli_files.root / "Channel" / "CLI.chn").read_text()
    channel_headers = "\n".join(
        path.read_text() for path in (cli_files.root / "Channel").glob("CLI.0??")
    )
    assert "13CHST0000H3DSXP" in chn
    assert "13CHST0000H3DSXP" in channel_headers


def test_set_accepts_multiple_input_paths(
    cli_files: CliFiles, run_cli: Callable[..., str]
) -> None:
    """Ensure set applies the requested change to every input container."""
    output = run_cli(
        "set",
        str(cli_files.mme),
        str(cli_files.second_mme),
        "fine_location_3",
        "H3",
        "-c",
        "13CHST*",
    )
    for path in (cli_files.mme, cli_files.second_mme):
        result = Isomme().read(path)
        assert (
            result.get_channel(
                "13CHST0000H3DSXP",
                filter=False,
                calculate=False,
                differentiate=False,
                integrate=False,
            )
        ) is not None
        assert str(path) in output


def test_convert_unit_accepts_multiple_inputs_and_converts_values(
    cli_files: CliFiles, run_cli: Callable[..., str]
) -> None:
    """Ensure convert changes units and numeric values across all input containers."""
    before = []
    for path in (cli_files.mme, cli_files.second_mme):
        channel = required_channel(Isomme().read(path), "13CHST*")
        before.append(channel.get_data().copy())

    output = run_cli(
        "convert",
        str(cli_files.mme),
        str(cli_files.second_mme),
        "unit",
        "mm",
        "-c",
        "13CHST*",
    )
    for path, old_data in zip((cli_files.mme, cli_files.second_mme), before):
        result = Isomme().read(path)
        channel = required_channel(result, "13CHST*")
        assert str(channel.unit) == "mm"
        np.testing.assert_allclose(channel.get_data(), old_data * 1000.0)
        assert str(required_channel(result, "11*").unit) == "g0"
    assert output.count("Matched 1 channel(s); changed 1.") == 2

    output = run_cli(
        "convert",
        str(cli_files.mme),
        str(cli_files.second_mme),
        "unit",
        "mm",
        "-c",
        "13CHST*",
    )
    assert output.count("Matched 1 channel(s); changed 0.") == 2


def test_incompatible_conversion_in_later_input_prevents_all_writes(
    cli_files: CliFiles, capsys: pytest.CaptureFixture[str]
) -> None:
    """Ensure a failed multi-input conversion leaves every input unchanged."""
    second = Isomme().read(cli_files.second_mme)
    required_channel(second, "13CHST*").set_unit("s")
    second.write(cli_files.second_mme)
    before = snapshot(cli_files.root)

    with pytest.raises(SystemExit, match="2"):
        main(
            [
                "convert",
                str(cli_files.mme),
                str(cli_files.second_mme),
                "unit",
                "mm",
                "-c",
                "13CHST*",
            ]
        )
    capsys.readouterr()
    assert snapshot(cli_files.root) == before


@pytest.mark.parametrize(
    ("field", "value", "pattern"),
    [
        ("fine_location_3", "H3", "99*"),
        ("fine_location_3", "TOO-LONG", "11*"),
        ("unit", "not_a_unit", "11*"),
    ],
)
def test_no_match_and_invalid_value_do_not_write(
    cli_files: CliFiles,
    capsys: pytest.CaptureFixture[str],
    field: str,
    value: str,
    pattern: str,
) -> None:
    """Ensure unmatched or invalid set requests fail before writing any files."""
    before = snapshot(cli_files.root)
    with pytest.raises(SystemExit, match="2"):
        main(["set", str(cli_files.mme), field, value, "-c", pattern])
    capsys.readouterr()
    assert snapshot(cli_files.root) == before


def test_individual_channel_file_is_rejected_before_reading(
    cli_files: CliFiles, capsys: pytest.CaptureFixture[str]
) -> None:
    """Ensure set rejects a channel data file before attempting an unsafe write."""
    xxx_path = cli_files.root / "Channel" / "CLI.001"
    before = snapshot(cli_files.root)
    with pytest.raises(SystemExit, match="2"):
        main(["set", str(xxx_path), "unit", "um", "-c", "*"])
    assert "Cannot write ISO-MME back" in capsys.readouterr().err
    assert snapshot(cli_files.root) == before
