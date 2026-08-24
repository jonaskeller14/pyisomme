from __future__ import annotations

import logging

from pyisomme.channel import Channel
from pyisomme.utils import debug_logging

logger = logging.getLogger("pyisomme.calculate")


@debug_logging(logger)
def calculate_resultant(
    c1: Channel, c2: Channel | float = 0, c3: Channel | float = 0
) -> Channel:
    """
    Takes 2 or 3 Channels and calculates the 2nd norm or resultant component.
    :param c1: X-Channel
    :param c2: Y-Channel
    :param c3: (optional) Z-Channel
    :return: Resultant Channel
    """
    new_channel = (c1**2 + c2**2 + c3**2) ** (1 / 2)
    new_channel.info = (
        c1.info.update(
            {
                "Data source": "calculation",
            }
        )
        .add(
            {
                f".Channel 00{idx}": channel.code
                for idx, channel in enumerate((c1, c2, c3), 1)
                if isinstance(channel, Channel)
            }
        )
        .add(
            {
                f".Filter 00{idx}": channel.code.filter_class
                for idx, channel in enumerate((c1, c2, c3), 1)
                if isinstance(channel, Channel)
            }
        )
    )
    new_channel.code = c1.code.set(direction="R")
    return new_channel
