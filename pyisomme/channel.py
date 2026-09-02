from __future__ import annotations

import copy
import logging
import re
import warnings
from fnmatch import fnmatch
from numbers import Real
from typing import Literal

import numpy as np
import pandas as pd
from astropy.units import UnitConversionError
from matplotlib import pyplot as plt
from scipy import interpolate as scipy_interpolate
from scipy.integrate import cumulative_trapezoid

from pyisomme.code import Code
from pyisomme.info import Info, InfoInput, InfoValue
from pyisomme.unit import Unit, g0

logger = logging.getLogger(__name__)

__all__ = [
    "Channel",
    "create_sample",
    "time_intersect",
]


class Channel:
    code: Code
    data: pd.DataFrame
    unit: Unit
    info: Info

    def __init__(
        self,
        code: str | Code,
        data: pd.DataFrame,
        unit: str | Unit | None = None,
        info: InfoInput | None = None,
    ):
        self.set_code(code)
        self._validate_data(data)
        self.data = data
        self.set_unit(unit)
        self.info = Info(info) if info is not None else Info()

    @staticmethod
    def _validate_data(data: pd.DataFrame) -> None:
        """Ensure that ``data`` represents one well-defined sampled signal.

        A Channel stores time in its DataFrame index and exactly one numeric
        value series in its sole column.  Enforcing this at construction keeps
        interpolation, numerical operations, unit conversion, and serialization
        consistent.
        """
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Channel data must be a pandas DataFrame")
        if data.empty:
            raise ValueError("Channel data must contain at least one sample")
        if data.shape[1] != 1:
            raise ValueError("Channel data must contain exactly one value column")
        if not pd.api.types.is_numeric_dtype(data.iloc[:, 0]):
            raise TypeError("Channel values must be numeric")
        if not all(
            isinstance(time, Real) and not isinstance(time, (bool, np.bool_))
            for time in data.index
        ):
            raise TypeError("Channel time index must be numeric")
        if data.index.hasnans:
            raise ValueError("Channel time index must not contain missing values")
        if not data.index.is_monotonic_increasing or not data.index.is_unique:
            raise ValueError(
                "Channel time index must be strictly increasing and unique"
            )

    def __str__(self):
        return self.code

    def __repr__(self):
        return f"Channel(code={self.code})"

    def set_code(
        self, new_code: str | Code | None = None, **code_components
    ) -> Channel:
        if new_code is None:  # if only components are set
            assert self.code is not None
            new_code = self.code

        if not re.fullmatch(r"[a-zA-Z0-9?]{16}", new_code):
            if re.search(r"[^a-zA-Z0-9]", new_code):
                logger.warning(
                    f"Code '{new_code}' contains invalid characters which will be removed"
                )
                new_code = re.sub(r"[^a-zA-Z0-9]", "", new_code)

            if len(new_code) > 16:
                logger.warning(f"Code '{new_code}' must be 16 characters long")
                logger.warning(f"Code '{new_code}' will be shortened to 16 characters")
                new_code = new_code[:16]
            elif len(new_code) < 16:
                logger.warning(f"Code '{new_code}' must be 16 characters long")
                logger.warning(f"Code '{new_code}' will be extended to 16 characters")
                new_code = new_code.ljust(16, "?")

        self.code = Code(new_code).set(**code_components)
        if not self.code.is_valid():
            logger.warning(f"'{self.code}' not a valid channel code")
        return self

    def set_unit(self, new_unit: None | str | Unit) -> Channel:
        """
        Set unit of Channel and return Channel.
        For converting the data see convert_unit()-method.
        :param new_unit: Unit-object or str
        :return: Channel (self)
        """
        if new_unit is None:
            new_unit = self.code.get_default_unit()
        elif isinstance(new_unit, str):
            if new_unit == "g" and self.code.physical_dimension == "AC":
                new_unit = Unit(g0)
        if new_unit is None:
            logger.warning("None is not a valid unit. Set unit to 1.")
            new_unit = "1"
        self.unit = Unit(new_unit)
        return self

    def convert_unit(self, new_unit: str | Unit) -> Channel:
        """
        Convert unit of Channel and return Channel.
        For setting unit without conversion see set_unit()-method.
        :param new_unit: Unit-object or str
        :return: Channel (self)
        """
        if self.unit is None:
            raise AttributeError(
                f"{self}. Not possible to convert units when current unit is None."
            )

        self.data.iloc[:, 0] = self.unit.to(
            other=new_unit, value=self.data.iloc[:, 0].to_numpy()
        )
        self.unit = Unit(new_unit)
        return self

    # Cutoff frequency (Hz) of each standard ISO filter class.
    _FILTER_CLASS_CFC = {"0": np.inf, "A": 1000, "B": 600, "C": 180, "D": 60}
    _CFC_METHODS = Literal["ISO-6487", "SAE-J211-1"]

    def cfc(
        self,
        filter_class: str,
        method: _CFC_METHODS = "ISO-6487",
        return_copy: bool = True,
    ) -> Channel:
        """
        Apply a filter to smooth curves, selected by ISO **filter class**
        ("0"/"A"/"B"/"C"/"D"). To filter by an explicit cutoff frequency use cfc_hz().
        REFERENCES:
        - Appendix C of references/SAE-J211-1-MAR95/sae.j211-1.1995.pdf
        - Annex A of references/ISO-6487/ISO-6487-2015.pdf
        :param filter_class: one of "0", "A", "B", "C", "D"
        :param method:
        :param return_copy:
        :return:
        """
        if not isinstance(filter_class, str):
            # Backward compatibility: cfc(<number>) historically meant a cutoff frequency.
            warnings.warn(
                "Channel.cfc(<numeric>) is deprecated; use cfc_hz(freq) for a cutoff "
                "frequency in Hz, or cfc('A'/'B'/'C'/'D') for an ISO filter class.",
                DeprecationWarning,
                stacklevel=2,
            )
            return self.cfc_hz(filter_class, method=method, return_copy=return_copy)
        if filter_class not in self._FILTER_CLASS_CFC:
            raise ValueError(
                f"Unknown filter class {filter_class!r}; expected one of "
                f"{sorted(self._FILTER_CLASS_CFC)}."
            )
        return self._apply_cfc(
            self._FILTER_CLASS_CFC[filter_class], filter_class, method, return_copy
        )

    def cfc_hz(
        self, freq: float, method: _CFC_METHODS = "ISO-6487", return_copy: bool = True
    ) -> Channel:
        """
        Apply a filter to smooth curves, selected by an explicit cutoff **frequency in Hz**.
        The nearest standard ISO filter class (or "S" for a non-standard cutoff) is recorded
        in the resulting channel code.
        :param freq: cutoff frequency in Hz (np.inf = no filtering)
        :param method:
        :param return_copy:
        :return:
        """
        filter_class = next(
            (fc for fc, hz in self._FILTER_CLASS_CFC.items() if hz == freq), "S"
        )
        return self._apply_cfc(freq, filter_class, method, return_copy)

    def _apply_cfc(
        self, cfc: float, filter_class: str, method: _CFC_METHODS, return_copy: bool
    ) -> Channel:
        # Check if Channel is already filtered
        if filter_class == "0":
            return copy.deepcopy(self) if return_copy else self
        elif (
            filter_class == "A"
            and self.code.filter_class in ("A", "B", "C", "D")
            or filter_class == "B"
            and self.code.filter_class in ("B", "C", "D")
            or filter_class == "C"
            and self.code.filter_class in ("C", "D")
            or filter_class == "D"
            and self.code.filter_class in ("D",)
        ):
            logger.warning("No filtering applied. Channel is already filtered.")
            return copy.deepcopy(self) if return_copy else self

        # Calculation
        if method == "ISO-6487":
            # Variables used
            samples = self.get_data()
            number_of_samples = len(samples)
            if number_of_samples < 4:
                raise ValueError(
                    "ISO-6487 filtering requires at least 4 samples; "
                    f"received {number_of_samples}."
                )
            sample_rate = self.info.get(
                "Sampling interval"
            )  # Sampling interval in seconds
            if isinstance(sample_rate, bool) or not isinstance(
                sample_rate, (int, float)
            ):
                sample_rate = np.diff(self.data.index).mean()
                logger.debug(
                    f"Sampling interval not found in channel info. Set sampling interval to mean diff: {sample_rate}."
                )

            number_of_add_points = 0.01 / sample_rate
            number_of_add_points = int(
                min([max([number_of_add_points, 100]), number_of_samples - 1])
            )
            index_last_point = number_of_samples + 2 * number_of_add_points - 1

            # Initial condition
            filter_tab = np.zeros(index_last_point + 1)
            for i in range(
                number_of_add_points, number_of_add_points + number_of_samples
            ):
                filter_tab[i] = samples[i - number_of_add_points]

            for i in range(0, number_of_add_points):
                filter_tab[number_of_add_points - i - 1] = (
                    2 * samples[0] - samples[i + 1]
                )
                filter_tab[number_of_samples + number_of_add_points + i] = (
                    2 * samples[number_of_samples - 1]
                    - samples[number_of_samples - i - 2]
                )

            # Computer filter coefficients
            wd = 2 * np.pi * cfc / 0.6 * 1.25
            wa = np.tan(wd * sample_rate / 2.0)
            b0 = wa**2 / (1 + wa**2 + np.sqrt(2) * wa)
            b1 = 2 * b0
            b2 = b0
            a1 = -2 * (wa**2 - 1) / (1 + wa**2 + np.sqrt(2) * wa)
            a2 = (-1 + np.sqrt(2) * wa - wa**2) / (1 + wa**2 + np.sqrt(2) * wa)

            # Filter forward
            y1 = 0.0
            for i in range(0, 10):
                y1 = y1 + filter_tab[i]
            y1 = y1 / 10
            x2 = 0
            x1 = filter_tab[0]
            x0 = filter_tab[1]
            filter_tab[0] = y1
            filter_tab[1] = y1
            for i in range(2, index_last_point + 1):
                x2 = x1
                x1 = x0
                x0 = filter_tab[i]
                filter_tab[i] = (
                    b0 * x0
                    + b1 * x1
                    + b2 * x2
                    + a1 * filter_tab[i - 1]
                    + a2 * filter_tab[i - 2]
                )

            # Filter backward
            y1 = 0
            for i in range(index_last_point, index_last_point - 9 - 1, -1):
                y1 = y1 + filter_tab[i]
            y1 = y1 / 10
            x2 = 0
            x1 = filter_tab[index_last_point]
            x0 = filter_tab[index_last_point - 1]
            filter_tab[index_last_point] = y1
            filter_tab[index_last_point - 1] = y1
            for i in range(index_last_point - 2, 0 - 1, -1):
                x2 = x1
                x1 = x0
                x0 = filter_tab[i]
                filter_tab[i] = (
                    b0 * x0
                    + b1 * x1
                    + b2 * x2
                    + a1 * filter_tab[i + 1]
                    + a2 * filter_tab[i + 2]
                )

            # Filtering of samples
            for i in range(
                number_of_add_points, number_of_add_points + number_of_samples
            ):
                samples[i - number_of_add_points] = filter_tab[i]

            data = copy.deepcopy(self.data)
            data.iloc[:, 0] = samples

            info = copy.deepcopy(self.info)
            info.update({"Channel frequency class": cfc})

            if return_copy:
                return Channel(
                    code=self.code.set(filter_class=filter_class),
                    data=data,
                    unit=self.unit,
                    info=info,
                )
            else:
                self.code = self.code.set(filter_class=filter_class)
                self.data = data
                self.info = info
                return self

        elif method == "SAE-J211-1":
            input_values = self.get_data()
            sample_interval = self.info.get("Sampling interval")
            if isinstance(sample_interval, bool) or not isinstance(
                sample_interval, (int, float)
            ):
                sample_interval = np.diff(self.data.index).mean()
                logger.debug(
                    f"Sampling interval not found in channel info. Set sampling interval to mean diff: {sample_interval}."
                )
            wd = 2 * np.pi * cfc / 0.6 * 1.25
            wa = np.tan(wd * sample_interval / 2.0)
            a0 = wa**2 / (1 + wa**2 + np.sqrt(2) * wa)
            a1 = 2 * a0
            a2 = a0
            b1 = -2 * (wa**2 - 1) / (1 + wa**2 + np.sqrt(2) * wa)
            b2 = (-1 + np.sqrt(2) * wa - wa**2) / (1 + wa**2 + np.sqrt(2) * wa)

            # forward
            output_values = np.zeros(len(input_values))
            for i in range(2, len(input_values)):
                inp0 = input_values[i]
                inp1 = input_values[i - 1]
                inp2 = input_values[i - 2]

                out2 = output_values[i - 2]
                out1 = output_values[i - 1]

                output_values[i] = (
                    a0 * inp0 + a1 * inp1 + a2 * inp2 + b1 * out1 + b2 * out2
                )

            # backward
            input_values = output_values
            output_values = np.zeros(len(input_values))
            for i in range(len(input_values) - 3, 0, -1):
                inp0 = input_values[i]
                inp2 = input_values[i + 2]
                inp1 = input_values[i + 1]

                out2 = output_values[i + 2]
                out1 = output_values[i + 1]

                output_values[i] = (
                    a0 * inp0 + a1 * inp1 + a2 * inp2 + b1 * out1 + b2 * out2
                )

            # final
            data = copy.deepcopy(self.data)
            data.iloc[:, 0] = output_values

            info = copy.deepcopy(
                self.info
            )  # deepcopy: Info.update mutates in place (was aliasing self.info)
            info.update({"Channel frequency class": cfc})

            if return_copy:
                return Channel(
                    code=self.code.set(filter_class=filter_class),
                    data=data,
                    unit=self.unit,
                    info=info,
                )
            else:
                self.code = self.code.set(filter_class=filter_class)
                self.data = data
                self.info = info
                return self
        else:
            raise NotImplementedError

    def get_data(
        self,
        t=None,
        unit=None,
        method: str = "linear",
        fill_value: float | tuple[float, float] = (0.0, 0.0),
    ) -> np.ndarray:
        """
        Returns the samples as an array. If t is given, interpolate at those time(s);
        out-of-range times return the fill value. If t is scalar the result is a 0-d
        array (use get_value() when a plain float is wanted).

        Always returns an ``np.ndarray`` — scipy's interp1d yields a (0-d) array even for
        a scalar t, so the historical ``| float`` annotation never held.
        :param t: None (whole signal), a scalar time, or an array of times
        :param unit: target unit for conversion (None keeps the channel unit)
        :param method: Interpolation method
        :param fill_value:
        :return: np.ndarray
        """
        time_array = self.data.index.to_numpy()
        value_array = copy.deepcopy(self.data.iloc[:, 0].to_numpy())

        if unit is not None:
            value_array = self.unit.to(unit, value_array)  # pyright: ignore[reportArgumentType]

        if t is None:
            return value_array  # pyright: ignore[reportReturnType]

        # Interpolation (kinds like "linear" need at least 2 points (otherwise zero division and nan return value)
        if len(time_array) < 2:
            method = "nearest"
        return scipy_interpolate.interp1d(
            time_array,
            value_array,
            kind=method,
            fill_value=fill_value,  # pyright: ignore[reportArgumentType]
            bounds_error=False,
        )(t)  # pyright: ignore[reportArgumentType]

    def get_value(
        self, t: float, unit=None, method: str = "linear", fill_value: tuple = (0, 0)
    ) -> float:
        """
        Interpolated scalar sample at a single time t, as a plain Python float.

        Thin scalar-typed wrapper over get_data() for the (common) case where exactly one
        value is wanted, so callers need not unwrap a 0-d array.
        :param t: a single time
        :return: float
        """
        return float(
            self.get_data(t=t, unit=unit, method=method, fill_value=fill_value)
        )

    def get_info(self, *labels: str) -> InfoValue:
        """
        Get channel info by giving one or multiple label(s) to identify information.
        Regex or fnmatch patterns possible.
        :param labels: key to find information in dict
        :return: first match or None
        """
        for label in labels:
            for name, value in self.info:
                if fnmatch(name, label):
                    return value
                try:
                    if re.match(label, name):
                        return value
                except re.error:
                    continue
        return None

    def differentiate(self) -> Channel:
        """
        Return new Channel with differentiated data
        :return: Channel
        """
        new_data = copy.deepcopy(self.data)
        new_data.iloc[:, 0] = np.gradient(self.get_data(), self.data.index)

        new_code = self.code.differentiate()
        new_unit = Unit(self.unit) / "s"
        new_info = copy.deepcopy(self.info)
        new_info.update({"Dimension": new_code.physical_dimension})

        new_channel = Channel(new_code, new_data, unit=new_unit, info=new_info)
        return new_channel

    def integrate(self, x_0: float = 0) -> Channel:
        """
        Return new Channel with integrated data
        :param x_0: value at t=0
        :return: Channel
        """
        new_data = pd.DataFrame(
            cumulative_trapezoid(self.data.iloc[:, 0], self.data.index, initial=0),
            index=self.data.index,
        )
        new_code = self.code.integrate()

        # 1. Multiply by Unit("s") instead of raw string "s"
        new_unit = Unit(self.unit) * Unit("s")

        # 2. Deepcopy metadata to ensure source channel remains untouched
        new_info = copy.deepcopy(self.info) if self.info is not None else {}
        new_info["Dimension"] = new_code.physical_dimension

        new_channel = Channel(new_code, new_data, unit=new_unit, info=new_info)

        # 3. Cast 0-d ndarray from get_data(t=0) to a standard float
        initial_val = float(new_channel.get_data(t=0))
        new_channel -= initial_val
        new_channel += x_0

        return new_channel

    def adjust_to_range(self, target_range: tuple = (-45, 45), unit="deg") -> Channel:
        angle_0 = self.get_value(t=0, unit=unit)

        old_offset = None
        offset = 0
        while old_offset != offset:
            old_offset = offset
            if target_range[-1] < angle_0 + offset:
                offset -= target_range[-1] - target_range[0]
            if angle_0 + offset < target_range[0]:
                offset += target_range[-1] - target_range[0]

        return self + offset

    def write(self, xxx_path):
        with open(xxx_path, "w", encoding="utf-8") as xxx_file:
            self.info.update(
                {
                    "Channel code": self.code,
                    "Unit": self.unit.to_isomme(),
                    "Number of samples": len(self.data),
                }
            )
            if self.get_info("Reference channel", "") in ("implicit", ""):
                # TODO: Check if implicit if valid instead and create unique time channel otherwise?
                self.info.update(
                    {
                        "Time of first sample": float(self.data.index[0]),
                        "Sampling interval": float(np.mean(np.diff(self.data.index))),
                    }
                )
            if len(self.get_data()) > 1:
                self.info.update(
                    {
                        "First global maximum value": np.max(self.get_data()),
                        "Time of maximum value": self.data.index[
                            int(np.argmax(self.get_data()))
                        ],
                        "First global minimum value": np.min(self.get_data()),
                        "Time of minimum value": self.data.index[
                            int(np.argmin(self.get_data()))
                        ],
                    }
                )

            self.info.write(xxx_file)
            xxx_file.write(
                self.data.to_string(header=False, index=False).replace(" ", "")
            )
        return self

    def plot(self, *args, **kwargs) -> None:
        data = copy.deepcopy(self.data)
        data.index *= (
            1000  # Channel time is stored in seconds; display it in milliseconds.
        )

        dimension = self.get_info("Dimension")
        if dimension is None:
            dimension = (
                self.code.get_info().get("Physical Dimension")
                or self.code.physical_dimension
            )

        kwargs.setdefault("title", str(self.code))
        kwargs.setdefault("xlabel", "Time [ms]")
        kwargs.setdefault("ylabel", f"{dimension} [{self.unit}]")
        label = kwargs.pop("label", str(self.code))
        if len(data.columns) == 1:
            data.columns = [label]
        else:
            kwargs["label"] = label
        kwargs.setdefault("legend", False)
        kwargs.setdefault("grid", True)
        kwargs.setdefault("figsize", (10, 6))

        data.plot(*args, **kwargs)
        plt.tight_layout()
        plt.show()

    def scale_y(self, factor: float) -> Channel:
        self.data *= factor
        return self

    def scale_x(self, factor: float) -> Channel:
        self.data = pd.DataFrame(self.data.values, index=self.data.index * factor)
        return self

    def offset_y(self, offset: float) -> Channel:
        self.data += offset
        return self

    def auto_offset_y(self, t: float = 0) -> Channel:
        return self.offset_y(offset=-self.get_value(t=t))

    def offset_x(self, offset: float) -> Channel:
        self.data = pd.DataFrame(self.data.values, index=self.data.index + offset)
        return self

    def crop(self, x_min: float | None = None, x_max: float | None = None) -> Channel:
        self.data = self.data.truncate(before=x_min, after=x_max)  # pyright: ignore[reportArgumentType]
        return self

    # Operator methods
    def __eq__(self, other) -> bool:
        if not isinstance(other, Channel):
            return False

        if self.code != other.code:
            return False

        if self.unit.physical_type != other.unit.physical_type:
            return False

        if not self.data.index.equals(other.data.index):
            return False

        val_self = self.get_data()
        val_other = other.get_data(unit=self.unit)
        return np.allclose(val_self, val_other, rtol=1e-5, atol=1e-8, equal_nan=True)

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __neg__(self) -> Channel:
        return Channel(
            self.code,
            -self.data,
            self.unit,
            info=self.info + [("Calculation History", f"-1 * {self.code}")],
        )

    def __add__(self, other) -> Channel:
        if isinstance(other, Channel):
            t = time_intersect(self, other)
            if not self.unit.is_equivalent(other.unit):
                raise UnitConversionError(
                    f"Cannot add channels with incompatible units: {self.unit} and {other.unit}"
                )
            return Channel(
                code=self.code,
                data=pd.DataFrame(
                    self.get_data(t) + other.get_data(t, unit=self.unit), index=t
                ),
                unit=self.unit,
                info=self.info
                + [("Calculation History", f"{self.code} + {other.code}")],
            )
        elif isinstance(other, (int, float)):
            return Channel(
                code=self.code,
                data=self.data + other,
                unit=self.unit,
                info=self.info + [("Calculation History", f"{self.code} + {other}")],
            )
        return NotImplemented

    def __radd__(self, other) -> Channel:
        return self.__add__(other)

    def __sub__(self, other) -> Channel:
        if isinstance(other, Channel):
            t = time_intersect(self, other)
            if not self.unit.is_equivalent(other.unit):
                raise UnitConversionError(
                    f"Cannot subtract channels with incompatible units: {self.unit} and {other.unit}"
                )
            return Channel(
                code=self.code,
                data=pd.DataFrame(
                    self.get_data(t) - other.get_data(t, unit=self.unit), index=t
                ),
                unit=self.unit,
                info=self.info
                + [("Calculation History", f"{self.code} - {other.code}")],
            )
        elif isinstance(other, (int, float)):
            return Channel(
                code=self.code,
                data=self.data - other,
                unit=self.unit,
                info=self.info + [("Calculation History", f"{self.code} - {other}")],
            )
        return NotImplemented

    def __mul__(self, other):
        # NOTE: unlike __add__/__sub__, mul/div intentionally skip the physical_type
        # compatibility check — multiplying/dividing different physical types is valid
        # (e.g. force * distance = energy) and the resulting unit is computed accordingly.
        if isinstance(other, Channel):
            t = time_intersect(self, other)
            return Channel(
                code=self.code,
                data=pd.DataFrame(self.get_data(t=t) * other.get_data(t=t), index=t),
                unit=self.unit * other.unit,
                info=self.info
                + [("Calculation History", f"{self.code} * {other.code}")],
            )
        elif isinstance(other, (int, float)):
            return Channel(
                code=self.code,
                data=self.data * other,
                unit=self.unit,
                info=self.info + [("Calculation History", f"{self.code} * {other}")],
            )
        elif isinstance(other, Unit):
            return Channel(
                code=self.code,
                data=self.data,
                unit=self.unit * other,
                info=self.info + [("Calculation History", f"{self.code} * {other}")],
            )
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other) -> Channel:
        if isinstance(other, Channel):
            t = time_intersect(self, other)
            return Channel(
                code=self.code,
                data=pd.DataFrame(self.get_data(t=t) / other.get_data(t=t), index=t),
                unit=self.unit / other.unit,
                info=self.info
                + [("Calculation History", f"{self.code} / {other.code}")],
            )
        elif isinstance(other, (int, float)):
            return Channel(
                code=self.code,
                data=self.data / other,
                unit=self.unit,
                info=self.info + [("Calculation History", f"{self.code} / {other}")],
            )
        elif isinstance(other, Unit):
            return Channel(
                code=self.code,
                data=self.data,
                unit=self.unit / other,
                info=self.info + [("Calculation History", f"{self.code} / {other}")],
            )
        return NotImplemented

    def __pow__(self, power, modulo=None) -> Channel:
        if not isinstance(power, (int, float)):
            return NotImplemented

        if modulo is not None:
            if not isinstance(modulo, (int, float)):
                return NotImplemented
            if modulo == 0:
                raise ZeroDivisionError("modulo by zero")

            calculated_data = (self.data**power) % modulo
            history_str = f"pow({self.code}, {power}, {modulo})"
        else:
            calculated_data = self.data**power
            history_str = f"{self.code}^{power}"

        return Channel(
            code=self.code,
            data=calculated_data,
            unit=self.unit**power,
            info=self.info + [("Calculation History", history_str)],
        )

    def __abs__(self) -> Channel:
        return Channel(
            code=self.code,
            data=abs(self.data),
            unit=self.unit,
            info=self.info + [("Calculation History", f"abs({self.code})")],
        )


def create_sample(
    code: str = "SAMPLE??????????",
    t_range: tuple[float, float, int] = (0, 0.2, 2001),
    y_range: tuple[float, float] = (0, 10),
    mode: Literal["linear", "sin", "pulse"] = "sin",
    unit: str | Unit | None = None,
    frequency: float | None = None,
    noise: float = 0.0,
    noise_per: float = 0.0,
    seed: int | None = 0,
    phase_offset: float = 0.0,
) -> Channel:
    """Create a deterministic sample channel for examples and tests.

    ``linear`` and ``sin`` span the two values in ``y_range``. ``pulse`` treats
    them as ``(baseline, peak)`` and creates a smooth, crash-like event that
    starts and finishes at the baseline. An optional frequency adds modest
    low-frequency structure to a pulse, or controls the frequency of a sine.
    ``noise`` is the standard deviation of Gaussian noise in the channel unit;
    use ``seed=None`` only when deliberately non-reproducible data is wanted.

    :param code: 16-character ISO-MME channel code.
    :param t_range: Start time, end time and number of samples.
    :param y_range: Minimum/maximum for linear and sine modes, or
        baseline/peak for pulse mode.
    :param mode: Base signal shape.
    :param unit: Channel unit.
    :param frequency: Frequency in Hz. A sine defaults to one cycle over the
        time range; a pulse has no modulation unless a frequency is supplied.
    :param phase_offset: Phase offset in radians for sine samples.
    :param noise: Standard deviation of additive Gaussian noise.
    :param noise_per: Standard deviation of additive Gaussian noise given as percentage from y-range
    :param seed: Random seed used for noise. The default is reproducible.
    :return: Sample channel.
    """
    resolved_code = Code(code)

    if unit is None:
        default_unit = resolved_code.get_default_unit()
        resolved_unit = default_unit if default_unit is not None else Unit("1")
    else:
        resolved_unit = Unit(unit)

    t_start, t_end, sample_count = t_range
    if sample_count < 2:
        raise ValueError("t_range must request at least two samples")
    if t_end <= t_start:
        raise ValueError("t_range end must be greater than its start")
    if frequency is not None and frequency <= 0:
        raise ValueError("frequency must be greater than zero")
    if noise < 0:
        raise ValueError("noise must not be negative")

    time_array = np.linspace(t_start, t_end, sample_count)
    baseline, peak = y_range
    duration = t_end - t_start

    if mode == "linear":
        value_array = np.linspace(baseline, peak, sample_count)
    elif mode == "sin":
        sine_frequency = 1 / duration if frequency is None else frequency
        phase = 2 * np.pi * sine_frequency * (time_array - t_start) + phase_offset
        value_array = (peak - baseline) / 2 * np.sin(phase) + sum(y_range) / 2
    elif mode == "pulse":
        # A raised-cosine pulse occupies the middle 40 % of the sample. It is
        # smooth at both ends, so filtering and differentiation do not see
        # artificial steps. Optional modulation adds real-signal-like low
        # frequency content without changing the baseline outside the event.
        relative_time = (time_array - t_start) / duration
        pulse_phase = (relative_time - 0.3) / 0.4
        active = (pulse_phase >= 0) & (pulse_phase <= 1)
        shape = np.zeros(sample_count)
        shape[active] = np.sin(np.pi * pulse_phase[active]) ** 2
        if frequency is not None:
            centre_time = t_start + duration / 2
            modulation = 0.9 + 0.1 * np.cos(
                2 * np.pi * frequency * (time_array - centre_time)
            )
            shape *= modulation
        value_array = baseline + (peak - baseline) * shape
    else:
        raise ValueError(f"mode={mode} does not exist.")

    if noise:
        value_array += np.random.default_rng(seed).normal(0.0, noise, sample_count)

    if noise_per:
        noise_from_per = noise_per * abs(peak - baseline)
        value_array += np.random.default_rng(seed).normal(
            0.0, noise_from_per, sample_count
        )

    data = pd.DataFrame({"Time": time_array, "SAMPLE": value_array}).set_index("Time")
    return Channel(
        code=resolved_code,
        unit=resolved_unit,
        data=data,
        info=[("Sampling interval", time_array[1] - time_array[0])],
    )


def time_intersect(*channels: Channel, interpolate: bool = False) -> np.ndarray:
    """
    Returns intersection of time-array of given channels.
    :param channels: Channel objects
    :param interpolate: Apply interpolation for time points in between
    :return: time array
    """
    if len(channels) == 0:
        return np.array([])
    time_array = channels[0].data.index.to_numpy()
    for channel in channels[1:]:
        if interpolate:
            t_min = np.max([np.min(time_array), np.min(channel.data.index)])
            t_max = np.min([np.max(time_array), np.max(channel.data.index)])
            time_array = np.sort(np.concatenate([time_array, channel.data.index]))
            time_array = time_array[(time_array >= t_min) * (time_array <= t_max)]
        else:
            time_array = np.intersect1d(time_array, channel.data.index)
    return time_array
