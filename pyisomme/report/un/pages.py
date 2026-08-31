from __future__ import annotations

from typing import Protocol

from pyisomme.isomme import Isomme
from pyisomme.report.page2 import ChannelPlotSpec


class SideOverall(Protocol):
    p: str


class SideReport(Protocol):
    isomme_list: list[Isomme]

    def overall(self, isomme: Isomme) -> SideOverall: ...


SIDE_POLE_CHEST_COMPRESSION = ChannelPlotSpec[SideReport](
    name="Chest Absolute Compression",
    title="Chest Absolute Compression",
    channels=lambda report: {
        isomme: [
            [f"?{report.overall(isomme).p}TRRILE01??DSRB"],
            [f"?{report.overall(isomme).p}TRRIRI01??DSRB"],
            [f"?{report.overall(isomme).p}TRRILE02??DSRB"],
            [f"?{report.overall(isomme).p}TRRIRI02??DSRB"],
            [f"?{report.overall(isomme).p}TRRILE03??DSRB"],
            [f"?{report.overall(isomme).p}TRRIRI04??DSRB"],
        ]
        for isomme in report.isomme_list
    },
    nrows=3,
    ncols=2,
    sharey=True,
)

SIDE_POLE_ABDOMEN_COMPRESSION = ChannelPlotSpec[SideReport](
    name="Abdomen Resultant Compression",
    title="Abdomen Resultant Compression",
    channels=lambda report: {
        isomme: [
            [f"?{report.overall(isomme).p}ABRILE01??DSRB"],
            [f"?{report.overall(isomme).p}ABRIRI01??DSRB"],
            [f"?{report.overall(isomme).p}ABRILE02??DSRB"],
            [f"?{report.overall(isomme).p}ABRIRI03??DSRB"],
        ]
        for isomme in report.isomme_list
    },
    nrows=2,
    ncols=2,
    sharey=True,
)

SIDE_POLE_SPINE_T12_ACCELERATION = ChannelPlotSpec[SideReport](
    name="Spine T12 Acceleration",
    title="Spine T12 Acceleration",
    channels=lambda report: {
        isomme: [
            [f"?{report.overall(isomme).p}THSP1200??AC{axis}C"]
            for axis in "XYZR"
        ]
        for isomme in report.isomme_list
    },
    nrows=2,
    ncols=2,
    sharey=True,
)

SIDE_BARRIER_CHEST_DEFLECTION = ChannelPlotSpec[SideReport](
    name="Chest Lateral Deflection",
    title="Chest Lateral Deflection",
    channels=lambda report: {
        isomme: [
            [f"?{report.overall(isomme).p}RIBSLEUP??DSYC"],
            [f"?{report.overall(isomme).p}RIBSRIUP??DSYC"],
            [f"?{report.overall(isomme).p}RIBSLEMI??DSYC"],
            [f"?{report.overall(isomme).p}RIBSRIMI??DSYC"],
            [f"?{report.overall(isomme).p}RIBSLELO??DSYC"],
            [f"?{report.overall(isomme).p}RIBSRILO??DSYC"],
        ]
        for isomme in report.isomme_list
    },
    nrows=3,
    ncols=2,
    sharey=True,
)

SIDE_BARRIER_CHEST_VC = ChannelPlotSpec[SideReport](
    name="Chest Lateral VC",
    title="Chest Lateral VC",
    channels=lambda report: {
        isomme: [
            [f"?{report.overall(isomme).p}VCCRLEUP??VEYC"],
            [f"?{report.overall(isomme).p}VCCRRIUP??VEYC"],
            [f"?{report.overall(isomme).p}VCCRLEMI??VEYC"],
            [f"?{report.overall(isomme).p}VCCRRIMI??VEYC"],
            [f"?{report.overall(isomme).p}VCCRLELO??VEYC"],
            [f"?{report.overall(isomme).p}VCCRRILO??VEYC"],
        ]
        for isomme in report.isomme_list
    },
    nrows=3,
    ncols=2,
    sharey=True,
)

SIDE_BARRIER_ABDOMEN_FORCE = ChannelPlotSpec[SideReport](
    name="Abdomen Force",
    title="Abdomen Force",
    channels=lambda report: {
        isomme: [
            [f"?{report.overall(isomme).p}ABDOLEFR??FOYB"],
            [f"?{report.overall(isomme).p}ABDORIFR??FOYB"],
            [f"?{report.overall(isomme).p}ABDOLEMI??FOYB"],
            [f"?{report.overall(isomme).p}ABDORIMI??FOYB"],
            [f"?{report.overall(isomme).p}ABDOLERE??FOYB"],
            [f"?{report.overall(isomme).p}ABDORIRE??FOYB"],
        ]
        for isomme in report.isomme_list
    },
    nrows=3,
    ncols=2,
    sharey=True,
)


def side_pole_chest_compression_spec_for(
    _report: SideReport,
) -> ChannelPlotSpec[SideReport]:
    return SIDE_POLE_CHEST_COMPRESSION


def side_pole_abdomen_compression_spec_for(
    _report: SideReport,
) -> ChannelPlotSpec[SideReport]:
    return SIDE_POLE_ABDOMEN_COMPRESSION


def side_pole_spine_t12_acceleration_spec_for(
    _report: SideReport,
) -> ChannelPlotSpec[SideReport]:
    return SIDE_POLE_SPINE_T12_ACCELERATION


def side_barrier_chest_deflection_spec_for(
    _report: SideReport,
) -> ChannelPlotSpec[SideReport]:
    return SIDE_BARRIER_CHEST_DEFLECTION


def side_barrier_chest_vc_spec_for(
    _report: SideReport,
) -> ChannelPlotSpec[SideReport]:
    return SIDE_BARRIER_CHEST_VC


def side_barrier_abdomen_force_spec_for(
    _report: SideReport,
) -> ChannelPlotSpec[SideReport]:
    return SIDE_BARRIER_ABDOMEN_FORCE


__all__ = [
    "side_barrier_abdomen_force_spec_for",
    "side_barrier_chest_deflection_spec_for",
    "side_barrier_chest_vc_spec_for",
    "side_pole_abdomen_compression_spec_for",
    "side_pole_chest_compression_spec_for",
    "side_pole_spine_t12_acceleration_spec_for",
]
