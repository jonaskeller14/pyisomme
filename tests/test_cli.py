from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import pyisomme.__main__ as cli
from pyisomme.channel import Channel
from pyisomme.code import CODE_COMPONENTS
from pyisomme.isomme import Isomme
from pyisomme.report import REPORTS


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
            Channel("11HEAD000000ACXP", pd.DataFrame([1.0, 2.0, 3.0], index=time), "g"),
            Channel(
                "13CHST000000DSXP",
                pd.DataFrame(np.array([4.0, 5.0, 6.0]) * scale, index=time),
                "m",
            ),
            Channel("14HEAD000000ACXP", pd.DataFrame([7.0, 8.0, 9.0], index=time), "g"),
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
        cli.main(list(arguments))
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


def test_top_level_help_and_subcommands_are_exposed(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit, match="0"):
        cli.main(["--help"])
    help_text = capsys.readouterr().out
    assert "Read, modify, plot, and report" in help_text
    for command in ("code", "convert", "list", "merge", "plot", "report", "set"):
        assert command in help_text

    with pytest.raises(SystemExit, match="0"):
        cli.main(["set", "--help"])
    set_help = capsys.readouterr().out
    assert "--dry-run" in set_help
    assert "--main-location" in set_help
    assert "characters 3-6" in set_help

    with pytest.raises(SystemExit, match="0"):
        cli.main(["convert", "--help"])
    assert "required --unit option" in capsys.readouterr().out


def test_every_subcommand_is_parsed_and_dispatched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def record(name: str) -> Callable[..., None]:
        def handler(*args: object, **kwargs: object) -> None:
            calls.append(name)

        return handler

    for command in ("list", "merge", "set", "convert", "report"):
        monkeypatch.setattr(cli, f"execute_{command}_command", record(command))
    monkeypatch.setattr(cli, "execute_code_command", record("code"))
    monkeypatch.setattr(cli, "execute_plot_command", record("plot"))

    report_name = REPORTS[0].__name__
    for invocation in (
        ["list", "input.mme"],
        ["code", "11HEAD000000ACXP"],
        ["merge", "output.mme", "input.mme"],
        ["set", "input.mme", "--unit", "g", "-c", "11*"],
        ["convert", "input.mme", "--unit", "g", "-c", "11*"],
        ["report", report_name, "report.pptx", "input.mme"],
        ["plot", "input.mme", "-c", "11*"],
    ):
        cli.main(invocation)

    assert calls == ["list", "code", "merge", "set", "convert", "report", "plot"]


def test_code_command_describes_channel_code(run_cli: Callable[..., str]) -> None:
    output = run_cli("code", "11HEAD0000H3ACXA")
    assert "Code: 11HEAD0000H3ACXA" in output
    assert "Main Location:" in output
    assert "Default unit:" in output


def test_list_command_filters_channel_codes(
    cli_files: CliFiles, run_cli: Callable[..., str]
) -> None:
    output = run_cli("list", str(cli_files.mme), "-c", "13CHST*")
    assert "CLI" in output
    assert "13CHST000000DSXP" in output
    assert "11HEAD000000ACXP" not in output


def test_set_updates_multiple_metadata_fields_and_relabels_units(
    cli_files: CliFiles, run_cli: Callable[..., str]
) -> None:
    before = required_channel(Isomme().read(cli_files.mme), "11*").get_data().copy()
    output = run_cli(
        "set",
        str(cli_files.mme),
        "--test-object",
        "2",
        "--position",
        "2",
        "--main-location",
        "ABCD",
        "--fine-location-1",
        "AA",
        "--fine-location-2",
        "BB",
        "--fine-location-3",
        "CC",
        "--physical-dimension",
        "DD",
        "--direction",
        "R",
        "--filter-class",
        "X",
        "--unit",
        "um",
        "-c",
        "11*",
    )
    channel = required_channel(Isomme().read(cli_files.mme), "22ABCDAABBCCDDRX")
    assert str(channel.unit) == "um"
    np.testing.assert_array_equal(channel.get_data(), before)
    assert "[g0] 11HEAD000000ACXP -> 22ABCDAABBCCDDRX [um]" in output
    assert {name for name, _ in CODE_COMPONENTS} == {
        "test_object",
        "position",
        "main_location",
        "fine_location_1",
        "fine_location_2",
        "fine_location_3",
        "physical_dimension",
        "direction",
        "filter_class",
    }


def test_set_dry_run_does_not_write(
    cli_files: CliFiles, run_cli: Callable[..., str]
) -> None:
    before = snapshot(cli_files.root)
    output = run_cli(
        "set",
        str(cli_files.mme),
        "--fine-location-3",
        "H3",
        "-c",
        "13CHST*",
        "--dry-run",
    )
    assert snapshot(cli_files.root) == before
    assert "Dry run: no files were written." in output


def test_convert_converts_values_across_multiple_inputs(
    cli_files: CliFiles, run_cli: Callable[..., str]
) -> None:
    before = [
        required_channel(Isomme().read(path), "13CHST*").get_data().copy()
        for path in (cli_files.mme, cli_files.second_mme)
    ]
    output = run_cli(
        "convert",
        str(cli_files.mme),
        str(cli_files.second_mme),
        "--unit",
        "mm",
        "-c",
        "13CHST*",
    )
    for path, old_data in zip((cli_files.mme, cli_files.second_mme), before):
        channel = required_channel(Isomme().read(path), "13CHST*")
        assert str(channel.unit) == "mm"
        np.testing.assert_allclose(channel.get_data(), old_data * 1000.0)
    assert output.count("13CHST000000DSXP:") == 2


def test_convert_dry_run_does_not_write(
    cli_files: CliFiles, run_cli: Callable[..., str]
) -> None:
    before = snapshot(cli_files.root)
    output = run_cli(
        "convert", str(cli_files.mme), "--unit", "mm", "-c", "13CHST*", "--dry-run"
    )
    assert snapshot(cli_files.root) == before
    assert "Dry run: no files were written." in output
