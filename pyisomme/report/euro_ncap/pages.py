from __future__ import annotations

import logging
from typing import Any, Protocol

import numpy as np
from matplotlib.colors import to_rgb

from pyisomme.calculate.olc import calculate_olc
from pyisomme.isomme import Isomme
from pyisomme.limit_set import LimitSet
from pyisomme.report.page2 import (
    ChannelPlotSpec,
    HICSpec,
    LineTablePage,
    TableData,
)
from pyisomme.report.report import Report
from pyisomme.unit import Unit, g0

logger = logging.getLogger(__name__)


class SideOverall(Protocol):
    p: str


class SideReport(Protocol):
    isomme_list: list[Isomme]

    def overall(self, isomme: Isomme) -> SideOverall: ...


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

_SIDE_SHOULDER_LATERAL_FORCE = ChannelPlotSpec[SideReport](
    name="Shoulder Lateral Force",
    title="Shoulder Lateral Force",
    channels=lambda report: {
        isomme: [
            [f"?{report.overall(isomme).p}SHLDLE00??FOYC"],
            [f"?{report.overall(isomme).p}SHLDRI00??FOYC"],
        ]
        for isomme in report.isomme_list
    },
    nrows=1,
    ncols=2,
    sharey=True,
)

_SIDE_CHEST_LATERAL_COMPRESSION = ChannelPlotSpec[SideReport](
    name="Chest Lateral Compression",
    title="Chest Lateral Compression",
    channels=lambda report: {
        isomme: [
            [f"?{report.overall(isomme).p}TRRILE01??DSYC"],
            [f"?{report.overall(isomme).p}TRRIRI01??DSYC"],
            [f"?{report.overall(isomme).p}TRRILE02??DSYC"],
            [f"?{report.overall(isomme).p}TRRIRI02??DSYC"],
            [f"?{report.overall(isomme).p}TRRILE03??DSYC"],
            [f"?{report.overall(isomme).p}TRRIRI03??DSYC"],
        ]
        for isomme in report.isomme_list
    },
    nrows=3,
    ncols=2,
    sharey=True,
)

_SIDE_CHEST_LATERAL_VC = ChannelPlotSpec[SideReport](
    name="Chest Lateral VC",
    title="Chest Lateral VC",
    channels=lambda report: {
        isomme: [
            [f"?{report.overall(isomme).p}VCCRLE01??VEYC"],
            [f"?{report.overall(isomme).p}VCCRRI01??VEYC"],
            [f"?{report.overall(isomme).p}VCCRLE02??VEYC"],
            [f"?{report.overall(isomme).p}VCCRRI02??VEYC"],
            [f"?{report.overall(isomme).p}VCCRLE03??VEYC"],
            [f"?{report.overall(isomme).p}VCCRRI03??VEYC"],
        ]
        for isomme in report.isomme_list
    },
    nrows=3,
    ncols=2,
    sharey=True,
)

_SIDE_ABDOMEN_LATERAL_COMPRESSION = ChannelPlotSpec[SideReport](
    name="Abdomen Lateral Compression",
    title="Abdomen Lateral Compression",
    channels=lambda report: {
        isomme: [
            [f"?{report.overall(isomme).p}ABRILE01??DSYC"],
            [f"?{report.overall(isomme).p}ABRIRI01??DSYC"],
            [f"?{report.overall(isomme).p}ABRILE02??DSYC"],
            [f"?{report.overall(isomme).p}ABRIRI02??DSYC"],
        ]
        for isomme in report.isomme_list
    },
    nrows=2,
    ncols=2,
    sharey=True,
)

_SIDE_ABDOMEN_LATERAL_VC = ChannelPlotSpec[SideReport](
    name="Abdomen Lateral VC",
    title="Abdomen Lateral VC",
    channels=lambda report: {
        isomme: [
            [f"?{report.overall(isomme).p}VCARLE01??VEYC"],
            [f"?{report.overall(isomme).p}VCARRI01??VEYC"],
            [f"?{report.overall(isomme).p}VCARLE02??VEYC"],
            [f"?{report.overall(isomme).p}VCARRI02??VEYC"],
        ]
        for isomme in report.isomme_list
    },
    nrows=2,
    ncols=2,
    sharey=True,
)

_SIDE_PUBIC_SYMPHYSIS_FORCE = ChannelPlotSpec[SideReport](
    name="Pubic Symphysis Force",
    title="Pubic Symphysis Force",
    channels=lambda report: {
        isomme: [[f"?{report.overall(isomme).p}PUBC0000??FOYB"]]
        for isomme in report.isomme_list
    },
)


def side_head_acceleration_spec_for(_report: SideReport) -> ChannelPlotSpec[SideReport]:
    return _SIDE_HEAD_ACCELERATION


def side_shoulder_lateral_force_spec_for(
    _report: SideReport,
) -> ChannelPlotSpec[SideReport]:
    return _SIDE_SHOULDER_LATERAL_FORCE


def side_chest_lateral_compression_spec_for(
    _report: SideReport,
) -> ChannelPlotSpec[SideReport]:
    return _SIDE_CHEST_LATERAL_COMPRESSION


def side_chest_lateral_vc_spec_for(_report: SideReport) -> ChannelPlotSpec[SideReport]:
    return _SIDE_CHEST_LATERAL_VC


def side_abdomen_lateral_compression_spec_for(
    _report: SideReport,
) -> ChannelPlotSpec[SideReport]:
    return _SIDE_ABDOMEN_LATERAL_COMPRESSION


def side_abdomen_lateral_vc_spec_for(
    _report: SideReport,
) -> ChannelPlotSpec[SideReport]:
    return _SIDE_ABDOMEN_LATERAL_VC


def side_pubic_symphysis_force_spec_for(
    _report: SideReport,
) -> ChannelPlotSpec[SideReport]:
    return _SIDE_PUBIC_SYMPHYSIS_FORCE


class DriverOverall(Protocol):
    p_driver: str


class DriverReport(Protocol):
    isomme_list: list[Isomme]

    def overall(self, isomme: Isomme) -> DriverOverall: ...


_DRIVER_BELT = ChannelPlotSpec[DriverReport](
    name="Driver Belt",
    title="Driver Belt",
    channels=lambda report: {
        isomme: [
            [f"?{report.overall(isomme).p_driver}SEBE000[30]B1FO[X0]C"],
            [f"?{report.overall(isomme).p_driver}SEBE000[30]B2FO[X0]C"],
            [f"?{report.overall(isomme).p_driver}SEBE000[30]B3FO[X0]C"],
            [f"?{report.overall(isomme).p_driver}SEBE000[30]B4FO[X0]C"],
            [f"?{report.overall(isomme).p_driver}SEBE000[30]B5FO[X0]C"],
            [f"?{report.overall(isomme).p_driver}SEBE000[30]B6FO[X0]C"],
        ]
        for isomme in report.isomme_list
    },
    nrows=3,
    ncols=2,
)

_DRIVER_HEAD_ACCELERATION = ChannelPlotSpec[DriverReport](
    name="Driver Head Acceleration",
    title="Driver Head Acceleration",
    channels=lambda report: {
        isomme: [
            [f"?{report.overall(isomme).p_driver}HEAD??????ACXA"],
            [f"?{report.overall(isomme).p_driver}HEAD??????ACYA"],
            [f"?{report.overall(isomme).p_driver}HEAD??????ACZA"],
            [f"?{report.overall(isomme).p_driver}HEAD??????ACRA"],
        ]
        for isomme in report.isomme_list
    },
    nrows=2,
    ncols=2,
    sharey=True,
)

_DRIVER_HIC_15 = HICSpec[DriverReport](
    name="Driver HIC15",
    title="Driver HIC15",
    position=lambda report, isomme: report.overall(isomme).p_driver,
    timespan=15,
)

_DRIVER_NECK_LOAD = ChannelPlotSpec[DriverReport](
    name="Driver Neck Load",
    title="Driver Neck Load",
    channels=lambda report: {
        isomme: [
            [f"?{report.overall(isomme).p_driver}NECKUP00??MOYB"],
            [f"?{report.overall(isomme).p_driver}NECKUP00??FOZA"],
            [f"?{report.overall(isomme).p_driver}NECKUP00??FOXA"],
        ]
        for isomme in report.isomme_list
    },
    nrows=2,
    ncols=2,
)

_DRIVER_FEMUR_AXIAL_FORCE = ChannelPlotSpec[DriverReport](
    name="Driver Femur Axial Force",
    title="Driver Femur Axial Force",
    channels=lambda report: {
        isomme: [
            [f"?{report.overall(isomme).p_driver}FEMRLE00??FOZB"],
            [f"?{report.overall(isomme).p_driver}FEMRRI00??FOZB"],
        ]
        for isomme in report.isomme_list
    },
    nrows=1,
    ncols=2,
    sharey=True,
)


def driver_belt_spec_for(_report: DriverReport) -> ChannelPlotSpec[DriverReport]:
    return _DRIVER_BELT


def driver_head_acceleration_spec_for(
    _report: DriverReport,
) -> ChannelPlotSpec[DriverReport]:
    return _DRIVER_HEAD_ACCELERATION


def driver_hic_15_spec_for(_report: DriverReport) -> HICSpec[DriverReport]:
    return _DRIVER_HIC_15


def driver_neck_load_spec_for(
    _report: DriverReport,
) -> ChannelPlotSpec[DriverReport]:
    return _DRIVER_NECK_LOAD


def driver_femur_axial_force_spec_for(
    _report: DriverReport,
) -> ChannelPlotSpec[DriverReport]:
    return _DRIVER_FEMUR_AXIAL_FORCE


class OLCTrolleyPage(LineTablePage[Report[Any]]):
    """Trolley velocity and its OLC construction with the resulting OLC value."""

    def __init__(self, report: Report[Any]) -> None:
        super().__init__(
            report,
            name="OLC Trolley",
            title="Occupant Load Criterion (OLC) of Trolley",
            channels=self._channels,
            table=self._table,
            nrows=1,
            ncols=2,
            # The report-level OLC limits are accelerations (g0), so they do not
            # apply to this velocity plot.
            limits=LimitSet(),
        )

    @staticmethod
    def _trolley_channel(isomme: Isomme) -> Any:
        return isomme.get_channel("M?MBAR0000??VEXA", "M?MBARCG00??VEXA")

    @classmethod
    def _channels(cls, report: Report[Any]) -> dict[Isomme, list[list[Any]]]:
        channels: dict[Isomme, list[list[Any]]] = {}
        for isomme in report.isomme_list:
            channel = cls._trolley_channel(isomme)
            if channel is None:
                logger.info(
                    "No trolley velocity channel in %s. OLC trolley plot left empty.",
                    isomme,
                )
                channels[isomme] = [[]]
                continue
            _, olc_visual = calculate_olc(channel)
            channels[isomme] = [[channel, olc_visual]]
        return channels

    @classmethod
    def _table(cls, report: Report[Any]) -> TableData:
        cell_texts = []
        cell_colors = []
        for isomme in report.isomme_list:
            channel = cls._trolley_channel(isomme)
            if channel is None:
                cell_texts.append(f"{np.nan:.2f}")
                cell_colors.append((0.0, 0.0, 0.0, 0.0))
                continue
            olc, _ = calculate_olc(channel)
            result = (
                report.overall(isomme)
                .criterion_compatibility_modifier.criterion_olc_modifier.result
            )
            cell_texts.append(f"{olc.get_data(unit=Unit(g0))[0]:.2f}")
            if result is None or result.color is None:
                cell_colors.append((0.0, 0.0, 0.0, 0.0))
            else:
                color = result.color
                rgb = to_rgb(color) if isinstance(color, str) else color[:3]
                cell_colors.append((*rgb, 0.5))
        return TableData(
            cell_texts=[cell_texts],
            cell_colors=[cell_colors],
            row_labels=[[isomme.test_number for isomme in report.isomme_list]],
            col_labels=[["OLC [g]"]],
        )


__all__ = [
    "OLCTrolleyPage",
    "driver_belt_spec_for",
    "driver_femur_axial_force_spec_for",
    "driver_head_acceleration_spec_for",
    "driver_hic_15_spec_for",
    "driver_neck_load_spec_for",
    "side_abdomen_lateral_compression_spec_for",
    "side_abdomen_lateral_vc_spec_for",
    "side_chest_lateral_compression_spec_for",
    "side_chest_lateral_vc_spec_for",
    "side_head_acceleration_spec_for",
    "side_pubic_symphysis_force_spec_for",
    "side_shoulder_lateral_force_spec_for",
]
