from __future__ import annotations

from pyisomme.unit import Unit, g0
from pyisomme.info import Info
from pyisomme.code import Code

import re
import pandas as pd
import numpy as np
import logging
from fnmatch import fnmatch
from scipy.integrate import cumulative_trapezoid
import copy
from astropy.units import CompositeUnit


logger = logging.getLogger(__name__)


class Channel:
    code: Code
    data: pd.DataFrame
    unit: Unit
    info: Info

    def __init__(self, code: str | Code, data: pd.DataFrame, unit: str | Unit = None, info: list | dict = None):
        self.set_code(code)
        self.data = data
        self.set_unit(unit)
        self.info = Info([]) if info is None else Info(info) if isinstance(info, list) else Info([(n, v) for n, v in info.items()])

    def __str__(self):
        return self.code

    def __repr__(self):
        return f"Channel(code={self.code})"

    def set_code(self, new_code: str | Code = None, **code_components) -> Channel:
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
                new_unit = g0
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
        self.data.iloc[:, :] = (self.data.to_numpy() * self.unit).to(new_unit).to_value()
        self.unit = Unit(new_unit)
        return self

    def cfc(self, value: int | str, method="ISO-6487", return_copy: bool = True) -> Channel:
        """
        Apply a filter to smooth curves.
        REFERENCES:
        - Appendix C of references/SAE-J211-1-MAR95/sae.j211-1.1995.pdf
        - Annex A of references/ISO-6487/ISO-6487-2015.pdf
        :param value:
        :param method:
        :param return_copy:
        :return:
        """
        if isinstance(value, str):
            filter_class = value
            cfc = None
        elif isinstance(value, int):
            filter_class = None
            cfc = value
        else:
            raise ValueError

        # Convert Filter-Class to cfc value
        if cfc is None:
            if filter_class == "0":
                cfc = np.inf
            elif filter_class == "A":
                cfc = 1000
            elif filter_class == "B":
                cfc = 600
            elif filter_class == "C":
                cfc = 180
            elif filter_class == "D":
                cfc = 60
            else:
                raise NotImplementedError

        if filter_class is None:
            if np.isinf(cfc):
                filter_class = "0"
            elif cfc == 1000:
                filter_class = "A"
            elif cfc == 600:
                filter_class = "B"
            elif cfc == 180:
                filter_class = "C"
            elif cfc == 60:
                filter_class = "D"
            else:
                filter_class = "S"

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

            info = self.info
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

    def get_data(self, t=None, unit=None) -> np.ndarray | float:
        """
        Returns Value at time t. If t is out of recorded range, zero will be returned
        If t between timesteps --> Interpolation
        :param t:
        :param unit:
        :return:
        """
        time_array = self.data.index.to_numpy()
        value_array = self.data.iloc[:, 0].to_numpy()

        # Unit conversion
        if unit is not None:
            old_unit = self.unit
            if isinstance(old_unit, CompositeUnit) or True:
                if not isinstance(unit, Unit):
                    unit = Unit(unit)
                value_array = (value_array * old_unit).to(unit).to_value()
            else:
                print(type(old_unit))
                logger.error("Could not determine old unit. No conversion will be performed.")

        if t is None:
            return value_array

        # Interpolation
        return np.interp(t, time_array, value_array, left=0, right=0)

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
        new_info = self.info
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
        new_unit = Unit(self.unit) * "s"
        new_info = self.info
        new_info.update({"Dimension": new_code.physical_dimension})

        new_channel = Channel(new_code, new_data, unit=new_unit, info=new_info)
        new_channel -= new_channel.get_data(t=0)
        new_channel += x_0
        return new_channel

    def adjust_to_range(self, target_range: tuple = (-45, 45), unit="deg") -> Channel:
        angle_0 = self.get_data(t=0, unit=unit)

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
                              "Number of samples": len(self.data)})
            if self.get_info("Reference channel", "") in ("implicit", ""):
                self.info.update({
                    "Time of first sample": self.data.index[0],
                    "Sampling interval": np.mean(np.diff(self.data.index)),
                })
            if len(self.get_data()) > 1:
                self.info.update({
                    "First global maximum value": np.max(self.get_data()),
                    "Time of maximum value": self.data.index[np.argmax(self.get_data())],
                    "First global minimum value": np.min(self.get_data()),
                    "Time of minimum value": self.data.index[np.argmin(self.get_data())],
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
        return self.offset_y(offset=self.get_data(t=t))

    def offset_x(self, offset: float) -> Channel:
        self.data = pd.DataFrame(self.data.values, index=self.data.index + offset)
        return self

    def crop(self, x_min: float = None, x_max: float = None) -> Channel:
        self.data = self.data.truncate(before=x_min, after=x_max)
        return self

    # Operator methods
    def __eq__(self, other):
        if isinstance(other, Channel):
            if self.unit.physical_type == other.unit.physical_type:
                return self.data.equals(other.convert_unit(self.unit).data)
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __neg__(self):
        return Channel(self.code,
                       -self.data,
                       self.unit,
                       info=self.info + [("Calculation History", f"-1 * {self.code}")])

    def __add__(self, other):
        if isinstance(other, Channel):
            t = time_intersect(self, other)
            if self.unit.physical_type == other.unit.physical_type:
                return Channel(code=self.code,
                               data=pd.DataFrame(self.get_data(t) + other.get_data(t, unit=self.unit), index=t),
                               unit=self.unit,
                               info=self.info + [("Calculation History", f"{self.code} - {other.code}")])
            else:
                logger.warning(f"Adding channels with non compatible physical units: {self.unit} and {other.unit}")
                return Channel(code=self.code,
                               data=pd.DataFrame(self.get_data(t=t) + other.get_data(t=t), index=t),
                               unit=self.unit,
                               info=self.info + [("Calculation History", f"{self.code} - {other.code}")])
        else:
            return Channel(code=self.code,
                           data=self.data + other,
                           unit=self.unit,
                           info=self.info + [("Calculation History", f"{self.code} - {other}")])

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
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
        else:
            return Channel(code=self.code,
                           data=self.data - other,
                           unit=self.unit,
                           info=self.info + [("Calculation History", f"{self.code} - {other}")])

    def __mul__(self, other):
        if isinstance(other, Channel):
            t = time_intersect(self, other)
            return Channel(code=self.code,
                           data=pd.DataFrame(self.get_data(t=t) * other.get_data(t=t), index=t),
                           unit=self.unit * other.unit,
                           info=self.info + [("Calculation History", f"{self.code} / {other.code}")])
        else:
            return Channel(code=self.code,
                           data=self.data * other,
                           unit=self.unit,
                           info=self.info + [("Calculation History", f"{self.code} / {other}")])

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, Channel):
            t = time_intersect(self, other)
            return Channel(code=self.code,
                           data=pd.DataFrame(self.get_data(t=t) / other.get_data(t=t), index=t),
                           unit=self.unit / other.unit,
                           info=self.info + [("Calculation History", f"{self.code} / {other.code}")])
        else:
            return Channel(code=self.code,
                           data=self.data / other,
                           unit=self.unit,
                           info=self.info + [("Calculation History", f"{self.code} / {other}")])

    def __pow__(self, power, modulo=None):
        return Channel(code=self.code,
                       data=self.data**power,
                       unit=self.unit,
                       info=self.info + [("Calculation History", f"{self.code}^{power}")])

    def __abs__(self):
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


def time_intersect(*channels: Channel) -> np.ndarray:
    """
    Returns intersection of time-array of given channels.
    :param channels: Channel objects
    :return: time array
    """
    if len(channels) == 0:
        return np.array([])
    time_array = channels[0].data.index
    for channel in channels[1:]:
        time_array = np.intersect1d(time_array, channel.data.index)
    return time_array
