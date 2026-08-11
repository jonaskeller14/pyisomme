from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from pyisomme.channel import Channel
from pyisomme.isomme import Isomme
from pyisomme.__main__ import CODE_FIELDS, build_parser, main


class TestCLI(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.mme_path = self.root / "CLI.mme"
        self.second_root = self.root / "second"
        self.second_root.mkdir()
        self.second_mme_path = self.second_root / "CLI2.mme"
        time = np.array([0.0, 0.001, 0.002])

        def fixture(test_number: str, scale: float) -> Isomme:
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

        fixture("CLI", 1.0).write(self.mme_path)
        fixture("CLI2", 2.0).write(self.second_mme_path)

    def snapshot(self) -> dict[str, bytes]:
        return {
            str(path.relative_to(self.root)): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file()
        }

    def run_cli(self, *arguments: str) -> str:
        output = StringIO()
        with redirect_stdout(output):
            main(list(arguments))
        return output.getvalue()

    def test_help_exposes_set_convert_and_all_fields(self) -> None:
        parser = build_parser()
        output = StringIO()
        with self.assertRaisesRegex(SystemExit, "0"), redirect_stdout(output):
            parser.parse_args(["set", "--help"])
        help_text = output.getvalue()
        self.assertIn("Quote wildcard patterns", help_text)
        for field in ("unit", *CODE_FIELDS):
            self.assertIn(field, help_text)
        output = StringIO()
        with self.assertRaisesRegex(SystemExit, "0"), redirect_stdout(output):
            parser.parse_args(["convert", "--help"])
        self.assertIn("numerically convert", output.getvalue())

    def test_code_fields_are_dispatched_and_unmatched_channel_is_unchanged(
        self,
    ) -> None:
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
            self.run_cli("set", str(self.mme_path), field, value, "-c", pattern)

        result = Isomme().read(self.mme_path)
        changed = result.get_channel(
            "22ABCDAABBCCDDRX",
            filter=False,
            calculate=False,
            differentiate=False,
            integrate=False,
        )
        self.assertIsNotNone(changed)
        self.assertIsNotNone(
            result.get_channel(
                "13CHST000000DSXP",
                filter=False,
                calculate=False,
                differentiate=False,
                integrate=False,
            )
        )
        self.assertEqual(set(values), set(CODE_FIELDS))

    def test_multiple_patterns_relabel_units_without_converting_values(self) -> None:
        before = {
            str(channel.code): channel.get_data().copy()
            for channel in Isomme().read(self.mme_path).channels
        }
        output = self.run_cli(
            "set", str(self.mme_path), "unit", "um", "-c", "11*", "13CHST*"
        )

        result = Isomme().read(self.mme_path)
        self.assertEqual(str(result.get_channel("11*").unit), "um")
        self.assertEqual(str(result.get_channel("13CHST*").unit), "um")
        self.assertEqual(str(result.get_channel("14*").unit), "g0")
        for channel in result.channels:
            np.testing.assert_array_equal(channel.get_data(), before[str(channel.code)])
        self.assertIn("Matched 2 channel(s); changed 2.", output)

        output = self.run_cli(
            "set", str(self.mme_path), "unit", "um", "-c", "11*", "13CHST*"
        )
        self.assertIn("Matched 2 channel(s); changed 0.", output)

    def test_round_trip_updates_chn_and_channel_header(self) -> None:
        self.run_cli(
            "set", str(self.mme_path), "fine_location_3", "H3", "-c", "13CHST*"
        )
        chn = (self.root / "Channel" / "CLI.chn").read_text()
        channel_headers = "\n".join(
            path.read_text() for path in (self.root / "Channel").glob("CLI.0??")
        )
        self.assertIn("13CHST0000H3DSXP", chn)
        self.assertIn("13CHST0000H3DSXP", channel_headers)

    def test_set_accepts_multiple_input_paths(self) -> None:
        output = self.run_cli(
            "set",
            str(self.mme_path),
            str(self.second_mme_path),
            "fine_location_3",
            "H3",
            "-c",
            "13CHST*",
        )
        for path in (self.mme_path, self.second_mme_path):
            result = Isomme().read(path)
            self.assertIsNotNone(
                result.get_channel(
                    "13CHST0000H3DSXP",
                    filter=False,
                    calculate=False,
                    differentiate=False,
                    integrate=False,
                )
            )
            self.assertIn(str(path), output)

    def test_convert_unit_accepts_multiple_inputs_and_converts_values(self) -> None:
        before = []
        for path in (self.mme_path, self.second_mme_path):
            channel = Isomme().read(path).get_channel("13CHST*")
            before.append(channel.get_data().copy())

        output = self.run_cli(
            "convert",
            str(self.mme_path),
            str(self.second_mme_path),
            "unit",
            "mm",
            "-c",
            "13CHST*",
        )
        for path, old_data in zip((self.mme_path, self.second_mme_path), before):
            result = Isomme().read(path)
            channel = result.get_channel("13CHST*")
            self.assertEqual(str(channel.unit), "mm")
            np.testing.assert_allclose(channel.get_data(), old_data * 1000.0)
            self.assertEqual(str(result.get_channel("11*").unit), "g0")
        self.assertEqual(output.count("Matched 1 channel(s); changed 1."), 2)

        output = self.run_cli(
            "convert",
            str(self.mme_path),
            str(self.second_mme_path),
            "unit",
            "mm",
            "-c",
            "13CHST*",
        )
        self.assertEqual(output.count("Matched 1 channel(s); changed 0."), 2)

    def test_incompatible_conversion_in_later_input_prevents_all_writes(self) -> None:
        second = Isomme().read(self.second_mme_path)
        second.get_channel("13CHST*").set_unit("s")
        second.write(self.second_mme_path)
        before = self.snapshot()

        with self.assertRaisesRegex(SystemExit, "2"), redirect_stderr(StringIO()):
            main(
                [
                    "convert",
                    str(self.mme_path),
                    str(self.second_mme_path),
                    "unit",
                    "mm",
                    "-c",
                    "13CHST*",
                ]
            )
        self.assertEqual(self.snapshot(), before)

    def test_no_match_and_invalid_value_do_not_write(self) -> None:
        for arguments in (
            ("fine_location_3", "H3", "-c", "99*"),
            ("fine_location_3", "TOO-LONG", "-c", "11*"),
            ("unit", "not_a_unit", "-c", "11*"),
        ):
            with self.subTest(arguments=arguments):
                before = self.snapshot()
                with (
                    self.assertRaisesRegex(SystemExit, "2"),
                    redirect_stderr(StringIO()),
                ):
                    main(["set", str(self.mme_path), *arguments])
                self.assertEqual(self.snapshot(), before)

    def test_individual_channel_file_is_rejected_before_reading(self) -> None:
        xxx_path = self.root / "Channel" / "CLI.001"
        before = self.snapshot()
        error = StringIO()
        with self.assertRaisesRegex(SystemExit, "2"), redirect_stderr(error):
            main(["set", str(xxx_path), "unit", "um", "-c", "*"])
        self.assertIn("Cannot write ISO-MME back", error.getvalue())
        self.assertEqual(self.snapshot(), before)


class TestMetadataRepairScripts(unittest.TestCase):
    EXPECTED = {
        "09203": (("21*", "TH"), ("24*", "H3")),
        "11391": (("11*", "H3"), ("13*", "H3")),
        "14084": (("11*", "H3"), ("13*", "HF")),
    }

    def test_scripts_use_expected_mappings_and_quoted_patterns(self) -> None:
        repository = Path(__file__).parents[1]
        for test_number, mappings in self.EXPECTED.items():
            with self.subTest(test_number=test_number):
                script = (
                    repository
                    / "data"
                    / "nhtsa"
                    / test_number
                    / "fix_channel_metadata.sh"
                ).read_text()
                for pattern, dummy in mappings:
                    self.assertIn(f"fine_location_3 {dummy} -c '{pattern}'", script)
                self.assertIn("unit um -c '??CHST??????DS??'", script)


if __name__ == "__main__":
    unittest.main()
