from __future__ import annotations

import copy
import logging
from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy.constants import g as STANDARD_GRAVITY
from scipy.integrate import cumulative_trapezoid
from scipy.spatial.transform import Rotation

from pyisomme.channel import Channel, time_intersect
from pyisomme.info import InfoValue
from pyisomme.utils import debug_logging

logger = logging.getLogger("pyisomme.calculate")


def _vector3(name: str, value: Sequence[float]) -> np.ndarray:
    """Return *value* as a finite three-component float vector."""
    vector = np.asarray(value, dtype=float)
    if vector.shape != (3,) or not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} must contain exactly three finite values")
    return vector


@debug_logging(logger)
def calculate_head_trajectory(
    channel_ac_x: Channel,
    channel_ac_y: Channel,
    channel_ac_z: Channel,
    channel_av_x: Channel,
    channel_av_y: Channel,
    channel_av_z: Channel,
    *,
    initial_angles: Sequence[float] = (0.0, 0.0, 0.0),
    initial_velocity: Sequence[float] = (0.0, 0.0, 0.0),
    initial_position: Sequence[float] = (0.0, 0.0, 0.0),
    sensor_offset: Sequence[float] = (0.0, 0.0, 0.0),
    gravity: float = -STANDARD_GRAVITY,
    gravity_correction: bool = True,
    axes_rotations: str = "xyz",
) -> tuple[Channel, Channel, Channel]:
    """Calculate the global head-CoG displacement trajectory.

    The six input channels must describe the same head and coordinate system:
    acceleration X/Y/Z and angular velocity X/Y/Z.  They are converted to
    ``m/s²`` and ``rad/s`` and sampled only at their common time points.
    ``initial_angles`` are Euler angles in radians, using ``axes_rotations``;
    velocities and positions are expressed in the resulting global frame.

    ``sensor_offset`` is the vector from the head CoG to the accelerometer in
    the measurement frame, in metres.  Leave it at zero for accelerometers at
    the CoG.  A non-zero offset applies the rigid-body tangential and
    centripetal acceleration correction.

    ``gravity_correction`` follows the baseline-relative correction used by
    the source implementation.  It must match the signal conditioning and
    gravity/sign convention of the measurement system.

    Adapted from TU Graz Vehicle Safety Institute's
    ``head-trajectory-calculation`` project (MIT licence):
    https://openvt.eu/EuroNCAP/head-trajectory-calculation.git

    Reference:
    Sinz, W., Moser, J., Klein, C., Raguse, K., von Middendorff, C., and
    Steiner, C. (2015). Precise Dummy Head Trajectories in Crash Tests based
    on Fusion of Optical and Electrical Data: Influence of Sensor Errors and
    Initial Values. SAE Technical Paper 2015-01-1442.
    https://doi.org/10.4271/2015-01-1442

    :return: Global X, Y and Z displacement channels (physical dimension
        ``DS``), in metres.
    """
    initial_angles_array = _vector3("initial_angles", initial_angles)
    initial_velocity_array = _vector3("initial_velocity", initial_velocity)
    initial_position_array = _vector3("initial_position", initial_position)
    sensor_offset_array = _vector3("sensor_offset", sensor_offset)
    if not np.isfinite(gravity):
        raise ValueError("gravity must be finite")

    channels = (
        channel_ac_x,
        channel_ac_y,
        channel_ac_z,
        channel_av_x,
        channel_av_y,
        channel_av_z,
    )
    time = time_intersect(*channels)
    if len(time) < 2:
        raise ValueError("Head trajectory calculation requires two common samples")

    acceleration_local = np.column_stack(
        [channel.get_data(t=time, unit="m/s**2") for channel in channels[:3]]
    )
    angular_velocity = np.column_stack(
        [channel.get_data(t=time, unit="rad/s") for channel in channels[3:]]
    )

    time_step = np.diff(time)
    delta_angles = (angular_velocity[1:] + angular_velocity[:-1]) * (
        time_step[:, np.newaxis] / 2
    )
    rotations = [Rotation.from_euler(axes_rotations, initial_angles_array)]
    for delta_angle in delta_angles:
        # Angular velocity is supplied in the head-fixed measurement frame.
        rotations.append(rotations[-1] * Rotation.from_rotvec(delta_angle))

    if np.any(sensor_offset_array):
        angular_acceleration = np.gradient(angular_velocity, time, axis=0)
        acceleration_local -= np.cross(angular_acceleration, sensor_offset_array)
        acceleration_local -= np.cross(
            angular_velocity,
            np.cross(angular_velocity, sensor_offset_array),
        )

    rotation_matrices = np.stack([rotation.as_matrix() for rotation in rotations])
    if gravity_correction:
        acceleration_local += gravity * (
            rotation_matrices[:, 2, :] - rotation_matrices[0, 2, :]
        )

    acceleration_global = np.einsum("nij,nj->ni", rotation_matrices, acceleration_local)
    velocity_global = cumulative_trapezoid(
        acceleration_global, time, axis=0, initial=0
    ) + initial_velocity_array
    position_global = cumulative_trapezoid(
        velocity_global, time, axis=0, initial=0
    ) + initial_position_array

    calculation_info: dict[str, InfoValue] = {
        "Data source": "calculation",
        ".Channel 001": str(channel_ac_x.code),
        ".Channel 002": str(channel_ac_y.code),
        ".Channel 003": str(channel_ac_z.code),
        ".Channel 004": str(channel_av_x.code),
        ".Channel 005": str(channel_av_y.code),
        ".Channel 006": str(channel_av_z.code),
        ".Initial angles": str(tuple(initial_angles_array)),
        ".Initial velocity": str(tuple(initial_velocity_array)),
        ".Initial position": str(tuple(initial_position_array)),
        ".Sensor offset": str(tuple(sensor_offset_array)),
        ".Gravity": float(gravity),
        ".Gravity correction": gravity_correction,
        ".Coordinate system": "global",
    }
    calculation_info.update(
        {
            f".Filter 00{index}": channel.code.filter_class
            for index, channel in enumerate(channels, 1)
        }
    )

    result_channels = []
    for column, direction in enumerate("XYZ"):
        result_channels.append(
            Channel(
                code=channel_ac_x.code.set(
                    physical_dimension="DS", direction=direction
                ),
                data=pd.DataFrame(position_global[:, column], index=time),
                unit="m",
                info=copy.deepcopy(channel_ac_x.info).update(calculation_info),
            )
        )
    return result_channels[0], result_channels[1], result_channels[2]
