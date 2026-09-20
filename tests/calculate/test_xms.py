import numpy as np
import pandas as pd
import pytest

import pyisomme
import pyisomme.providers as providers


class TestCalculateXMS:
    @staticmethod
    def channel(time, values, *, code="11HEAD0000H3ACRA", info=None):
        return pyisomme.Channel(
            code=code,
            data=pd.DataFrame(values, index=time),
            unit="g",
            info=info,
        )

    @pytest.fixture
    def isomme(self):
        time = [0.0, 0.001, 0.002, 0.003, 0.004]
        channel = pyisomme.Channel(
            code="11HEAD0000H3ACXA",
            data=pd.DataFrame([0.0, 1.0, 2.0, 3.0, 4.0], index=time),
            unit="g",
        )
        return pyisomme.Isomme(channels=[channel])

    def test_calculate_xms(self, isomme):
        direct = pyisomme.calculate_xms(isomme.channels[0], min_delta_t=1, method="S")
        assert direct.code.fine_location_2 == "1S"

    @pytest.mark.parametrize("method", ["S", "C"])
    def test_interpolates_threshold_crossings(self, method):
        channel = self.channel([0.0, 0.001, 0.002], [0.0, 10.0, 0.0])

        result = pyisomme.calculate_xms(channel, min_delta_t=1, method=method)

        assert result.get_data()[0] == pytest.approx(5.0)

    def test_cumulative_combines_disconnected_events(self):
        channel = self.channel(
            np.arange(0.0, 0.009, 0.001),
            [0.0, 10.0, 10.0, 0.0, 0.0, 10.0, 10.0, 0.0, 0.0],
        )

        continuous = pyisomme.calculate_xms(channel, min_delta_t=3, method="S")
        cumulative = pyisomme.calculate_xms(channel, min_delta_t=3, method="C")

        assert cumulative.get_data()[0] > continuous.get_data()[0]

    def test_irregular_sampling_uses_elapsed_time(self):
        channel = self.channel(
            [0.0, 0.00025, 0.001, 0.0016, 0.002],
            [0.0, 2.5, 10.0, 4.0, 0.0],
        )

        result = pyisomme.calculate_xms(channel, min_delta_t=1, method="C")

        assert result.get_data()[0] == pytest.approx(5.0)

    def test_resampling_preserves_piecewise_linear_result(self):
        coarse = self.channel([0.0, 0.001, 0.002], [0.0, 10.0, 0.0])
        fine_time = np.linspace(0.0, 0.002, 21)
        fine = self.channel(
            fine_time, np.interp(fine_time, coarse.data.index, coarse.get_data())
        )

        coarse_result = pyisomme.calculate_xms(coarse, min_delta_t=1, method="C")
        fine_result = pyisomme.calculate_xms(fine, min_delta_t=1, method="C")

        assert coarse_result.get_data()[0] == pytest.approx(fine_result.get_data()[0])

    def test_constant_negative_signal_does_not_default_to_zero(self):
        channel = self.channel([0.0, 0.001, 0.002, 0.003], [-5.0] * 4)

        result = pyisomme.calculate_xms(channel, min_delta_t=3, method="C")

        assert result.get_data()[0] == pytest.approx(-5.0)

    def test_rejects_recording_shorter_than_requested_duration(self):
        channel = self.channel([0.0, 0.001, 0.002], [0.0, 1.0, 0.0])

        with pytest.raises(ValueError, match="shorter"):
            pyisomme.calculate_xms(channel, min_delta_t=3, method="C")

    def test_rejects_non_finite_values(self):
        channel = self.channel([0.0, 0.001, 0.002, 0.003], [0.0, np.nan, 1.0, 0.0])

        with pytest.raises(ValueError, match="finite channel values"):
            pyisomme.calculate_xms(channel, min_delta_t=3, method="C")

    def test_does_not_mutate_source_metadata(self):
        channel = self.channel(
            [0.0, 0.001, 0.002, 0.003],
            [5.0] * 4,
            info={"Data source": "measurement", "Custom": "kept"},
        )

        result = pyisomme.calculate_xms(channel, min_delta_t=3, method="C")

        assert channel.info.get("Data source") == "measurement"
        assert channel.info.get(".Analysis start time") is None
        assert result.info.get("Data source") == "calculation"
        assert result.info.get("Custom") == "kept"

    def test_calculate_xms_provider(self, isomme):
        provided = isomme.get_channel("11HEAD001SH3ACXX")
        assert provided is not None
        assert provided.code.filter_class == "X"
        assert provided.get_data()[0] >= 0

        xms = isomme.get_channel("11HEAD003SH3ACXX")
        assert xms is not None
        assert xms.code.fine_location_2 == "3S"
        assert xms.code.filter_class == "X"
        assert xms.data.shape == (1, 1)

    @pytest.mark.parametrize(
        ("location", "expected_filter"),
        [("HEAD", "A"), ("CHST", "C"), ("THSP", "C")],
    )
    def test_provider_uses_location_specific_filter(
        self, monkeypatch, location, expected_filter
    ):
        time = [0.0, 0.001, 0.002, 0.003]
        channels = [
            self.channel(
                time,
                [5.0] * 4,
                code=f"11{location}0000H3ACR{filter_class}",
            )
            for filter_class in ("A", "C")
        ]
        isomme = pyisomme.Isomme(channels=channels)
        source_filters = []
        calculate_xms = providers.calculate_xms

        def capture_source_filter(channel, min_delta_t=3, method="S"):
            source_filters.append(channel.code.filter_class)
            return calculate_xms(channel, min_delta_t=min_delta_t, method=method)

        monkeypatch.setattr(providers, "calculate_xms", capture_source_filter)

        result = isomme.get_channel(f"11{location}003CH3ACRX")

        assert result is not None
        assert source_filters == [expected_filter]

    def test_provider_does_not_guess_filter_for_unknown_location(self):
        channel = self.channel(
            [0.0, 0.001, 0.002, 0.003],
            [5.0] * 4,
            code="11PELV0000H3ACRA",
        )

        result = pyisomme.Isomme(channels=[channel]).get_channel("11PELV003CH3ACRX")

        assert result is None
