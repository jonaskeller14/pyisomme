from __future__ import annotations

from typing import Protocol

from pyisomme.isomme import Isomme
from pyisomme.report.page2 import ChannelPlotSpec


class SideOverall(Protocol):
    p: str


class SideReport(Protocol):
    isomme_list: list[Isomme]

    def overall(self, isomme: Isomme) -> SideOverall: ...


class DriverOverall(Protocol):
    p_driver: str


class DriverReport(Protocol):
    isomme_list: list[Isomme]

    def overall(self, isomme: Isomme) -> DriverOverall: ...


_SIDE_HEAD_ACCELERATION = ChannelPlotSpec[SideReport](
    name="Head Acceleration",
    title="Head Acceleration",
    channels=lambda report: {
        isomme: [
            [f"?{report.overall(isomme).p}HEAD??????AC{axis}A"]
            for axis in "XYZR"
        ]
        for isomme in report.isomme_list
    },
    nrows=2,
    ncols=2,
    sharey=True,
)


def side_head_acceleration_spec_for(_report: SideReport) -> ChannelPlotSpec[SideReport]:
    return _SIDE_HEAD_ACCELERATION


_DRIVER_HEAD_ACCELERATION = ChannelPlotSpec[DriverReport](
    name="Driver Head Acceleration",
    title="Driver Head Acceleration",
    channels=lambda report: {
        isomme: [
            [f"?{report.overall(isomme).p_driver}HEAD??????AC{axis}A"]
            for axis in "XYZR"
        ]
        for isomme in report.isomme_list
    },
    nrows=2,
    ncols=2,
    sharey=True,
)


def driver_head_acceleration_spec_for(
    _report: DriverReport,
) -> ChannelPlotSpec[DriverReport]:
    return _DRIVER_HEAD_ACCELERATION


__all__ = ["driver_head_acceleration_spec_for", "side_head_acceleration_spec_for"]
