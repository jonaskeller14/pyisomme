from __future__ import annotations

from pyisomme.unit import Unit, g0
from pyisomme.info import Info

import re
import pandas as pd
import numpy as np
import logging
from fnmatch import fnmatch
from pathlib import Path
import xml.etree.ElementTree as ET
from scipy.integrate import cumulative_trapezoid
import copy
from astropy.units import CompositeUnit


logger = logging.getLogger(__name__)


class Code(str):
    def __new__(cls, code):
        assert re.fullmatch(r"[a-zA-Z0-9?]{16}", code), \
            "Invalid code. Code must be 16 characters long, only letters and digits."
        return super(Code, cls).__new__(cls, code)

    def __init__(self, code: str):
        super().__init__()

        self.test_object: str = code[0]
        self.position: str = code[1]
        self.main_location: str = code[2:6]
        self.fine_location_1: str = code[6:8]
        self.fine_location_2: str = code[8:10]
        self.fine_location_3: str = code[10:12]
        self.physical_dimension: str = code[12:14]
        self.direction: str = code[14]
        self.filter_class: str = code[15]

    def set(self,
            test_object: str = None,
            position: str = None,
            main_location: str = None,
            fine_location_1: str = None,
            fine_location_2: str = None,
            fine_location_3: str = None,
            physical_dimension: str = None,
            direction: str = None,
            filter_class: str = None) -> Code:
        if test_object is None:
            test_object = self.test_object
        if position is None:
            position = self.position
        if main_location is None:
            main_location = self.main_location
        if fine_location_1 is None:
            fine_location_1 = self.fine_location_1
        if fine_location_2 is None:
            fine_location_2 = self.fine_location_2
        if fine_location_3 is None:
            fine_location_3 = self.fine_location_3
        if physical_dimension is None:
            physical_dimension = self.physical_dimension
        if direction is None:
            direction = self.direction
        if filter_class is None:
            filter_class = self.filter_class

        return Code(f"{test_object}{position}{main_location}{fine_location_1}{fine_location_2}{fine_location_3}{physical_dimension}{direction}{filter_class}")

    def get_info(self) -> dict:
        """
        Data from 'channel_codes.xml'
        :return: dict with code attributes
        """
        info = {}
        root = ET.parse(Path(__file__).parent.joinpath("channel_codes.xml")).getroot()
        for element in root.findall("Codification/Element"):
            for channel in element.findall(".//Channel"):
                if fnmatch(str(self), channel.get("code")):
                    info[element.get("name")] = channel.get("description")
                    break
            if element.get("name") not in info:
                logger.warning(f"'{element.get('name')}' of '{self}' not valid.")
        return info

    def get_default_unit(self) -> Unit | None:
        """
        Returns SI-Unit (default-unit) of Dimension (part of the channel code).
        Default Units are stored in 'channel_codes.xml'
        :return: Unit or None
        """
        root = ET.parse(Path(__file__).parent.joinpath("channel_codes.xml")).getroot()
        for element in root.findall("Codification/Element[@name='Physical Dimension']"):
            for channel in element.findall(".//Channel"):
                if fnmatch(str(self), channel.get("code")):
                    default_unit = channel.get("default_unit")
                    if default_unit is not None:
                        return Unit(default_unit)
        return None

    def integrate(self):
        """
        Integrate Dimension of Channel code.
        :return: str or Error is raised
        """
        replace_patterns = (
            (r"(............)AC(..)", r"\1VE\2"),
            (r"(............)VE(..)", r"\1DS\2"),
            (r"(............)AA(..)", r"\1AV\2"),
            (r"(............)AV(..)", r"\1AN\2"),
        )
        for replace_pattern in replace_patterns:
            if re.search(replace_pattern[0], self):
                return Code(re.sub(*replace_pattern, self))
        raise NotImplementedError("Could not integrate code")

    def differentiate(self):
        """
        Differentiate Dimension of Channel code.
        :return: str or Error is raised
        """
        replace_patterns = (
            (r"(............)DS(..)", r"\1VE\2"),
            (r"(............)DC(..)", r"\1VE\2"),
            (r"(............)VE(..)", r"\1AC\2"),
            (r"(............)AV(..)", r"\1AA\2"),
            (r"(............)AN(..)", r"\1AV\2"),
        )
        for replace_pattern in replace_patterns:
            if re.search(replace_pattern[0], self):
                return Code(re.sub(*replace_pattern, self))
        raise NotImplementedError("Could not differentiate code")

    def is_valid(self) -> bool:
        """
        Data from 'channel_codes.xml'
        :return: True if code contains valid parts and is as a whole valid
        """
        if len(self) != 16:
            logger.error("Code length not 16 characters.")
            return False

        root = ET.parse(Path(__file__).parent.joinpath("channel_codes.xml")).getroot()
        for element in root.findall("Codification/Element"):
            match = False
            for channel in element.findall(".//Channel"):
                if fnmatch(str(self), channel.get("code")):
                    match = True
                    break
            if not match:
                logger.debug(f"{element.get('name')} of '{self}' not valid.")
                return False
        return True


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

    def cfc(self, value: int | str, method="ISO-6487") -> Channel:
        """
        Apply a filter to smooth curves.
        REFERENCES:
        - Appendix C of references/SAE-J211-1-MAR95/sae.j211-1.1995.pdf
        - Annex A of references/ISO-6487/ISO-6487-2015.pdf
        :param value:
        :param method:
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
                return copy.deepcopy(self)
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
            elif cfc == "600":
                filter_class = "B"
            elif cfc == 180:
                filter_class = "C"
            elif cfc == 60:
                filter_class = "D"
            else:
                filter_class = "S"

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

            info = self.info
            info.update({"Channel frequency class": cfc})

            return Channel(
                code=self.code.set(filter_class=filter_class),
                data=data,
                unit=self.unit,
                info=info
            )

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

            return Channel(
                code=self.code.set(filter_class=filter_class),
                data=data,
                unit=self.unit,
                info=info
            )
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
        new_info["Dimension"] = new_code.physical_dimension

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
        new_info["Dimension"] = new_code.physical_dimension

        new_channel = Channel(new_code, new_data, unit=new_unit, info=new_info)
        new_channel -= new_channel.get_data(t=0)
        new_channel += x_0
        return new_channel

    def plot(self, *args, **kwargs) -> None:
        self.data.plot(*args, **kwargs).get_figure().show()

    # Operator methods
    def __eq__(self, other):
        if isinstance(other, Channel):
            if self.unit.physical_type == other.unit.physical_type:
                return self.data.equals(other.convert_unit(self.unit).data)
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __neg__(self):
        return Channel(self.code, -self.data, self.unit, self.info)

    def __add__(self, other):
        if isinstance(other, Channel):
            t = time_intersect(self, other)
            if self.unit.physical_type == other.unit.physical_type:
                return Channel(code=self.code,
                               data=pd.DataFrame(self.get_data(t) + other.get_data(t, unit=self.unit), index=t),
                               unit=self.unit,
                               info=self.info)
            else:
                logger.warning(f"Adding channels with non compatible physical units: {self.unit} and {other.unit}")
                return Channel(code=self.code,
                               data=pd.DataFrame(self.get_data(t=t) + other.get_data(t=t), index=t),
                               unit=self.unit,
                               info=self.info)
        else:
            return Channel(code=self.code,
                           data=self.data + other,
                           unit=self.unit,
                           info=self.info)

    def __sub__(self, other):
        if isinstance(other, Channel):
            t = time_intersect(self, other)
            if self.unit.physical_type == other.unit.physical_type:
                return Channel(code=self.code,
                               data=pd.DataFrame(self.get_data(t) - other.get_data(t, unit=self.unit), index=t),
                               unit=self.unit,
                               info=self.info)
            else:
                logger.warning(f"Subtracting channels with non compatible physical units: {self.unit} and {other.unit}")
                return Channel(code=self.code,
                               data=pd.DataFrame(self.get_data(t=t) - other.get_data(t=t), index=t),
                               unit=self.unit,
                               info=self.info)
        else:
            return Channel(code=self.code,
                           data=self.data - other,
                           unit=self.unit,
                           info=self.info)

    def __mul__(self, other):
        if isinstance(other, Channel):
            t = time_intersect(self, other)
            return Channel(code=self.code,
                           data=pd.DataFrame(self.get_data(t=t) * other.get_data(t=t), index=t),
                           unit=self.unit * other.unit,
                           info=self.info)
        else:
            return Channel(code=self.code,
                           data=self.data * other,
                           unit=self.unit,
                           info=self.info)

    def __truediv__(self, other):
        if isinstance(other, Channel):
            t = time_intersect(self, other)
            return Channel(code=self.code,
                           data=pd.DataFrame(self.get_data(t=t) / other.get_data(t=t), index=t),
                           unit=self.unit / other.unit,
                           info=self.info)
        else:
            return Channel(code=self.code,
                           data=self.data / other,
                           unit=self.unit,
                           info=self.info)

    def __pow__(self, power, modulo=None):
        return Channel(code=self.code,
                       data=self.data**power,
                       unit=self.unit,
                       info=self.info + [("Calculation History", f"x^{power}")])

    def __abs__(self):
        return Channel(code=self.code,
                       data=abs(self.data),
                       unit=self.unit,
                       info=self.info + [("Calculation History", "abs(x)")])


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
    elif mode == "random":
        raise NotImplementedError  # TODO
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
