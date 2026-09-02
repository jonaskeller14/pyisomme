import numpy as np
import pandas as pd
import pytest

import pyisomme


class TestCalculateHeadTrajectory:
    @pytest.fixture
    def channels(self):
        time = [0.5, 1.5, 2.5]
        channels = []
        for code, values, unit in (
            ("11HEAD0000H3ACXA", [1.0, 1.0, 1.0], "m/s**2"),
            ("11HEAD0000H3ACYA", [0.0, 0.0, 0.0], "m/s**2"),
            ("11HEAD0000H3ACZA", [0.0, 0.0, 0.0], "m/s**2"),
            ("11HEAD0000H3AVXA", [0.0, 0.0, 0.0], "rad/s"),
            ("11HEAD0000H3AVYA", [0.0, 0.0, 0.0], "rad/s"),
            ("11HEAD0000H3AVZA", [0.0, 0.0, 0.0], "rad/s"),
        ):
            channels.append(
                pyisomme.Channel(code, pd.DataFrame(values, index=time), unit)
            )
        return channels

    def test_calculates_global_displacement(self, channels):
        position_x, position_y, position_z = pyisomme.calculate_head_trajectory(
            *channels,
            initial_velocity=(2.0, 0.0, 0.0),
            initial_position=(10.0, 20.0, 30.0),
        )

        np.testing.assert_allclose(position_x.get_data(), [10.0, 12.5, 16.0])
        np.testing.assert_allclose(position_y.get_data(), [20.0, 20.0, 20.0])
        np.testing.assert_allclose(position_z.get_data(), [30.0, 30.0, 30.0])
        assert [
            channel.code.physical_dimension
            for channel in (position_x, position_y, position_z)
        ] == ["DS"] * 3
        assert [
            channel.code.direction for channel in (position_x, position_y, position_z)
        ] == list("XYZ")
        assert all(
            channel.unit.is_equivalent("m")
            for channel in (position_x, position_y, position_z)
        )
        assert position_x.get_info(".Coordinate system") == "global"

    def test_requires_two_common_samples(self, channels):
        channels[-1].data.index = [2.5, 3.5, 4.5]

        with pytest.raises(ValueError, match="two common samples"):
            pyisomme.calculate_head_trajectory(*channels)
