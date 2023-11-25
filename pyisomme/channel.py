import math
import pandas as pd
import numpy as np
import logging
import fnmatch
from astropy import units as u
from pathlib import Path
import xml.etree.ElementTree as ET
from scipy.interpolate import interp1d
from scipy.integrate import quad
from scipy.misc import derivative
import copy


class Channel:
    def __init__(self, code, data, unit=None, info=None):
        self.code = code
        self.data = data
        self.unit = str_to_unit(unit)
        self.info = info if info is not None else {}

    def __str__(self):
        return self.code

    def set_code(self, new_code):
        if is_possible_channel_code(new_code):
            logging.info(f"Renaming {self.code} to {new_code} (valid)")
        else:
            logging.warning(f"Renaming {self.code} to {new_code} (not valid!)")
        self.code = new_code
        return self

    def set_unit(self, new_unit):
        self.unit = new_unit

    def convert_unit(self, new_unit):
        pass

    def get_sampling_interval(self):
        return self.info["Sampling interval"]
        # TODO: Berechne erst! , falls interpoliert wurde und info nicht vorhanden ist

    def cfc(self, cfc, method="SAE-J211-1"):
        """
        #TODO
        #TODO: method iso6487
        REFERENCES:
        - Appendix C of "\references\SAE-J211-1-MAR95\sae.j211-1.1995.pdf"
        :param cfc:
        :param method:
        :return:
        """
        # filterclass to cfc
        if cfc == "A":
            cfc = 1000
        elif cfc == "B":
            cfc = 600
        elif cfc == "C":
            cfc = 180
        elif cfc == "D":
            cfc = 60
        elif cfc == "0":
            return self

        # Method
        if method != "SAE-J211-1":
            logging.error(f"'method={method}' not supported (yet). No filter applied")
            return self

        # SAE-J211-1
        input_values = self.data.to_numpy()
        sample_interval = self.get_sampling_interval()
        wd = 2 * math.pi * cfc / 0.6 * 1.25
        wa = math.tan(wd * sample_interval / 2.0)
        a0 = wa**2 / (1 + wa**2 + math.sqrt(2) * wa)
        a1 = 2 * a0
        a2 = a0
        b1 = -2 * (wa**2 - 1) / (1 + wa**2 + math.sqrt(2) * wa)
        b2 = (-1 + math.sqrt(2)*wa - wa**2) / (1 + wa**2 + math.sqrt(2) * wa)

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
        self.data.iloc[:, 0] = output_values
        return self


    def get_data(self, t=None, unit=None):
        """
        Returns Value at time t. If t is out of recorded range, 'default_return' will be returned
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
            if isinstance(old_unit, u.Unit):
                if not isinstance(unit, u.Unit):
                    unit = str_to_unit(unit)
                if unit is not None:
                    value_array = (value_array * old_unit).to(unit).to_value()
            else:
                logging.error("Could not determine old unit. No conversion will be performed.")

        if t is None:
            return value_array

        # Interpolation
        interpolator = interp1d(time_array, value_array, bounds_error=False, fill_value=(0,0))
        try:
            return float(interpolator(t))  # if t is float or int
        except TypeError:
            return interpolator(t)  # if t is list object

    def get_info(self, *labels):
        """
        Get channel info by giving one or multiple label(s) to identify information.
        Regex or fnmatch patterns possible.
        :param labels: key to find information in dict
        :return: first match or None
        """
        for label in labels:
            for key in self.info:
                if re.match(label, key) or fnmatch(key, label):
                    return self.info[key]
        return None

    def differentiate(self):
        """
        # TODO
        :return:
        """
        new_data = copy.deepcopy(self.data)
        new_data.iloc[:, 0] = np.zeros(len(new_data))
        new_data.iloc[:, 0] = [derivative(self.get_data, t, dx=1e-3) for t in self.data.index]
        new_data.iloc[0, 0] = new_data.iloc[1, 0]
        new_data.iloc[-1, 0] = new_data.iloc[-2, 0]
        return Channel("????????????????", new_data, unit=None, info=None)

    def integrate(self):
        """
        # TODO
        :return:
        """
        t1 = self.data.index[0]
        new_data = copy.deepcopy(self.data)
        new_data.iloc[:, 0] = np.zeros(len(new_data))
        new_data.iloc[:, 0] = [quad(self.get_data, t1, t2)[0] for t2 in self.data.index]
        return Channel("????????????????", new_data, unit=None, info=None)

    # Operator methods
    # TOOD: soll ich das nicht weglassen?
    def __eq__(self, other):
        #TODO: data ist jetzt df
        EPSILON = 0.001
        if not isinstance(other.data, self.data.__class__):
            return False
        return np.dot(self.data, other.data) * np.dot(self.data, other.data) > (1-EPSILON) * np.dot(self.data, self.data) * np.dot(other.data, other.data)

    def __ne__(self, other):
        return not __eq__(self, other)


    def __add__(self, other):
        if isinstance(other, Channel):
            assert self.unit == other.unit
            time_array = np.unique(self.data.index.to_list() + other.data.index.to_list())
            new_data = self.get_data(time_array) + other.get_data(time_array)
            new_data = pd.DataFrame({"Time": time_array, "??": new_data}).set_index("Time")
            return Channel("????????????????", new_data, self.unit)
        else:
            new_data = self.data + other
            return Channel(self.code, new_data, self.unit, self.info)

    def __sub__(self, other):
        if isinstance(other, Channel):
            assert self.unit == other.unit
            time_array = np.unique(self.data.index.to_list() + other.data.index.to_list())
            new_data = self.get_data(time_array) - other.get_data(time_array)
            new_data = pd.DataFrame({"Time": time_array, "??": new_data}).set_index("Time")
            return Channel("????????????????", new_data, self.unit)
        else:
            new_data = self.data - other
            return Channel(self.code, new_data, self.unit, self.info)

    def __mul__(self, other):
        if isinstance(other, Channel):
            assert self.unit == other.unit
            time_array = np.unique(self.data.index.to_list() + other.data.index.to_list())
            new_data = self.get_data(time_array) * other.get_data(time_array)
            new_data = pd.DataFrame({"Time": time_array, "??": new_data}).set_index("Time")
            return Channel("????????????????", new_data, self.unit)
        else:
            new_data = self.data * other
            return Channel(self.code, new_data, self.unit, self.info)

    def __truediv__(self, other):
        if isinstance(other, Channel):
            assert self.unit == other.unit
            time_array = np.unique(self.data.index.to_list() + other.data.index.to_list())
            new_data = self.get_data(time_array) / other.get_data(time_array)
            new_data = pd.DataFrame({"Time": time_array, "??": new_data}).set_index("Time")
            return Channel("????????????????", new_data, self.unit)
        else:
            new_data = self.data / other
            return Channel(self.code, new_data, self.unit, self.info)

    def __pow__(self, power, modulo=None):
        new_data = self.data**power
        return Channel(self.code, new_data, self.unit, self.info)


def is_possible_channel_code(code:str) -> bool:
    """
    Data from 'channel_codes.xml'
    :param code: ISO-MME channel code (16 character)
    :return: True if code contains valid parts and is as a whole valid
    """
    if len(get_code_info(code)) < 9:
        return False
    root = ET.parse(Path(__file__).parent.joinpath("channel_codes.xml")).getroot()  # TODO: nur einmal auslesen
    for channel in root.findall("Possible_Channels//Channel"):
        if fnmatch.fnmatch(code, channel.get("code")):
            return True
    return False


def get_code_info(code:str) -> dict:
    """
    Data from 'channel_codes.xml'
    :param code: ISO-MME channel code (16 character)
    :return: dict with code attributes
    """
    info = {}
    root = ET.parse(Path(__file__).parent.joinpath("channel_codes.xml")).getroot()  # TODO: nur einmal auslesen
    for element in root.findall("Codification/Element"):
        for channel in element.findall(".//Channel"):
            if fnmatch.fnmatch(code, channel.get("code")):
                info[element.get("name")] = channel.get("description")
                break
        if element.get("name") not in info:
            logging.warning(f"{code}: '{element.get('name')}' not part of available ones.")
    return info


def hic(max_delta_t, channel) -> float:
    """
    Computes head injury criterion (HIC)
    HIC15 --> max_delta_t = 15
    HIC36 --> max_delta_t = 36

    REFERENCES
    - https://en.wikipedia.org/wiki/Head_injury_criterion

    :param max_delta_t: in ms
    :param channel:
    :return:
    """
    max_delta_t *= 1e-3
    time_array = channel.get_time()
    res = 0
    for t1 in time_array:
        for t2 in time_array[(t1 < time_array)*(time_array <= t1 + max_delta_t)]:
            new_res, _ = quad(channel.f, t1, t2)
            new_res = (t2 - t1) * (1 / (t2 - t1) * new_res)**2.5
            if new_res > res:
                res = new_res
    return res


def str_to_unit(unit_str:str=None):
    """
    #TODO
    :param input_str:
    :return:
    """
    u.set_enabled_aliases({"Nm": u.Unit("N*m")})

    if unit_str is None:
        return None
    try:
        return u.Unit(unit_str)
    except ValueError:
        logging.error(f"Could not parse unit '{unit_str}'.")
        return None


def create_sample(code="SAMPLE??????????", t_range:tuple=(0,0.01,1000), y_range:tuple=(0,10), mode:str="sin", unit=None):
    time_array = np.linspace(*t_range)
    n = len(time_array)

    # y-data
    if mode == "linear":
        value_array = np.linspace(y_range[0], y_range[1], n)
    elif mode == "sin":
        x = np.linspace(0, 2*np.pi, n)
        value_array = abs(y_range[1] - y_range[0])/2 * np.sin(x) + sum(y_range)/2
    else:
        raise ValueError(f"mode={mode} does not exist: Available modes: 'linear', 'sin'")


    # TODO: mode = random, sin, const, linear

    data = pd.DataFrame({"Time": time_array, "SAMPLE": value_array}).set_index("Time")
    return Channel(code, data, unit)


def channel_norm(c1, c2, c3=0):
    """
    Takes 2 or 3 Channels and calculates the norm or resultant component.
    :param c1: X-Channel
    :param c2: Y-Channel
    :param c3: (optional) Z-Channel
    :return: Resultant Channel
    """
    new_channel = (c1**2 + c2**2 + c3**2)**(1/2)
    new_channel.info = c1.info
    new_channel.code = c1.code[:14] + "R" + c1.code[15]
    return new_channel



