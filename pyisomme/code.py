from __future__ import annotations

from pyisomme.unit import Unit

import re
from fnmatch import fnmatch
import logging
from pathlib import Path
import xml.etree.ElementTree as ET


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


def combine_codes(*codes: str | Code) -> Code:
    if len (codes) == 0:
        return Code("????????????????")

    comnbined_code = Code(codes[0])
    for code in codes[1:]:
        code = Code(code)
        for idx, (code_char, comnbined_code_char) in enumerate(zip(code, comnbined_code)):
            if code_char != comnbined_code_char:
                comnbined_code = Code(f"{comnbined_code[:idx]}?{comnbined_code[idx+1:]}")
    return comnbined_code
