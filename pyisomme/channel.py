from __future__ import annotations

from pyisomme.unit import Unit, g0
from pyisomme.info import Info
from pyisomme.code import Code

import re
import pandas as pd
import numpy as np
import logging
import warnings
from fnmatch import fnmatch
from scipy.integrate import cumulative_trapezoid
from scipy import interpolate as scipy_interpolate
import copy
from typing import Literal
from astropy.units import CompositeUnit


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

    def __init__(self, code: str | Code, data: pd.DataFrame, unit: str | Unit | None = None, info: list | dict | None = None):
        self.set_code(code)
        self.data = data
        self.set_unit(unit)
        self.info = Info([]) if info is None else Info(info) if isinstance(info, list) else Info([(n, v) for n, v in info.items()])

    def __str__(self):
        return self.code

    def __repr__(self):
        return f"Channel(code={self.code})"

    def set_code(self, new_code: str | Code | None = None, **code_components) -> Channel:
        if new_code is None:  # if only components are set
            assert self.code is not None
            new_code = self.code

        if not re.fullmatch(r"[a-zA-Z0-9?]{16}", new_code):
            if re.search(r"[^a-zA-Z0-9]", new_code):
                logger.warning(f"Code '{new_code}' contains invalid characters which will be removed")
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
            raise AttributeError(f"{self}. Not possible to convert units when current unit is None.")

        self.data.iloc[:, :] = self.unit.to(other=new_unit, value=self.data.to_numpy()) # type: ignore
        self.unit = Unit(new_unit)
        return self

    # Cutoff frequency (Hz) of each standard ISO filter class.
    _FILTER_CLASS_CFC = {"0": np.inf, "A": 1000, "B": 600, "C": 180, "D": 60}
    _CFC_METHODS = Literal["ISO-6487", "SAE-J211-1"]

    def cfc(self, filter_class: str, method: _CFC_METHODS = "ISO-6487", return_copy: bool = True) -> Channel:
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
                DeprecationWarning, stacklevel=2,
            )
            return self.cfc_hz(filter_class, method=method, return_copy=return_copy)
        if filter_class not in self._FILTER_CLASS_CFC:
            raise ValueError(
                f"Unknown filter class {filter_class!r}; expected one of "
                f"{sorted(self._FILTER_CLASS_CFC)}."
            )
        return self._apply_cfc(self._FILTER_CLASS_CFC[filter_class], filter_class, method, return_copy)

    def cfc_hz(self, freq: float, method: _CFC_METHODS = "ISO-6487", return_copy: bool = True) -> Channel:
        """
        Apply a filter to smooth curves, selected by an explicit cutoff **frequency in Hz**.
        The nearest standard ISO filter class (or "S" for a non-standard cutoff) is recorded
        in the resulting channel code.
        :param freq: cutoff frequency in Hz (np.inf = no filtering)
        :param method:
        :param return_copy:
        :return:
        """
        filter_class = next((fc for fc, hz in self._FILTER_CLASS_CFC.items() if hz == freq), "S")
        return self._apply_cfc(freq, filter_class, method, return_copy)

    def _apply_cfc(self, cfc: float, filter_class: str, method: _CFC_METHODS, return_copy: bool) -> Channel:
        # Check if Channel is already filtered
        if filter_class == "0":
            return copy.deepcopy(self) if return_copy else self
        elif (filter_class == "A" and self.code.filter_class in ("A", "B", "C", "D") or
              filter_class == "B" and self.code.filter_class in ("B", "C", "D") or
              filter_class == "C" and self.code.filter_class in ("C", "D") or
              filter_class == "D" and self.code.filter_class in ("D",)):
            logger.warning("No filtering applied. Channel is already filtered.")
            return copy.deepcopy(self) if return_copy else self

        # Calculation
        if method == "ISO-6487":
            # Variables used
            samples = self.get_data()
            number_of_samples = len(samples)
            sample_rate = self.info.get("Sampling interval")
            if sample_rate is None:
                sample_rate = np.diff(self.data.index).mean()
                logger.debug(f"Sampling interval not found in channel info. Set sampling interval to mean diff: {sample_rate}.")

            number_of_add_points = 0.01 * sample_rate
            number_of_add_points = min([max([number_of_add_points, 100]), number_of_samples - 1])
            index_last_point = number_of_samples + 2 * number_of_add_points - 1

            # Initial condition
            filter_tab = np.zeros(index_last_point + 1)
            for i in range(number_of_add_points, number_of_add_points + number_of_samples):
                filter_tab[i] = samples[i - number_of_add_points]

            for i in range(0, number_of_add_points):
                filter_tab[number_of_add_points - i - 1] = 2 * samples[0] - samples[i+1]
                filter_tab[number_of_samples + number_of_add_points + i] = 2 * samples[number_of_samples-1] - samples[number_of_samples - i - 2]

            # Computer filter coefficients
            wd = 2 * np.pi * cfc / 0.6 * 1.25
            wa = np.tan(wd * sample_rate / 2.0)
            b0 = wa**2 / (1 + wa**2 + np.sqrt(2) * wa)
            b1 = 2 * b0
            b2 = b0
            a1 = -2 * (wa**2 - 1) / (1 + wa**2 + np.sqrt(2) * wa)
            a2 = (-1 + np.sqrt(2)*wa - wa**2) / (1 + wa**2 + np.sqrt(2) * wa)

            # Filter forward
            y1 = 0
            for i in range(0, 10):
                y1 = y1 + filter_tab[i]
            y1 = y1/10
            x2 = 0
            x1 = filter_tab[0]
            x0 = filter_tab[1]
            filter_tab[0] = y1
            filter_tab[1] = y1
            for i in range(2, index_last_point+1):
                x2 = x1
                x1 = x0
                x0 = filter_tab[i]
                filter_tab[i] = b0 * x0 + b1 * x1 + b2 * x2 + a1 * filter_tab[i - 1] + a2 * filter_tab[i - 2]

            # Filter backward
            y1 = 0
            for i in range(index_last_point, index_last_point-9-1, -1):
                y1 = y1 + filter_tab[i]
            y1 = y1/10
            x2 = 0
            x1 = filter_tab[index_last_point]
            x0 = filter_tab[index_last_point-1]
            filter_tab[index_last_point] = y1
            filter_tab[index_last_point-1] = y1
            for i in range(index_last_point-2, 0-1, -1):
                x2 = x1
                x1 = x0
                x0 = filter_tab[i]
                filter_tab[i] = b0 * x0 + b1 * x1 + b2 * x2 + a1 * filter_tab[i + 1] + a2 * filter_tab[i + 2]

            # Filtering of samples
            for i in range(number_of_add_points, number_of_add_points + number_of_samples):
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
                    info=info
                )
            else:
                self.code = self.code.set(filter_class=filter_class)
                self.data = data
                self.info = info
                return self

        elif method == "SAE-J211-1":
            input_values = self.get_data()
            sample_interval = self.info.get("Sampling interval")
            if sample_interval is None:
                sample_interval = np.diff(self.data.index).mean()
                logger.debug(f"Sampling interval not found in channel info. Set sampling interval to mean diff: {sample_interval}.")
            wd = 2 * np.pi * cfc / 0.6 * 1.25
            wa = np.tan(wd * sample_interval / 2.0)
            a0 = wa**2 / (1 + wa**2 + np.sqrt(2) * wa)
            a1 = 2 * a0
            a2 = a0
            b1 = -2 * (wa**2 - 1) / (1 + wa**2 + np.sqrt(2) * wa)
            b2 = (-1 + np.sqrt(2)*wa - wa**2) / (1 + wa**2 + np.sqrt(2) * wa)

            # forward
            output_values = np.zeros(len(input_values))
            for i in range(2, len(input_values)):
                inp0 = input_values[i]
                inp1 = input_values[i - 1]
                inp2 = input_values[i - 2]

                out2 = output_values[i - 2]
                out1 = output_values[i - 1]

                output_values[i] = a0 * inp0 + a1 * inp1 + a2 * inp2 + b1 * out1 + b2 * out2

            # backward
            input_values = output_values
            output_values = np.zeros(len(input_values))
            for i in range(len(input_values)-3, 0, -1):
                inp0 = input_values[i]
                inp2 = input_values[i + 2]
                inp1 = input_values[i + 1]

                out2 = output_values[i + 2]
                out1 = output_values[i + 1]

                output_values[i] = a0 * inp0 + a1 * inp1 + a2 * inp2 + b1 * out1 + b2 * out2

            # final
            data = copy.deepcopy(self.data)
            data.iloc[:, 0] = output_values

            info = copy.deepcopy(self.info)  # deepcopy: Info.update mutates in place (was aliasing self.info)
            info.update({"Channel frequency class": cfc})

            if return_copy:
                return Channel(
                    code=self.code.set(filter_class=filter_class),
                    data=data,
                    unit=self.unit,
                    info=info
                )
            else:
                self.code = self.code.set(filter_class=filter_class)
                self.data = data
                self.info = info
                return self
        else:
            raise NotImplementedError

    def get_data(self, t=None, unit=None, method: str = "linear", fill_value: float | tuple[float, float] = (0.0, 0.0)) -> np.ndarray:
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
            value_array = self.unit.to(unit, value_array)  # type: ignore

        if t is None:
            return value_array  # type: ignore

        # Interpolation (kinds like "linear" need at least 2 points (otherwise zero division and nan return value)
        if len(time_array) < 2:
            method = "nearest"
        return scipy_interpolate.interp1d(time_array, value_array, kind=method, fill_value=fill_value, bounds_error=False)(t)

    def get_value(self, t: float, unit=None, method: str = "linear", fill_value: tuple = (0, 0)) -> float:
        """
        Interpolated scalar sample at a single time t, as a plain Python float.

        Thin scalar-typed wrapper over get_data() for the (common) case where exactly one
        value is wanted, so callers need not unwrap a 0-d array.
        :param t: a single time
        :return: float
        """
        return float(self.get_data(t=t, unit=unit, method=method, fill_value=fill_value))

    def get_info(self, *labels: str) -> str | None:
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
            index=self.data.index
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
                offset -= (target_range[-1] - target_range[0])
            if angle_0 + offset < target_range[0]:
                offset += (target_range[-1] - target_range[0])

        return self + offset

    def write(self, xxx_path):
        with open(xxx_path, "w") as xxx_file:
            self.info.update({"Channel code": self.code,
                              "Unit": self.unit,
                              "Number of samples": len(self.data)})
            if self.get_info("Reference channel", "") in ("implicit", ""):
                # TODO: Check if implicit if valid instead and create unique time channel otherwise?
                self.info.update({
                    "Time of first sample": self.data.index[0],
                    "Sampling interval": np.mean(np.diff(self.data.index)),
                })
            if len(self.get_data()) > 1:
                self.info.update({
                    "First global maximum value": np.max(self.get_data()),
                    "Time of maximum value": self.data.index[int(np.argmax(self.get_data()))],
                    "First global minimum value": np.min(self.get_data()),
                    "Time of minimum value": self.data.index[int(np.argmin(self.get_data()))],
                })

            self.info.write(xxx_file)
            xxx_file.write(self.data.to_string(header=False, index=False).replace(" ", ""))
        return self

    def plot(self, *args, **kwargs) -> None:
        self.data.plot(*args, **kwargs).get_figure().show()

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
        return self.offset_y(offset=self.get_value(t=t))

    def offset_x(self, offset: float) -> Channel:
        self.data = pd.DataFrame(self.data.values, index=self.data.index + offset)
        return self

    def crop(self, x_min: float | None = None, x_max: float | None = None) -> Channel:
        self.data = self.data.truncate(before=x_min, after=x_max)  # type: ignore[arg-type]
        return self

    # Operator methods
    def __eq__(self, other) -> bool:
        if not isinstance(other, Channel):
            return False

        # # Check code identity (optional, if code is part of channel equality)
        # if getattr(self, "code", None) != getattr(other, "code", None):
        #     return False

        # Unit compatibility check
        if self.unit.physical_type != other.unit.physical_type:
            return False

        # Index / timestamp alignment check
        if not self.data.index.equals(other.data.index):
            return False

        # Compare values with floating-point tolerance using unit conversion
        try:
            val_self = self.get_data()
            val_other = other.get_data(unit=self.unit)
            return bool(np.allclose(val_self, val_other, rtol=1e-5, atol=1e-8, equal_nan=True))
        except Exception:
            return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __neg__(self):
        return Channel(self.code,
                       -self.data,
                       self.unit,
                       info=self.info + [("Calculation History", f"-1 * {self.code}")])

    def __add__(self, other) -> Channel:
        if isinstance(other, Channel):
            t = time_intersect(self, other)
            if self.unit.physical_type == other.unit.physical_type:
                return Channel(code=self.code,
                               data=pd.DataFrame(self.get_data(t) + other.get_data(t, unit=self.unit), index=t),
                               unit=self.unit,
                               info=self.info + [("Calculation History", f"{self.code} + {other.code}")])
            else:
                logger.warning(f"Adding channels with non compatible physical units: {self.unit} and {other.unit}")
                return Channel(code=self.code,
                               data=pd.DataFrame(self.get_data(t=t) + other.get_data(t=t), index=t),
                               unit=self.unit,
                               info=self.info + [("Calculation History", f"{self.code} + {other.code}")])
        elif isinstance(other, (int, float)):
            return Channel(code=self.code,
                           data=self.data + other,
                           unit=self.unit,
                           info=self.info + [("Calculation History", f"{self.code} + {other}")])
        return NotImplemented

    def __radd__(self, other) -> Channel:
        return self.__add__(other)

    def __sub__(self, other) -> Channel:
        if isinstance(other, Channel):
            t = time_intersect(self, other)
            if self.unit.physical_type == other.unit.physical_type:
                return Channel(code=self.code,
                               data=pd.DataFrame(self.get_data(t) - other.get_data(t, unit=self.unit), index=t),
                               unit=self.unit,
                               info=self.info + [("Calculation History", f"{self.code} - {other.code}")])
            else:
                logger.warning(f"Subtracting channels with non compatible physical units: {self.unit} and {other.unit}")
                return Channel(code=self.code,
                               data=pd.DataFrame(self.get_data(t=t) - other.get_data(t=t), index=t),
                               unit=self.unit,
                               info=self.info + [("Calculation History", f"{self.code} - {other.code}")])
        elif isinstance(other, (int, float)):
            return Channel(code=self.code,
                           data=self.data - other,
                           unit=self.unit,
                           info=self.info + [("Calculation History", f"{self.code} - {other}")])
        return NotImplemented

    def __mul__(self, other):
        # NOTE: unlike __add__/__sub__, mul/div intentionally skip the physical_type
        # compatibility check — multiplying/dividing different physical types is valid
        # (e.g. force * distance = energy) and the resulting unit is computed accordingly.
        if isinstance(other, Channel):
            t = time_intersect(self, other)
            return Channel(code=self.code,
                           data=pd.DataFrame(self.get_data(t=t) * other.get_data(t=t), index=t),
                           unit=self.unit * other.unit,
                           info=self.info + [("Calculation History", f"{self.code} * {other.code}")])
        elif isinstance(other, (int, float)):
            return Channel(code=self.code,
                           data=self.data * other,
                           unit=self.unit,
                           info=self.info + [("Calculation History", f"{self.code} * {other}")])
        elif isinstance(other, Unit):
            return Channel(code=self.code,
                           data=self.data,
                           unit=self.unit * other,
                           info=self.info + [("Calculation History", f"{self.code} * {other}")])
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other) -> Channel:
        if isinstance(other, Channel):
            t = time_intersect(self, other)
            return Channel(code=self.code,
                           data=pd.DataFrame(self.get_data(t=t) / other.get_data(t=t), index=t),
                           unit=self.unit / other.unit,
                           info=self.info + [("Calculation History", f"{self.code} / {other.code}")])
        elif isinstance(other, (int, float)):
            return Channel(code=self.code,
                           data=self.data / other,
                           unit=self.unit,
                           info=self.info + [("Calculation History", f"{self.code} / {other}")])
        elif isinstance(other, Unit):
            return Channel(code=self.code,
                           data=self.data,
                           unit=self.unit / other,
                           info=self.info + [("Calculation History", f"{self.code} / {other}")])
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
            unit=self.unit,
            info=self.info + [("Calculation History", history_str)],
        )

    def __abs__(self) -> Channel:
        return Channel(code=self.code,
                       data=abs(self.data),
                       unit=self.unit,
                       info=self.info + [("Calculation History", f"abs({self.code})")])


def create_sample(code: str = "SAMPLE??????????",
                  t_range: tuple = (0, 0.1, 1000),
                  y_range: tuple = (0, 10),
                  mode: str = "sin",
                  unit: str | Unit = "1") -> Channel:
    """
    Create a sample Channel object for testing purposes.
    :param code: channel code (str)
    :param t_range: Time range (min, max, num)
    :param y_range: y-Range (min, max)
    :param mode: function type
    :param unit:
    :return: Channel
    """
    time_array = np.linspace(*t_range)
    n = len(time_array)

    # y-data
    if mode == "linear":
        value_array = np.linspace(y_range[0], y_range[1], n)
    elif mode == "sin":
        x = np.linspace(0, 2*np.pi, n)
        value_array = abs(y_range[1] - y_range[0])/2 * np.sin(x) + sum(y_range)/2
    else:
        raise ValueError(f"mode={mode} does not exist.")

    data = pd.DataFrame({"Time": time_array, "SAMPLE": value_array}).set_index("Time")
    return Channel(code, data, unit, info=[("Sampling interval", np.diff(time_array)[0])])


def time_intersect(*channels: Channel, interpolate: bool = False) -> np.ndarray:
    """
    Returns intersection of time-array of given channels.
    :param channels: Channel objects
    :param interpolate: Apply interpolation for time points in between
    :return: time array
    """
    if len(channels) == 0:
        return np.array([])
    time_array = channels[0].data.index
    for channel in channels[1:]:
        if interpolate:
            t_min = np.max([np.min(time_array), np.min(channel.data.index)])
            t_max = np.min([np.max(time_array), np.max(channel.data.index)])
            time_array = np.sort(np.concatenate([time_array, channel.data.index]))
            time_array = time_array[(time_array >= t_min) * (time_array <= t_max)]
        else:
            time_array = np.intersect1d(time_array, channel.data.index)
    return time_array
