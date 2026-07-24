import pyisomme
from pyisomme.errors import MalformedFileError
from pyisomme.parsing import parse_xxx, resolve_time_axis, get_normalization_notes

import unittest
import os
import logging
import numpy as np


logger = logging.getLogger(__name__)
logging.basicConfig(format='%(module)-12s %(levelname)-8s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S', level=logging.WARNING)


class TestParsing(unittest.TestCase):
    def check_if_isomme_not_empty(self, isomme):
        logger.info(isomme.test_info)
        logger.info(isomme.channel_info)
        logger.info(isomme.channels)
        logger.info(isomme.channels[0].info)
        assert len(isomme.test_info) != 0
        assert len(isomme.channel_info) != 0
        assert len(isomme.channels) != 0
        assert len(isomme.channels[0].info) != 0

    def test_utf_8(self):
        isomme = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "utf-8"))
        self.check_if_isomme_not_empty(isomme)

    def test_ascii(self):
        isomme = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "ascii"))
        self.check_if_isomme_not_empty(isomme)

    def test_windows_1252(self):
        isomme = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "windows-1252"))
        self.check_if_isomme_not_empty(isomme)

    def test_iso_8859_1(self):
        isomme = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "iso-8859-1"))
        self.check_if_isomme_not_empty(isomme)

    def test_utf_8_zip(self):
        isomme = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "utf-8.zip"))
        self.check_if_isomme_not_empty(isomme)

    def test_ascii_zip(self):
        isomme = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "ascii.zip"))
        self.check_if_isomme_not_empty(isomme)

    def test_windows_1252_zip(self):
        isomme = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "windows-1252.zip"))
        self.check_if_isomme_not_empty(isomme)

    def test_iso_8859_1_zip(self):
        isomme = pyisomme.Isomme().read(os.path.join(__file__, "..", "..", "data", "tests", "iso-8859-1.zip"))
        self.check_if_isomme_not_empty(isomme)


class TestTimeAxisNormalization(unittest.TestCase):
    """Fixture-free tests for the ingest normalization boundary in ``parse_xxx``."""

    @staticmethod
    def _channel_text(header_lines, data_values):
        return "\n".join(list(header_lines) + [str(v) for v in data_values])

    def test_declared_implicit_reconstructs_time_axis(self):
        text = self._channel_text(
            ["Channel code                :11HEADCG0000ACXP",
             "Reference channel           :implicit",
             "Time of first sample        :-0.05",
             "Sampling interval           :0.01"],
            [0.0, 1.0, 2.0, 3.0],
        )
        channel = parse_xxx(text, pyisomme.Isomme())
        # 4 samples from -0.05 with step 0.01 -> last sample at -0.05 + 3*0.01 = -0.02
        np.testing.assert_allclose(channel.data.index, [-0.05, -0.04, -0.03, -0.02])
        # Fully specified -> no assumption recorded.
        self.assertEqual(get_normalization_notes(channel), [])

    def test_assumed_implicit_records_note_and_uses_correct_endpoint(self):
        text = self._channel_text(
            ["Channel code                :11HEADCG0000ACXP",
             "Time of first sample        :0.0",
             "Sampling interval           :0.01"],
            [0.0, 1.0, 2.0, 3.0],
        )
        channel = parse_xxx(text, pyisomme.Isomme())
        # step stays 0.01 (last sample 0.03), not the old n*dt=0.04 endpoint bug.
        np.testing.assert_allclose(channel.data.index, [0.0, 0.01, 0.02, 0.03])
        self.assertEqual(len(get_normalization_notes(channel)), 1)

    def test_sampling_interval_only_assumes_time_zero(self):
        text = self._channel_text(
            ["Channel code                :11HEADCG0000ACXP",
             "Sampling interval           :0.01"],
            [0.0, 1.0, 2.0],
        )
        channel = parse_xxx(text, pyisomme.Isomme())
        np.testing.assert_allclose(channel.data.index, [0.0, 0.01, 0.02])
        self.assertIn("Time of first sample", get_normalization_notes(channel)[0])

    def test_no_timing_non_tirs_falls_back_to_sample_index_with_note(self):
        text = self._channel_text(
            ["Channel code                :11HEADCG0000ACXP"],
            [10.0, 11.0, 12.0],
        )
        channel = parse_xxx(text, pyisomme.Isomme())
        np.testing.assert_array_equal(channel.data.index, [0, 1, 2])
        self.assertEqual(len(get_normalization_notes(channel)), 1)

    def test_tirs_channel_uses_sample_index_without_note(self):
        text = self._channel_text(
            ["Channel code                :11TIRS000000TIRP"],
            [0.0, 1.0, 2.0],
        )
        channel = parse_xxx(text, pyisomme.Isomme())
        np.testing.assert_array_equal(channel.data.index, [0, 1, 2])
        # Sample index is the expected shape for a time-reference channel -> not flagged.
        self.assertEqual(get_normalization_notes(channel), [])

    def test_non_numeric_data_raises_malformed_file_error(self):
        text = self._channel_text(
            ["Channel code                :11HEADCG0000ACXP",
             "Sampling interval           :0.01"],
            ["not_a_number", 1.0],
        )
        with self.assertRaises(MalformedFileError):
            parse_xxx(text, pyisomme.Isomme())

    def test_note_recorded_in_standard_comments_field_without_clobbering(self):
        text = self._channel_text(
            ["Channel code                :11HEADCG0000ACXP",
             "Comments                    :DRIVER HEAD CG X ACCELERATION",
             "Sampling interval           :0.01"],
            [0.0, 1.0, 2.0],
        )
        channel = parse_xxx(text, pyisomme.Isomme())
        comments = [v for k, v in channel.info if k == "Comments"]
        # Authored comment preserved; normalization note appended as a second Comments line.
        self.assertIn("DRIVER HEAD CG X ACCELERATION", comments)
        self.assertEqual(len(get_normalization_notes(channel)), 1)

    def test_resolve_time_axis_returns_note_for_undeclared_convention(self):
        info = pyisomme.Info([("Sampling interval", 0.01)])
        index, note = resolve_time_axis(info, 3, pyisomme.Isomme())
        self.assertIsNotNone(index)
        self.assertIsNotNone(note)


if __name__ == '__main__':
    unittest.main()
