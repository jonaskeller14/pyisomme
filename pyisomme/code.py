from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from fnmatch import translate
from functools import cache, lru_cache
from pathlib import Path
from typing import NamedTuple

from pyisomme.errors import InvalidCodeError
from pyisomme.unit import Unit

logger = logging.getLogger(__name__)


_CHANNEL_CODES_ROOT: ET.Element = ET.parse(
    Path(__file__).parent.joinpath("channel_codes.xml")
).getroot()

CODE_LENGTH = 16

_CODE_REGEX = re.compile(r"[a-zA-Z0-9?]{16}")

CODE_COMPONENTS: tuple[tuple[str, slice], ...] = (
    ("test_object", slice(0, 1)),
    ("position", slice(1, 2)),
    ("main_location", slice(2, 6)),
    ("fine_location_1", slice(6, 8)),
    ("fine_location_2", slice(8, 10)),
    ("fine_location_3", slice(10, 12)),
    ("physical_dimension", slice(12, 14)),
    ("direction", slice(14, 15)),
    ("filter_class", slice(15, 16)),
)


class _ChannelDefinition(NamedTuple):
    """One '<Channel>' row of 'channel_codes.xml', with its code pattern pre-compiled."""

    pattern: re.Pattern[str]
    description: str | None
    default_unit: str | None


class _ElementDefinition(NamedTuple):
    """One '<Element>' group of 'channel_codes.xml', i.e. the definitions of one code component."""

    name: str
    channels: tuple[_ChannelDefinition, ...]


@cache
def _codification() -> tuple[_ElementDefinition, ...]:
    """
    'channel_codes.xml' as a lookup table, built once on first use.

    'fnmatch.translate' builds the same regex 'fnmatch.fnmatchcase' would, but here it is
    compiled ahead of time: the 878 code patterns do not fit fnmatch's 256-entry pattern
    cache, so matching them one by one recompiles most of them on every single lookup.
    Matching is case-sensitive on every platform - 'fnmatch.fnmatch' would run both sides
    through 'os.path.normcase' and thus be case-insensitive on Windows only.
    :return: one entry per code component, in code order
    """
    return tuple(
        _ElementDefinition(
            name=element.get("name", ""),
            channels=tuple(
                _ChannelDefinition(
                    pattern=re.compile(translate(channel.get("code", ""))),
                    description=channel.get("description"),
                    default_unit=channel.get("default_unit"),
                )
                for channel in element.findall(".//Channel")
            ),
        )
        for element in _CHANNEL_CODES_ROOT.findall("Codification/Element")
    )


def pattern_length(pattern: str) -> int | None:
    """
    How many characters a code must have to match 'pattern' (fnmatch pattern).
    :param pattern: an fnmatch-style channel code pattern
    :return: the code length the pattern requires, or None if unbounded
    """
    length = 0
    index = 0
    while index < len(pattern):
        if pattern[index] == "*":
            return None
        if pattern[index] == "[":
            close = pattern.find("]", index + 2)  # '[]...]' starts with a literal ]
            if close == -1:  # an unmatched '[' is a literal one to fnmatch
                index += 1
                length += 1
                continue
            index = close + 1
        else:
            index += 1
        length += 1
    return length


@lru_cache(maxsize=4096)
def _lookup(code: str) -> tuple[_ChannelDefinition | None, ...]:
    """
    Look up a code in 'channel_codes.xml'. Cached: a Code is immutable, so is its result.
    :param code: 16-character channel code
    :return: first matching definition per code component, None where the component is undefined
    """
    return tuple(
        next(
            (channel for channel in element.channels if channel.pattern.match(code)),
            None,
        )
        for element in _codification()
    )


class Code(str):
    """
    A 16-character ISO-MME channel code.

    As immutable as the str it is: the nine components are read-only views onto the string
    itself, so they can never drift out of sync with it. Use set() to derive a new code
    with individual components replaced.
    """

    __slots__ = ()

    def __new__(cls, code: str) -> Code:
        if not _CODE_REGEX.fullmatch(code):
            raise InvalidCodeError(
                f"Invalid code '{code}'. Code must be 16 characters long, containing only "
                "letters, digits and '?' wildcards."
            )
        return super().__new__(cls, code)

    def __repr__(self) -> str:
        return f"Code('{self}')"

    @property
    def test_object(self) -> str:
        return self[0]

    @property
    def position(self) -> str:
        return self[1]

    @property
    def main_location(self) -> str:
        return self[2:6]

    @property
    def fine_location_1(self) -> str:
        return self[6:8]

    @property
    def fine_location_2(self) -> str:
        return self[8:10]

    @property
    def fine_location_3(self) -> str:
        return self[10:12]

    @property
    def physical_dimension(self) -> str:
        return self[12:14]

    @property
    def direction(self) -> str:
        return self[14]

    @property
    def filter_class(self) -> str:
        return self[15]

    @property
    def components(self) -> tuple[str, ...]:
        """
        :return: the nine code components, in code order
        """
        return tuple(self[component_slice] for _, component_slice in CODE_COMPONENTS)

    def set(
        self,
        test_object: str | None = None,
        position: str | None = None,
        main_location: str | None = None,
        fine_location_1: str | None = None,
        fine_location_2: str | None = None,
        fine_location_3: str | None = None,
        physical_dimension: str | None = None,
        direction: str | None = None,
        filter_class: str | None = None,
    ) -> Code:
        """
        Derive a new code, replacing the given components and keeping all others.
        :return: new Code or InvalidCodeError is raised
        """
        new_values = (
            test_object,
            position,
            main_location,
            fine_location_1,
            fine_location_2,
            fine_location_3,
            physical_dimension,
            direction,
            filter_class,
        )

        components = []
        for new_value, current, (name, component_slice) in zip(
            new_values, self.components, CODE_COMPONENTS
        ):
            if new_value is None:
                components.append(current)
                continue
            length = component_slice.stop - component_slice.start
            if len(new_value) != length:
                raise InvalidCodeError(
                    f"Invalid {name} '{new_value}' for code '{self}'. "
                    f"{name} must be exactly {length} character(s) long."
                )
            components.append(new_value)

        return Code("".join(components))

    def get_info(self) -> dict[str, str | None]:
        """
        Data from 'channel_codes.xml'
        :return: dict with code attributes
        """
        info: dict[str, str | None] = {}
        undefined = []
        for element, channel in zip(_codification(), _lookup(self)):
            if channel is None:
                undefined.append(element.name)
            else:
                info[element.name] = channel.description
        if undefined:
            logger.warning(f"'{self}' has no definition for {', '.join(undefined)}.")
        return info

    def get_default_unit(self) -> Unit | None:
        """
        Returns SI-Unit (default-unit) of Dimension (part of the channel code).
        Default Units are stored in 'channel_codes.xml'
        :return: Unit or None
        """
        for element, channel in zip(_codification(), _lookup(self)):
            if element.name != "Physical Dimension":
                continue
            if channel is not None and channel.default_unit is not None:
                return Unit(channel.default_unit)
        return None

    def integrate(self) -> Code:
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

    def differentiate(self) -> Code:
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
        for element, channel in zip(_codification(), _lookup(self)):
            if channel is None:
                logger.debug(f"{element.name} of '{self}' not valid.")
                return False
        return True


def combine_codes(*codes: str | Code) -> Code:
    """
    Combine codes into a single pattern, replacing every character the codes disagree on.
    :return: Code with '?' wildcards where the codes differ
    """
    if len(codes) == 0:
        return Code("????????????????")

    combined_code = Code(codes[0])
    for code in codes[1:]:
        combined_code = Code(
            "".join(
                combined_char if combined_char == code_char else "?"
                for combined_char, code_char in zip(combined_code, Code(code))
            )
        )
    return combined_code
