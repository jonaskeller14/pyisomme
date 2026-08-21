import logging
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest

import pyisomme
from pyisomme.errors import MalformedFileError
from pyisomme.parsing import (
    get_normalization_notes,
    parse_mme,
    parse_xxx,
    resolve_time_axis,
)
from pyisomme.sources import read_text_with_fallback

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(module)-12s %(levelname)-8s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S",
    level=logging.WARNING,
)


FIXTURES = Path(__file__).parent.parent / "data" / "tests"

#: Every fixture encodes the *same* container; only the header text differs. See the module
#: docstring of the generator for what each encoding is meant to exercise.
N_SAMPLES = 20
SAMPLING_INTERVAL = 0.0001
TIME_OF_FIRST_SAMPLE = -0.0005
TIMES = [TIME_OF_FIRST_SAMPLE + i * SAMPLING_INTERVAL for i in range(N_SAMPLES)]
DROPPED_SAMPLE_IDX = 12  # the one ``NOVALUE`` in the chest channel


@dataclass(frozen=True)
class EncodingData:
    fixture_name: str
    laboratory: str
    customer: str
    comments: list[str]
    head_channel_name: str
    chest_channel_name: str


ENCODINGS = [
    EncodingData(
        "ascii",
        "MGA Research Corporation",
        "NHTSA / Office of Vehicle Safety Compliance",
        [
            "Time zero: first contact with the barrier face",
            "Chest deflection channel: IR-TRACC, 50 % ile Hybrid III",
        ],
        "Head CG X acceleration",
        "Chest deflection X (IR-TRACC)",
    ),
    EncodingData(
        "iso-8859-1",
        "Crash-Prüfzentrum Köln GmbH",
        "Société Automobile Française S.A.",
        [
            "Meßunsicherheit ±0,5 %; Prüftemperatur 22 °C",
            "Dummy: Hybrid III 50 %, Sitzposition vorne links",
        ],
        "Kopf-Schwerpunkt Beschleunigung X",
        "Brustkorb-Eindrückung X (µm)",
    ),
    EncodingData(
        "windows-1252",
        "Crash-Prüfzentrum Köln GmbH",
        "Renault S.A. — Direction de la Sécurité",
        [
            "Prüfkosten 25.000 €; Bericht „Nr. 4711“ …",
            "Sensorik: Kistler™ – Drift ±0,5 % nachgeprüft",
        ],
        "Kopf-Schwerpunkt Beschleunigung X",
        "Brustkorb-Eindrückung X (µm)",
    ),
    EncodingData(
        "utf-8",
        "Crash-Prüfzentrum Köln GmbH",
        "トヨタ自動車株式会社 (Toyota Motor Corp.)",
        [
            "Δv = 56,3 km/h → Pulsdauer 78 ms; Prüftemperatur 22 °C",
            "Brückenimpedanz 50 Ω; Meßunsicherheit ±0,5 % …",
        ],
        "Kopf-Schwerpunkt Beschleunigung X",
        "Brustkorb-Eindrückung X (µm)",
    ),
]


class TestEncodingContainer:
    """
    Assertions shared by every encoding fixture.

    Split into a *structure* part, identical for all four encodings because they encode
    the same container, and a *text* part naming the exact non-ASCII strings that must
    survive decoding. Asserting the text matters: a container full of mojibake still
    reads without error, so a non-emptiness check alone would not notice a broken codec.
    """

    def read_fixture(self, encoding_data, suffix=""):
        return pyisomme.Isomme().read(FIXTURES / (encoding_data.fixture_name + suffix))

        # -- structure -----------------------------------------------------------------

    def check_structure(self, isomme):
        assert isomme.test_number == "test"
        assert len(isomme.test_info) != 0
        assert len(isomme.channel_info) != 0
        assert [channel.code for channel in isomme.channels] == [
            "11TIRS000000TIRP",
            "11HEADCG0000ACXP",
            "11CHST0000H3DSXP",
        ]
        for channel in isomme.channels:
            assert len(channel.info) != 0

    def check_header_values(self, isomme):
        # A value containing colons must not be split at the second one.
        assert isomme.get_test_info("Time of test") == "10:32:45"
        # Empty value and explicit NOVALUE both mean "absent".
        assert isomme.get_test_info("Regulation") is None
        assert isomme.get_test_info("Client test ref number") is None
        # Tab-padded keyword, and a value with trailing whitespace.
        assert isomme.get_test_info("Movie reference") is None
        assert isomme.get_test_info("Test performed by") == "Crash Team 3"
        # Typed values.
        assert isomme.get_test_info("Impact velocity") == 56.3
        assert isomme.get_test_info("Number of test objects") == 1

    def check_channels(self, isomme):
        tirs, head, chest = isomme.channels

        # Time-reference channel: no timing header at all, so it keeps the sample index
        # - the canonical shape for TIRS, and therefore not flagged as an assumption.
        np.testing.assert_array_equal(tirs.data.index, np.arange(N_SAMPLES))
        np.testing.assert_allclose(tirs.get_data(), TIMES)
        assert get_normalization_notes(tirs) == []

        # Declared 'explicit': the time axis is read out of the referenced TIRS channel.
        np.testing.assert_allclose(head.data.index, TIMES)
        assert get_normalization_notes(head) == []
        assert str(head.unit) == "g0"
        # rtol is loosened because the files store samples at 7 significant digits,
        # the precision real ISO-MME writers use.
        np.testing.assert_allclose(
            head.get_data(),
            [0.0 if t < 0 else 42.0 * math.sin(math.pi * t / 0.0020) for t in TIMES],
            rtol=1e-6,
        )

        # Declared 'implicit': the axis is rebuilt from first sample + interval.
        np.testing.assert_allclose(chest.data.index, TIMES)
        assert get_normalization_notes(chest) == []
        assert str(chest.unit) == "um"
        values = chest.get_data()
        assert int(np.isnan(values).sum()) == 1
        assert np.isnan(values[DROPPED_SAMPLE_IDX]), "NOVALUE must become NaN"
        assert values[0] == 0.0
        # A colon inside a channel-header value, same trap as in the .mme.
        assert [v for k, v in chest.info if k == "Comments"] == [
            "IR-TRACC, calibrated 2026-04-02: drift within tolerance"
        ]

    # -- text ----------------------------------------------------------------------

    def check_text(self, isomme, encoding_data):
        assert isomme.get_test_info("Laboratory name") == encoding_data.laboratory
        assert isomme.get_test_info("Customer name") == encoding_data.customer
        assert [
            v for k, v in isomme.test_info if k == "Comments"
        ] == encoding_data.comments
        _, head, chest = isomme.channels
        assert head.get_info("Name of the channel") == encoding_data.head_channel_name
        assert chest.get_info("Name of the channel") == encoding_data.chest_channel_name

    # -- the two tests every fixture runs -------------------------------------------

    def check_all(self, isomme, encoding_data):
        self.check_structure(isomme)
        self.check_header_values(isomme)
        self.check_channels(isomme)
        self.check_text(isomme, encoding_data)

    @pytest.mark.parametrize(
        "encoding_data",
        ENCODINGS,
        ids=lambda encoding_data: encoding_data.fixture_name,
    )
    def test_folder(self, encoding_data):
        self.check_all(self.read_fixture(encoding_data), encoding_data)

    @pytest.mark.parametrize(
        "encoding_data",
        ENCODINGS,
        ids=lambda encoding_data: encoding_data.fixture_name,
    )
    def test_zip(self, encoding_data):
        self.check_all(self.read_fixture(encoding_data, ".zip"), encoding_data)

    @pytest.mark.parametrize("encoding_data", [ENCODINGS[-1]], ids=["utf-8"])
    def test_bom_does_not_leak_into_the_first_keyword(self, encoding_data):
        raw = (FIXTURES / encoding_data.fixture_name / "test.mme").read_bytes()
        assert raw.startswith(b"\xef\xbb\xbf"), "fixture must carry a UTF-8 BOM"
        isomme = self.read_fixture(encoding_data)
        assert isomme.test_info.keys()[0] == "Data format"
        assert isomme.get_test_info("Data format") == "ISO-MME"


class TestEncodingFallback:
    """Fixture-free tests for :func:`read_text_with_fallback`."""

    # The redundant "utf-8" arguments below are spelled out on purpose: in a test about
    # which codec is chosen, leaving the codec implicit would defeat the point.

    def test_utf_8_is_preferred(self):
        text = "Prüfstand Ω"
        assert read_text_with_fallback(text.encode("utf-8")) == text  # noqa: UP012

    def test_utf_8_bom_is_stripped(self):
        raw = "﻿Test number:1".encode("utf-8")  # noqa: UP012
        assert read_text_with_fallback(raw) == "Test number:1"

    def test_windows_1252_specials_survive(self):
        text = "25.000 € „Nr. 4711“ … Kistler™ – ±0,5 %"
        assert read_text_with_fallback(text.encode("cp1252")) == text

    def test_windows_1252_ellipsis_does_not_become_a_line_break(self):
        # 0x85 decoded as ISO-8859-1 is U+0085 NEL, which str.splitlines() splits on.
        decoded = read_text_with_fallback("Comments :a … b".encode("cp1252"))
        assert len(decoded.splitlines()) == 1

    def test_bytes_undefined_in_cp1252_fall_through_to_iso_8859_1(self):
        # 0x81, 0x8D, 0x8F, 0x90 and 0x9D have no cp1252 mapping; ISO-8859-1 takes anything.
        raw = b"Lab \x81\x8d\x8f\x90\x9d name"
        assert read_text_with_fallback(raw) == raw.decode("iso-8859-1")

    def test_utf_16_is_detected_by_its_bom(self):
        # UTF-16 ASCII text is NUL-interleaved, which is *valid* UTF-8 - without the BOM
        # check it would decode silently into garbage instead of raising.
        text = "Test number:1"
        for bom_encoding in ("utf-16-le", "utf-16-be"):
            raw = ("﻿" + text).encode(bom_encoding)
            assert read_text_with_fallback(raw) == text

    def test_never_raises_on_arbitrary_bytes(self):
        assert isinstance(read_text_with_fallback(bytes(range(256))), str)


class TestHeaderLineSplitting:
    """The keyword/value split, which several realistic values used to break."""

    def test_value_containing_a_colon_is_kept_whole(self):
        info = parse_mme("Comments                    :Dummy: Hybrid III 50 %")
        assert info.keys() == ["Comments"]
        assert info["Comments"] == "Dummy: Hybrid III 50 %"

    def test_timestamp_value_is_kept_whole(self):
        info = parse_mme("Time of test                :10:32:45")
        assert info["Time of test"] == "10:32:45"

    def test_tab_padding_is_stripped_from_the_keyword(self):
        info = parse_mme("Movie reference\t\t:NOVALUE")
        assert info.keys() == ["Movie reference"]
        assert info["Movie reference"] is None

    def test_duplicate_keywords_are_all_kept(self):
        info = parse_mme(
            "Comments                    :first\nComments                    :second"
        )
        assert [v for k, v in info if k == "Comments"] == ["first", "second"]

    def test_line_without_colon_is_reported_not_parsed(self, caplog):
        with caplog.at_level(logging.ERROR, logger="pyisomme.parsing"):
            info = parse_mme("this line has no separator")
        assert len(info) == 0


class TestTimeAxisNormalization:
    """Fixture-free tests for the ingest normalization boundary in ``parse_xxx``."""

    @staticmethod
    def _channel_text(header_lines, data_values):
        return "\n".join(list(header_lines) + [str(v) for v in data_values])

    def test_declared_implicit_reconstructs_time_axis(self):
        text = self._channel_text(
            [
                "Channel code                :11HEADCG0000ACXP",
                "Reference channel           :implicit",
                "Time of first sample        :-0.05",
                "Sampling interval           :0.01",
            ],
            [0.0, 1.0, 2.0, 3.0],
        )
        channel = parse_xxx(text, pyisomme.Isomme())
        # 4 samples from -0.05 with step 0.01 -> last sample at -0.05 + 3*0.01 = -0.02
        np.testing.assert_allclose(channel.data.index, [-0.05, -0.04, -0.03, -0.02])
        # Fully specified -> no assumption recorded.
        assert get_normalization_notes(channel) == []

    def test_assumed_implicit_records_note_and_uses_correct_endpoint(self):
        text = self._channel_text(
            [
                "Channel code                :11HEADCG0000ACXP",
                "Time of first sample        :0.0",
                "Sampling interval           :0.01",
            ],
            [0.0, 1.0, 2.0, 3.0],
        )
        channel = parse_xxx(text, pyisomme.Isomme())
        # step stays 0.01 (last sample 0.03), not the old n*dt=0.04 endpoint bug.
        np.testing.assert_allclose(channel.data.index, [0.0, 0.01, 0.02, 0.03])
        assert len(get_normalization_notes(channel)) == 1

    def test_sampling_interval_only_assumes_time_zero(self):
        text = self._channel_text(
            [
                "Channel code                :11HEADCG0000ACXP",
                "Sampling interval           :0.01",
            ],
            [0.0, 1.0, 2.0],
        )
        channel = parse_xxx(text, pyisomme.Isomme())
        np.testing.assert_allclose(channel.data.index, [0.0, 0.01, 0.02])
        assert "Time of first sample" in get_normalization_notes(channel)[0]

    def test_no_timing_non_tirs_falls_back_to_sample_index_with_note(self):
        text = self._channel_text(
            ["Channel code                :11HEADCG0000ACXP"],
            [10.0, 11.0, 12.0],
        )
        channel = parse_xxx(text, pyisomme.Isomme())
        np.testing.assert_array_equal(channel.data.index, [0, 1, 2])
        assert len(get_normalization_notes(channel)) == 1

    def test_tirs_channel_uses_sample_index_without_note(self):
        text = self._channel_text(
            ["Channel code                :11TIRS000000TIRP"],
            [0.0, 1.0, 2.0],
        )
        channel = parse_xxx(text, pyisomme.Isomme())
        np.testing.assert_array_equal(channel.data.index, [0, 1, 2])
        # Sample index is the expected shape for a time-reference channel -> not flagged.
        assert get_normalization_notes(channel) == []

    def test_non_numeric_data_raises_malformed_file_error(self):
        text = self._channel_text(
            [
                "Channel code                :11HEADCG0000ACXP",
                "Sampling interval           :0.01",
            ],
            ["not_a_number", 1.0],
        )
        with pytest.raises(MalformedFileError):
            parse_xxx(text, pyisomme.Isomme())

    def test_note_recorded_in_standard_comments_field_without_clobbering(self):
        text = self._channel_text(
            [
                "Channel code                :11HEADCG0000ACXP",
                "Comments                    :DRIVER HEAD CG X ACCELERATION",
                "Sampling interval           :0.01",
            ],
            [0.0, 1.0, 2.0],
        )
        channel = parse_xxx(text, pyisomme.Isomme())
        comments = [v for k, v in channel.info if k == "Comments"]
        # Authored comment preserved; normalization note appended as a second Comments line.
        assert "DRIVER HEAD CG X ACCELERATION" in comments
        assert len(get_normalization_notes(channel)) == 1

    def test_resolve_time_axis_returns_note_for_undeclared_convention(self):
        info = pyisomme.Info([("Sampling interval", 0.01)])
        index, note = resolve_time_axis(info, 3, pyisomme.Isomme())
        assert index is not None
        assert note is not None
