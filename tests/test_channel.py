import unittest
import logging
import warnings
import copy
from unittest.mock import patch

from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import astropy.units as u

from pyisomme.channel import Channel, create_sample
from pyisomme.isomme import Isomme
from pyisomme.unit import Unit, g0


logger = logging.getLogger(__name__)
logging.basicConfig(format='%(module)-12s %(levelname)-8s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S', level=logging.WARNING)


class TestChannel(unittest.TestCase):
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
            t_range=(0., 1., 101),
            y_range=(2., -12.),
            mode="pulse",
            unit="N",
            frequency=4.,
        )

        values = channel.get_data()
        self.assertEqual(values[0], 2.)
        self.assertEqual(values[-1], 2.)
        self.assertAlmostEqual(np.min(values), -12.)
        self.assertGreater(len(np.unique(values)), 20)

    def test_create_sample_noise_is_seeded_and_optional(self):
        kwargs = {
            "t_range": (0., 0.1, 100),
            "y_range": (0., 10.),
            "mode": "pulse",
            "noise": 0.1,
        }
        first = create_sample(seed=42, **kwargs)
        repeated = create_sample(seed=42, **kwargs)
        different = create_sample(seed=43, **kwargs)

        np.testing.assert_array_equal(first.get_data(), repeated.get_data())
        self.assertFalse(np.array_equal(first.get_data(), different.get_data()))

    def test_create_sample_rejects_invalid_signal_parameters(self):
        with self.assertRaisesRegex(ValueError, "at least two samples"):
            create_sample(t_range=(0., 1., 1))
        with self.assertRaisesRegex(ValueError, "greater than its start"):
            create_sample(t_range=(1., 1., 10))
        with self.assertRaisesRegex(ValueError, "frequency"):
            create_sample(frequency=0.)
        with self.assertRaisesRegex(ValueError, "noise"):
            create_sample(noise=-0.1)

    def test_get_info(self):
        channel = Channel(code="11HEAD0000H3ACXP",
                                   data=pd.DataFrame([]),
                                   info=[("Time of first sample", -0.030399999)])
        assert channel.get_info("Time of first sample") == channel.get_info("[XT]ime * f?rst sample")
        assert channel.get_info("Time of first sample") == channel.get_info("[XT]ime .* f.rst sample")

    def test_eq(self):
        c_1 = Channel(code="????????????????", data=pd.DataFrame([1]), unit="m")
        c_2 = Channel(code="????????????????", data=pd.DataFrame([1000]), unit="mm")

        self.assertTrue(c_1 == c_2)

    def test_ne(self):
        c_1 = Channel(code="????????????????", data=pd.DataFrame([1]), unit="m")
        c_2 = Channel(code="????????????????", data=pd.DataFrame([1]), unit="mm")

        self.assertTrue(c_1 != c_2)

    def test_add(self):
        c_1 = Channel(code="????????????????", data=pd.DataFrame([1]), unit="m")
        c_2 = Channel(code="????????????????", data=pd.DataFrame([1000]), unit="mm")

        self.assertEqual((c_1 + c_2).get_data(unit="m"), 2)
        self.assertEqual((c_1 + 1).get_data(unit="m"), 2)

    def test_sub(self):
        c_1 = Channel(code="????????????????", data=pd.DataFrame([1]), unit="m")
        c_2 = Channel(code="????????????????", data=pd.DataFrame([1000]), unit="mm")

        self.assertEqual((c_1 - c_2).get_data(unit="m"), 0)
        self.assertEqual((c_1 - 1).get_data(unit="m"), 0)

    def test_calculation_history_add_mul(self):
        c_1 = Channel(code="11HEAD0000H3ACXA", data=pd.DataFrame([1]), unit="m")
        c_2 = Channel(code="11HEAD0000H3ACYA", data=pd.DataFrame([1]), unit="m")

        # __add__ must record "+", not "-"
        self.assertEqual((c_1 + c_2).info[-1], ("Calculation History", "11HEAD0000H3ACXA + 11HEAD0000H3ACYA"))
        self.assertEqual((c_1 + 1).info[-1], ("Calculation History", "11HEAD0000H3ACXA + 1"))
        # __sub__ records "-"
        self.assertEqual((c_1 - c_2).info[-1], ("Calculation History", "11HEAD0000H3ACXA - 11HEAD0000H3ACYA"))
        # __mul__ must record "*", not "/"
        self.assertEqual((c_1 * c_2).info[-1], ("Calculation History", "11HEAD0000H3ACXA * 11HEAD0000H3ACYA"))
        self.assertEqual((c_1 * 2).info[-1], ("Calculation History", "11HEAD0000H3ACXA * 2"))
        # __truediv__ records "/"
        self.assertEqual((c_1 / c_2).info[-1], ("Calculation History", "11HEAD0000H3ACXA / 11HEAD0000H3ACYA"))

    def test_differentiate_does_not_mutate_source_info(self):
        source = create_sample(code="11HEAD0000H3VEXA", mode="linear")
        before = list(source.info)

        derived = source.differentiate()

        # The source channel's info must be untouched by the derivation.
        self.assertEqual(list(source.info), before)
        # The derived channel gets its own updated Dimension.
        self.assertEqual(derived.info.get("Dimension"), derived.code.physical_dimension)

    def test_integrate_does_not_mutate_source_info(self):
        source = create_sample(code="11HEAD0000H3ACXA", mode="linear")
        before = list(source.info)

        derived = source.integrate()

        self.assertEqual(list(source.info), before)
        self.assertEqual(derived.info.get("Dimension"), derived.code.physical_dimension)

    def test_cfc_and_cfc_hz_equivalence(self):
        # Filter class "B" and its cutoff frequency 600 Hz must produce identical results,
        # and both must record filter class "B" in the code.
        source = create_sample(code="11HEAD0000H3ACXP", mode="sin")
        by_class = copy.deepcopy(source).cfc("B")
        by_freq = copy.deepcopy(source).cfc_hz(600)

        self.assertTrue(np.allclose(by_class.get_data(), by_freq.get_data()))
        self.assertEqual(by_class.code.filter_class, "B")
        self.assertEqual(by_freq.code.filter_class, "B")

    def test_cfc_hz_non_standard_frequency_records_S(self):
        source = create_sample(code="11HEAD0000H3ACXP", mode="sin")
        self.assertEqual(copy.deepcopy(source).cfc_hz(123.0).code.filter_class, "S")

    def test_cfc_unknown_filter_class_raises(self):
        source = create_sample(code="11HEAD0000H3ACXP", mode="sin")
        with self.assertRaises(ValueError):
            source.cfc("Z")

    def test_cfc_numeric_is_deprecated_and_delegates(self):
        # Backward-compat shim: cfc(<number>) warns and behaves like cfc_hz(<number>).
        source = create_sample(code="11HEAD0000H3ACXP", mode="sin")
        expected = copy.deepcopy(source).cfc_hz(600)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = copy.deepcopy(source).cfc(600) # type: ignore
        self.assertTrue(any(issubclass(w.category, DeprecationWarning) for w in caught))
        self.assertTrue(np.allclose(result.get_data(), expected.get_data()))

    def test_cfc_does_not_mutate_source_info(self):
        # Both filter methods must leave the source channel's info untouched.
        for method in ("ISO-6487", "SAE-J211-1"):
            source = create_sample(code="11HEAD0000H3ACXP", mode="sin")
            before = list(source.info)
            copy.deepcopy(source).cfc("B", method=method)
            self.assertEqual(list(source.info), before, msg=method)

    def test_get_value_is_float_get_data_is_ndarray(self):
        source = create_sample(code="11HEAD0000H3ACXP", mode="sin")
        self.assertIsInstance(source.get_value(t=0.0), float)
        self.assertIsInstance(source.get_data(t=0.0), np.ndarray)
        self.assertIsInstance(source.get_data(), np.ndarray)

    def test_getitem_index_types(self):
        c0 = create_sample(code="11HEAD0000H3ACXP", mode="sin")
        c1 = create_sample(code="11HEAD0000H3ACYP", mode="sin")
        iso = Isomme(test_number="TEST", channels=[c0, c1])

        # int -> single Channel, slice -> list
        self.assertIs(iso[0], c0)
        self.assertEqual(iso[0:2], [c0, c1])

        # str -> code-pattern shorthand for get_channels (a list)
        self.assertEqual(iso["11HEAD0000H3ACXP"], [c0])
        self.assertEqual(iso["11HEAD0000H3AC?P"], [c0, c1])

        # unsupported key type -> explicit TypeError (was a silent None)
        with self.assertRaises(TypeError):
            iso[1.5] # type: ignore

    def test_plot_uses_channel_metadata_defaults(self):
        channel = Channel(
            code="11HEAD0000H3ACXP",
            data=pd.DataFrame({"sample": [0., 1.]}, index=[0., 0.01]),
            unit="m/s^2",
            info={"Dimension": "Acceleration"},
        )

        try:
            with patch("pyisomme.channel.plt.show") as show:
                channel.plot()

            ax = plt.gca()
            self.assertEqual(ax.get_title(), str(channel.code))
            self.assertEqual(ax.get_xlabel(), "Time [ms]")
            self.assertEqual(ax.get_ylabel(), f"Acceleration [{channel.unit}]")
            np.testing.assert_array_equal(ax.lines[0].get_xdata(), [0., 10.])
            self.assertIsNone(ax.get_legend())
            self.assertTrue(any(line.get_visible() for line in ax.get_xgridlines()))
            np.testing.assert_array_equal(ax.figure.get_size_inches(), [10., 6.])
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
            self.assertEqual(ax.get_title(), "Custom title")
            self.assertEqual(ax.get_xlabel(), "Custom x")
            self.assertEqual(ax.get_ylabel(), "Custom y")
            self.assertEqual(
                [text.get_text() for text in ax.get_legend().get_texts()],
                ["Custom series"],
            )
            self.assertFalse(any(line.get_visible() for line in ax.get_xgridlines()))
            np.testing.assert_array_equal(ax.figure.get_size_inches(), [4., 3.])
        finally:
            plt.close("all")

class TestChannelConvertUnit(unittest.TestCase):
    """Test suite enforcing edge cases for Channel.convert_unit and Unit.to integration."""

    def setUp(self):
        # Sample channel: 1 meter at t=0, t=1, t=2
        self.data = pd.DataFrame([1.0, 2.0, 3.0], index=[0, 1, 2])
        self.channel = Channel(
            code="11HEAD0000H3ACXA",
            data=self.data.copy(),
            unit="m"
        )

    def test_convert_unit_with_string_input(self):
        """Conversion using a plain string target unit (e.g., 'mm')."""
        result = self.channel.convert_unit("mm")

        # 1 m, 2 m, 3 m -> 1000 mm, 2000 mm, 3000 mm
        expected = np.array([[1000.0], [2000.0], [3000.0]])
        np.testing.assert_allclose(self.channel.data.to_numpy(), expected)
        self.assertEqual(self.channel.unit, Unit("mm"))
        self.assertIs(result, self.channel, msg="convert_unit should return self for chaining")

    def test_convert_unit_with_custom_unit_instance(self):
        """Conversion using a custom Unit instance."""
        target_unit = Unit("km")
        self.channel.convert_unit(target_unit)

        expected = np.array([[0.001], [0.002], [0.003]])
        np.testing.assert_allclose(self.channel.data.to_numpy(), expected)
        self.assertEqual(self.channel.unit, Unit("km"))

    def test_convert_unit_with_native_astropy_unit(self):
        """Conversion using a native Astropy unit object (u.cm)."""
        self.channel.convert_unit(u.cm)

        expected = np.array([[100.0], [200.0], [300.0]])
        np.testing.assert_allclose(self.channel.data.to_numpy(), expected)
        self.assertEqual(self.channel.unit, Unit("cm"))

    def test_convert_unit_with_scaled_custom_unit(self):
        """Conversion involving scaled units like Earth gravity (g0 -> m/s^2)."""
        g_channel = Channel(
            code="11HEAD0000H3ACXA",
            data=pd.DataFrame([1.0]),
            unit=Unit(g0)
        )
        g_channel.convert_unit("m/s^2")

        # 1 g0 = ~9.80665 m/s^2
        self.assertAlmostEqual(g_channel.data.iloc[0, 0], 9.80665, places=4) # type: ignore
        self.assertEqual(g_channel.unit, Unit("m/s^2"))

    def test_convert_unit_raises_attribute_error_when_unit_is_none(self):
        """Edge Case: Channel.unit is None should raise AttributeError."""
        self.channel.unit = None # type: ignore
        with self.assertRaises(AttributeError) as ctx:
            self.channel.convert_unit("mm")

        self.assertIn("Not possible to convert units when current unit is None", str(ctx.exception))

    def test_convert_unit_raises_error_for_incompatible_dimensions(self):
        """Edge Case: Converting meters ('m') to seconds ('s') must fail."""
        with self.assertRaises(u.UnitConversionError):
            self.channel.convert_unit("s")

    def test_convert_unit_in_place_dataframe_mutation(self):
        """Verifies that the underlying DataFrame is mutated in-place and retains index/shape."""
        original_df_id = id(self.channel.data)
        self.channel.convert_unit("mm")

        self.assertEqual(id(self.channel.data), original_df_id, "DataFrame instance should not be replaced")
        self.assertEqual(self.channel.data.shape, (3, 1))
        np.testing.assert_array_equal(self.channel.data.index.to_numpy(), np.array([0, 1, 2]))


if __name__ == '__main__':
    unittest.main()
