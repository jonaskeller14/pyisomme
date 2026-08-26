import copy
import logging
import warnings
from unittest.mock import patch

import astropy.units as u
import numpy as np
import pandas as pd
import pytest
from matplotlib import pyplot as plt

from pyisomme.channel import Channel, create_sample
from pyisomme.isomme import Isomme
from pyisomme.unit import Unit, g0

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(module)-12s %(levelname)-8s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S",
    level=logging.WARNING,
)


class TestChannel:
    def test_init(self):
        Channel(code="11HEAD0000H3ACXP", data=pd.DataFrame([]))
        # < 16 chars
        Channel(code="11HEAD0000H3", data=pd.DataFrame([]))
        # > 16 chars
        Channel(code="11HEAD0000H3ACXP123", data=pd.DataFrame([]))
        # invalid chars
        Channel(code="TOTAL_ENERGY", data=pd.DataFrame([]))

    def test_create_sample_pulse_has_baseline_peak_and_frequency_content(self):
        channel = create_sample(
            code="11FEMRLE0000FOZP",
            t_range=(0.0, 1.0, 101),
            y_range=(2.0, -12.0),
            mode="pulse",
            unit="N",
            frequency=4.0,
        )

        values = channel.get_data()
        assert values[0] == 2.0
        assert values[-1] == 2.0
        assert np.min(values) == pytest.approx(-12.0)
        assert len(np.unique(values)) > 20

    def test_create_sample_noise_is_seeded_and_optional(self):
        kwargs = {
            "t_range": (0.0, 0.1, 100),
            "y_range": (0.0, 10.0),
            "mode": "pulse",
            "noise": 0.1,
        }
        first = create_sample(seed=42, **kwargs)
        repeated = create_sample(seed=42, **kwargs)
        different = create_sample(seed=43, **kwargs)

        np.testing.assert_array_equal(first.get_data(), repeated.get_data())
        assert not np.array_equal(first.get_data(), different.get_data())

    def test_create_sample_rejects_invalid_signal_parameters(self):
        with pytest.raises(ValueError, match="at least two samples"):
            create_sample(t_range=(0.0, 1.0, 1))
        with pytest.raises(ValueError, match="greater than its start"):
            create_sample(t_range=(1.0, 1.0, 10))
        with pytest.raises(ValueError, match="frequency"):
            create_sample(frequency=0.0)
        with pytest.raises(ValueError, match="noise"):
            create_sample(noise=-0.1)

    def test_get_info(self):
        channel = Channel(
            code="11HEAD0000H3ACXP",
            data=pd.DataFrame([]),
            info=[("Time of first sample", -0.030399999)],
        )
        assert channel.get_info("Time of first sample") == channel.get_info(
            "[XT]ime * f?rst sample"
        )
        assert channel.get_info("Time of first sample") == channel.get_info(
            "[XT]ime .* f.rst sample"
        )

    def test_eq(self):
        c_1 = Channel(code="????????????????", data=pd.DataFrame([1]), unit="m")
        c_2 = Channel(code="????????????????", data=pd.DataFrame([1000]), unit="mm")

        assert c_1 == c_2

    def test_eq_requires_same_code(self):
        c_1 = Channel(code="11HEAD0000H3ACXA", data=pd.DataFrame([1]), unit="m")
        c_2 = Channel(code="11HEAD0000H3ACYA", data=pd.DataFrame([1000]), unit="mm")

        assert c_1 != c_2

    def test_ne(self):
        c_1 = Channel(code="????????????????", data=pd.DataFrame([1]), unit="m")
        c_2 = Channel(code="????????????????", data=pd.DataFrame([1]), unit="mm")

        assert c_1 != c_2

    def test_add(self):
        c_1 = Channel(code="????????????????", data=pd.DataFrame([1]), unit="m")
        c_2 = Channel(code="????????????????", data=pd.DataFrame([1000]), unit="mm")

        assert (c_1 + c_2).get_data(unit="m") == 2
        assert (c_1 + 1).get_data(unit="m") == 2

    def test_sub(self):
        c_1 = Channel(code="????????????????", data=pd.DataFrame([1]), unit="m")
        c_2 = Channel(code="????????????????", data=pd.DataFrame([1000]), unit="mm")

        assert (c_1 - c_2).get_data(unit="m") == 0
        assert (c_1 - 1).get_data(unit="m") == 0

    def test_calculation_history_add_mul(self):
        c_1 = Channel(code="11HEAD0000H3ACXA", data=pd.DataFrame([1]), unit="m")
        c_2 = Channel(code="11HEAD0000H3ACYA", data=pd.DataFrame([1]), unit="m")

        # __add__ must record "+", not "-"
        assert (c_1 + c_2).info[-1] == (
            "Calculation History",
            "11HEAD0000H3ACXA + 11HEAD0000H3ACYA",
        )
        assert (c_1 + 1).info[-1] == ("Calculation History", "11HEAD0000H3ACXA + 1")
        # __sub__ records "-"
        assert (c_1 - c_2).info[-1] == (
            "Calculation History",
            "11HEAD0000H3ACXA - 11HEAD0000H3ACYA",
        )
        # __mul__ must record "*", not "/"
        assert (c_1 * c_2).info[-1] == (
            "Calculation History",
            "11HEAD0000H3ACXA * 11HEAD0000H3ACYA",
        )
        assert (c_1 * 2).info[-1], ("Calculation History", "11HEAD0000H3ACXA * 2")
        # __truediv__ records "/"
        assert (c_1 / c_2).info[-1] == (
            "Calculation History",
            "11HEAD0000H3ACXA / 11HEAD0000H3ACYA",
        )

    def test_differentiate_does_not_mutate_source_info(self):
        source = create_sample(code="11HEAD0000H3VEXA", mode="linear")
        before = list(source.info)

        derived = source.differentiate()

        # The source channel's info must be untouched by the derivation.
        assert list(source.info) == before
        # The derived channel gets its own updated Dimension.
        assert derived.info.get("Dimension") == derived.code.physical_dimension

    def test_integrate_does_not_mutate_source_info(self):
        source = create_sample(code="11HEAD0000H3ACXA", mode="linear")
        before = list(source.info)

        derived = source.integrate()

        assert list(source.info) == before
        assert derived.info.get("Dimension") == derived.code.physical_dimension

    def test_cfc_and_cfc_hz_equivalence(self):
        # Filter class "B" and its cutoff frequency 600 Hz must produce identical results,
        # and both must record filter class "B" in the code.
        source = create_sample(code="11HEAD0000H3ACXP", mode="sin")
        by_class = copy.deepcopy(source).cfc("B")
        by_freq = copy.deepcopy(source).cfc_hz(600)

        assert np.allclose(by_class.get_data(), by_freq.get_data())
        assert by_class.code.filter_class == "B"
        assert by_freq.code.filter_class == "B"

    def test_cfc_hz_non_standard_frequency_records_S(self):
        source = create_sample(code="11HEAD0000H3ACXP", mode="sin")
        assert copy.deepcopy(source).cfc_hz(123.0).code.filter_class == "S"

    def test_cfc_unknown_filter_class_raises(self):
        source = create_sample(code="11HEAD0000H3ACXP", mode="sin")
        with pytest.raises(ValueError):
            source.cfc("Z")

    def test_cfc_numeric_is_deprecated_and_delegates(self):
        # Backward-compat shim: cfc(<number>) warns and behaves like cfc_hz(<number>).
        source = create_sample(code="11HEAD0000H3ACXP", mode="sin")
        expected = copy.deepcopy(source).cfc_hz(600)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = copy.deepcopy(source).cfc(600)  # type: ignore
        assert any(issubclass(w.category, DeprecationWarning) for w in caught)
        assert np.allclose(result.get_data(), expected.get_data())

    def test_cfc_does_not_mutate_source_info(self):
        # Both filter methods must leave the source channel's info untouched.
        for method in ("ISO-6487", "SAE-J211-1"):
            source = create_sample(code="11HEAD0000H3ACXP", mode="sin")
            before = list(source.info)
            copy.deepcopy(source).cfc("B", method=method)
            assert list(source.info) == before, method

    def test_get_value_is_float_get_data_is_ndarray(self):
        source = create_sample(code="11HEAD0000H3ACXP", mode="sin")
        assert isinstance(source.get_value(t=0.0), float)
        assert isinstance(source.get_data(t=0.0), np.ndarray)
        assert isinstance(source.get_data(), np.ndarray)

    def test_scale_and_offset_methods_transform_the_expected_axis(self):
        channel = Channel(
            code="11HEAD0000H3ACXP",
            data=pd.DataFrame({"sample": [5.0, 6.0]}, index=[0.0, 0.1]),
            unit="m/s^2",
        )

        assert channel.scale_y(2.0) is channel
        np.testing.assert_array_equal(channel.get_data(), [10.0, 12.0])
        np.testing.assert_array_equal(channel.data.index, [0.0, 0.1])

        assert channel.offset_y(-3.0) is channel
        np.testing.assert_array_equal(channel.get_data(), [7.0, 9.0])

        assert channel.scale_x(2.0) is channel
        np.testing.assert_array_equal(channel.data.index, [0.0, 0.2])

        assert channel.offset_x(-0.1) is channel
        np.testing.assert_array_equal(channel.data.index, [-0.1, 0.1])

    def test_auto_offset_y_zeros_value_at_requested_time(self):
        channel = Channel(
            code="11HEAD0000H3ACXP",
            data=pd.DataFrame({"sample": [5.0, 6.0]}, index=[0.0, 0.1]),
            unit="m/s^2",
        )

        assert channel.auto_offset_y(t=0.0) is channel
        np.testing.assert_array_equal(channel.get_data(), [0.0, 1.0])
        assert channel.get_value(t=0.0) == 0.0

    def test_crop_limits_channel_to_requested_time_range(self):
        channel = Channel(
            code="11HEAD0000H3ACXP",
            data=pd.DataFrame({"sample": [1.0, 2.0, 3.0]}, index=[0.0, 0.1, 0.2]),
            unit="m/s^2",
        )

        assert channel.crop(x_min=0.1, x_max=0.2) is channel
        np.testing.assert_array_equal(channel.data.index, [0.1, 0.2])
        np.testing.assert_array_equal(channel.get_data(), [2.0, 3.0])

    def test_getitem_index_types(self):
        c0 = create_sample(code="11HEAD0000H3ACXP", mode="sin")
        c1 = create_sample(code="11HEAD0000H3ACYP", mode="sin")
        iso = Isomme(test_number="TEST", channels=[c0, c1])

        # int -> single Channel, slice -> list
        assert iso[0] is c0
        assert iso[0:2] == [c0, c1]

        # str -> code-pattern shorthand for get_channels (a list)
        assert iso["11HEAD0000H3ACXP"] == [c0]
        assert iso["11HEAD0000H3AC?P"] == [c0, c1]

        # unsupported key type -> explicit TypeError (was a silent None)
        with pytest.raises(TypeError):
            iso[1.5]  # type: ignore

    def test_plot_uses_channel_metadata_defaults(self):
        channel = Channel(
            code="11HEAD0000H3ACXP",
            data=pd.DataFrame({"sample": [0.0, 1.0]}, index=[0.0, 0.01]),
            unit="m/s^2",
            info={"Dimension": "Acceleration"},
        )

        try:
            with patch("pyisomme.channel.plt.show") as show:
                channel.plot()

            ax = plt.gca()
            assert ax.get_title() == str(channel.code)
            assert ax.get_xlabel() == "Time [ms]"
            assert ax.get_ylabel() == f"Acceleration [{channel.unit}]"
            np.testing.assert_array_equal(ax.lines[0].get_xdata(), [0.0, 10.0])
            assert ax.get_legend() is None
            assert any(line.get_visible() for line in ax.get_xgridlines())
            np.testing.assert_array_equal(ax.figure.get_size_inches(), [10.0, 6.0])
            show.assert_called_once_with()
        finally:
            plt.close("all")

    def test_plot_kwargs_override_metadata_defaults(self):
        channel = create_sample(code="11HEAD0000H3ACXP", unit="m/s^2")

        try:
            with patch("pyisomme.channel.plt.show"):
                channel.plot(
                    title="Custom title",
                    xlabel="Custom x",
                    ylabel="Custom y",
                    label="Custom series",
                    legend=True,
                    grid=False,
                    figsize=(4, 3),
                )

            ax = plt.gca()
            assert ax.get_title() == "Custom title"
            assert ax.get_xlabel() == "Custom x"
            assert ax.get_ylabel() == "Custom y"
            assert [text.get_text() for text in ax.get_legend().get_texts()] == [
                "Custom series"
            ]

            assert not any(line.get_visible() for line in ax.get_xgridlines())
            np.testing.assert_array_equal(ax.figure.get_size_inches(), [4.0, 3.0])
        finally:
            plt.close("all")


class TestChannelConvertUnit:
    """Test suite enforcing edge cases for Channel.convert_unit and Unit.to integration."""

    @pytest.fixture
    def sample_channel(self):
        # Sample channel: 1 meter at t=0, t=1, t=2
        data = pd.DataFrame([1.0, 2.0, 3.0], index=[0, 1, 2])
        return Channel(code="11HEAD0000H3ACXA", data=data.copy(), unit="m")

    def test_convert_unit_with_string_input(self, sample_channel):
        """Conversion using a plain string target unit (e.g., 'mm')."""
        result = sample_channel.convert_unit("mm")

        # 1 m, 2 m, 3 m -> 1000 mm, 2000 mm, 3000 mm
        expected = np.array([[1000.0], [2000.0], [3000.0]])
        np.testing.assert_allclose(sample_channel.data.to_numpy(), expected)
        assert sample_channel.unit == Unit("mm")
        assert result is sample_channel, "convert_unit should return self for chaining"

    def test_convert_unit_with_custom_unit_instance(self, sample_channel):
        """Conversion using a custom Unit instance."""
        target_unit = Unit("km")
        sample_channel.convert_unit(target_unit)

        expected = np.array([[0.001], [0.002], [0.003]])
        np.testing.assert_allclose(sample_channel.data.to_numpy(), expected)
        assert sample_channel.unit == Unit("km")

    def test_convert_unit_with_native_astropy_unit(self, sample_channel):
        """Conversion using a native Astropy unit object (u.cm)."""
        sample_channel.convert_unit(u.cm)

        expected = np.array([[100.0], [200.0], [300.0]])
        np.testing.assert_allclose(sample_channel.data.to_numpy(), expected)
        assert sample_channel.unit == Unit("cm")

    def test_convert_unit_with_scaled_custom_unit(self):
        """Conversion involving scaled units like Earth gravity (g0 -> m/s^2)."""
        g_channel = Channel(
            code="11HEAD0000H3ACXA", data=pd.DataFrame([1.0]), unit=Unit(g0)
        )
        g_channel.convert_unit("m/s^2")

        # 1 g0 = ~9.80665 m/s^2
        assert g_channel.data.iloc[0, 0] == pytest.approx(9.80665, 1e-4)
        assert g_channel.unit == Unit("m/s^2")

    def test_convert_unit_raises_attribute_error_when_unit_is_none(
        self, sample_channel
    ):
        """Edge Case: Channel.unit is None should raise AttributeError."""
        sample_channel.unit = None  # type: ignore
        with pytest.raises(AttributeError) as ctx:
            sample_channel.convert_unit("mm")

        assert "Not possible to convert units when current unit is None" in str(
            ctx.exconly
        )

    def test_convert_unit_raises_error_for_incompatible_dimensions(
        self, sample_channel
    ):
        """Edge Case: Converting meters ('m') to seconds ('s') must fail."""
        with pytest.raises(u.UnitConversionError):
            sample_channel.convert_unit("s")

    def test_convert_unit_in_place_dataframe_mutation(self, sample_channel):
        """Verifies that the underlying DataFrame is mutated in-place and retains index/shape."""
        original_df_id = id(sample_channel.data)
        sample_channel.convert_unit("mm")

        assert id(sample_channel.data) == original_df_id, (
            "DataFrame instance should not be replaced"
        )
        assert sample_channel.data.shape == (3, 1)
        np.testing.assert_array_equal(
            sample_channel.data.index.to_numpy(), np.array([0, 1, 2])
        )
