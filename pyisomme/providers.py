from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Literal
from collections.abc import Sequence
import fnmatch
import numpy as np
import pandas as pd

from pyisomme.channel import Channel, time_intersect
from pyisomme.code import Code
from pyisomme.calculate import (
    calculate_adjusted_lower_tibia_moment_My,
    calculate_adjusted_upper_tibia_moment_My,
    calculate_resultant,
    calculate_bric,
    calculate_hic,
    calculate_xms,
    calculate_damage,
    calculate_neck_MOCx,
    calculate_neck_MOCy,
    calculate_neck_Mx_base,
    calculate_neck_My_base,
    calculate_neck_nij,
    calculate_vc,
    calculate_femur_impulse,
    calculate_tibia_index,
    calculate_tibia_index_using_total_moment,
    calculate_chest_pc_score,
    calculate_olc,
)

if TYPE_CHECKING:
    from pyisomme.isomme import Isomme


class ChannelProvider:
    """Knows how to synthesize one derived channel from others."""

    def matches(self, code: Code) -> bool:
        """Whether this provider can (attempt to) build the requested ``code``."""
        raise NotImplementedError

    def build(self, isomme: Isomme, code: Code) -> Channel | None:
        """Synthesize the channel, or return ``None`` if a required input is absent."""
        raise NotImplementedError


class _FnProvider(ChannelProvider):
    """A provider whose ``matches``/``build`` are supplied as plain functions.

    Lets each bespoke synthesis block stay a small, readable function rather than a class,
    while still living behind the uniform :class:`ChannelProvider` interface.
    """

    def __init__(self,
                 match: Callable[[Code], bool],
                 build: Callable[[Isomme, Code], Channel | None]):
        self._match = match
        self._build = build

    def matches(self, code: Code) -> bool:
        return self._match(code)

    def build(self, isomme: Isomme, code: Code) -> Channel | None:
        return self._build(isomme, code)


class AggregatePairProvider(ChannelProvider):
    """Element-wise min / max / max-abs over a set of sibling channels.

    The ~10 copy-pasted "minimum/maximum of left and right" (or upper/middle/lower,
    front/middle/rear, ...) blocks differ only in: which code component varies, the member
    values, the aggregation, and whether the source ``info`` is carried over. They all
    resample the members onto a common time base (:func:`time_intersect`) and select
    element-wise. This one provider expresses all of them as configuration.
    """

    def __init__(self,
                 match: Callable[[Code], bool],
                 vary: str,
                 members: Sequence[str],
                 agg: Literal["min", "max", "max_abs"],
                 keep_info: bool = False):
        self._match = match
        self.vary = vary
        self.members = tuple(members)
        self.agg = agg
        self.keep_info = keep_info

    def matches(self, code: Code) -> bool:
        return self._match(code)

    def build(self, isomme: Isomme, code: Code) -> Channel | None:
        channels = [isomme.get_channel(code.set(**{self.vary: member})) for member in self.members]
        if any(channel is None for channel in channels):
            return None
        first = channels[0]
        t = time_intersect(*channels)
        data = [first.get_data(t=t)] + [channel.get_data(t=t, unit=first.unit) for channel in channels[1:]]
        if self.agg == "min":
            values = np.min(data, axis=0)
        elif self.agg == "max":
            values = np.max(data, axis=0)
        elif self.agg == "max_abs":
            values = np.array(data)
            values = values[np.argmax(np.abs(values), axis=0), np.arange(values.shape[1])]
        else:
            raise ValueError(f"Unknown aggregation '{self.agg}'")
        kwargs = {"info": first.info} if self.keep_info else {}
        return Channel(code=first.code.set(**{self.vary: "00"}),
                       data=pd.DataFrame(values, index=t),
                       unit=first.unit,
                       **kwargs)


# --------------------------------------------------------------------------------------- #
# Bespoke synthesis blocks (transcribed verbatim from the old get_channel if-cascade).
# Each returns None on missing inputs so get_channel falls through to the next provider.
# --------------------------------------------------------------------------------------- #

def _build_resultant(isomme: Isomme, code: Code) -> Channel | None:
    channel_xyz = [isomme.get_channel(code.set(direction=direction)) for direction in "XYZ"]
    if all(channel is not None for channel in channel_xyz):
        return calculate_resultant(*channel_xyz)
    channel_123 = [isomme.get_channel(code.set(direction=direction)) for direction in "123"]
    if all(channel is not None for channel in channel_123):
        return calculate_resultant(*channel_123)
    return None


def _build_bric(isomme: Isomme, code: Code) -> Channel | None:
    channel_head_av_xyz = [isomme.get_channel(code.set(main_location="HEAD", physical_dimension="AV", direction=direction, filter_class="D")) for direction in "XYZ"]
    if all(channel is not None for channel in channel_head_av_xyz):
        return calculate_bric(*channel_head_av_xyz)
    return None


def _build_hic(isomme: Isomme, code: Code) -> Channel | None:
    head_channel = isomme.get_channel(code.set(main_location="HEAD",
                                               fine_location_1="??",
                                               fine_location_2="00",
                                               physical_dimension="AC",
                                               filter_class="A"))
    if head_channel is not None:
        return calculate_hic(head_channel, max_delta_t=int(code.fine_location_2))
    return None


def _build_xms(isomme: Isomme, code: Code) -> Channel | None:
    channel = isomme.get_channel(code.set(fine_location_2="00",
                                          filter_class="A" if not code.main_location == "THSP" else "C"))
    if channel is not None:
        return calculate_xms(channel, min_delta_t=int(code.fine_location_2[0]), method=code.fine_location_2[1])
    return None


def _build_damage(isomme: Isomme, code: Code) -> Channel | None:
    if code.filter_class == "X":
        channel_xyz = [isomme.get_channel(code.set(fine_location_1="00", fine_location_2="00", direction=direction, filter_class="A"),
                                          code.set(fine_location_1="CG", fine_location_2="00", direction=direction, filter_class="A")) for direction in "XYZ"]
        if all(channel is not None for channel in channel_xyz):
            if code.direction == "X":
                return calculate_damage(*channel_xyz)[4]
            if code.direction == "Y":
                return calculate_damage(*channel_xyz)[5]
            if code.direction == "Z":
                return calculate_damage(*channel_xyz)[6]
            if code.direction == "R":
                return calculate_damage(*channel_xyz)[7]
    else:
        channel_xyz = [isomme.get_channel(code.set(fine_location_1="00", fine_location_2="00", direction=direction),
                                          code.set(fine_location_1="CG", fine_location_2="00", direction=direction)) for direction in "XYZ"]
        if all(channel is not None for channel in channel_xyz):
            if code.direction == "X":
                return calculate_damage(*channel_xyz)[0]
            if code.direction == "Y":
                return calculate_damage(*channel_xyz)[1]
            if code.direction == "Z":
                return calculate_damage(*channel_xyz)[2]
            if code.direction == "R":
                return calculate_damage(*channel_xyz)[3]
    return None


def _build_neck_total_moment(isomme: Isomme, code: Code) -> Channel | None:
    if code.fine_location_1 == "UP":
        if code.direction == "X":
            if code.filter_class == "X":
                channel_mx = isomme.get_channel(code.set(main_location="NECK", physical_dimension="MO", direction="X", filter_class="B"))
                channel_fy = isomme.get_channel(code.set(main_location="NECK", physical_dimension="FO", direction="Y", filter_class="B"))
                if channel_mx is not None and channel_fy is not None:
                    return calculate_neck_MOCx(channel_mx, channel_fy)[1]
            else:
                channel_mx = isomme.get_channel(code.set(main_location="NECK", physical_dimension="MO", direction="X"))
                channel_fy = isomme.get_channel(code.set(main_location="NECK", physical_dimension="FO", direction="Y"))
                if channel_mx is not None and channel_fy is not None:
                    return calculate_neck_MOCx(channel_mx, channel_fy)[0]
        elif code.direction == "Y":
            if code.filter_class == "X":
                channel_my = isomme.get_channel(code.set(main_location="NECK", physical_dimension="MO", direction="Y", filter_class="B"))
                channel_fx = isomme.get_channel(code.set(main_location="NECK", physical_dimension="FO", direction="X", filter_class="B"))
                if channel_my is not None and channel_fx is not None:
                    return calculate_neck_MOCy(channel_my, channel_fx)[1]
            else:
                channel_my = isomme.get_channel(code.set(main_location="NECK", physical_dimension="MO", direction="Y"))
                channel_fx = isomme.get_channel(code.set(main_location="NECK", physical_dimension="FO", direction="X"))
                if channel_my is not None and channel_fx is not None:
                    return calculate_neck_MOCy(channel_my, channel_fx)[0]
    elif code.fine_location_1 == "LO":
        if code.direction == "X":
            if code.filter_class == "X":
                channel_mx = isomme.get_channel(code.set(main_location="NECK", physical_dimension="MO", direction="X", filter_class="B"))
                channel_fy = isomme.get_channel(code.set(main_location="NECK", physical_dimension="FO", direction="Y", filter_class="B"))
                if channel_mx is not None and channel_fy is not None:
                    return calculate_neck_Mx_base(channel_mx, channel_fy)[1]
            else:
                channel_mx = isomme.get_channel(code.set(main_location="NECK", physical_dimension="MO", direction="X"))
                channel_fy = isomme.get_channel(code.set(main_location="NECK", physical_dimension="FO", direction="Y"))
                if channel_mx is not None and channel_fy is not None:
                    return calculate_neck_Mx_base(channel_mx, channel_fy)[0]
        elif code.direction == "Y":
            if code.filter_class == "X":
                channel_my = isomme.get_channel(code.set(main_location="NECK", physical_dimension="MO", direction="Y", filter_class="B"))
                channel_fx = isomme.get_channel(code.set(main_location="NECK", physical_dimension="FO", direction="X", filter_class="B"))
                if channel_my is not None and channel_fx is not None:
                    return calculate_neck_My_base(channel_my, channel_fx)[1]
            else:
                channel_my = isomme.get_channel(code.set(main_location="NECK", physical_dimension="MO", direction="Y"))
                channel_fx = isomme.get_channel(code.set(main_location="NECK", physical_dimension="FO", direction="X"))
                if channel_my is not None and channel_fx is not None:
                    return calculate_neck_My_base(channel_my, channel_fx)[0]
    return None


def _build_nij(isomme: Isomme, code: Code) -> Channel | None:
    if code.filter_class == "X":
        c_fz = isomme.get_channel(code.set(main_location="NECK", fine_location_1="UP", fine_location_2="00", physical_dimension="FO", direction="Z", filter_class="B"))
        c_mocy = isomme.get_channel(code.set(main_location="NECK", fine_location_1="UP", fine_location_2="00", physical_dimension="MO", direction="Y", filter_class="B"))
        if c_fz is not None and c_mocy is not None:
            if code.fine_location_2 == "00":
                return calculate_neck_nij(c_fz, c_mocy, oop=code.fine_location_1 == "OP")[5]
            elif code.fine_location_2 == "CF":
                return calculate_neck_nij(c_fz, c_mocy, oop=code.fine_location_1 == "OP")[6]
            elif code.fine_location_2 == "CE":
                return calculate_neck_nij(c_fz, c_mocy, oop=code.fine_location_1 == "OP")[7]
            elif code.fine_location_2 == "TF":
                return calculate_neck_nij(c_fz, c_mocy, oop=code.fine_location_1 == "OP")[8]
            elif code.fine_location_2 == "TE":
                return calculate_neck_nij(c_fz, c_mocy, oop=code.fine_location_1 == "OP")[9]
    else:
        c_fz = isomme.get_channel(code.set(main_location="NECK", fine_location_1="UP", fine_location_2="00", physical_dimension="FO", direction="Z"))
        c_mocy = isomme.get_channel(code.set(main_location="NECK", fine_location_1="UP", fine_location_2="00", physical_dimension="MO", direction="Y"))
        if c_fz is not None and c_mocy is not None:
            if code.fine_location_2 == "00":
                return calculate_neck_nij(c_fz, c_mocy, oop=code.fine_location_1 == "OP")[0]
            elif code.fine_location_2 == "CF":
                return calculate_neck_nij(c_fz, c_mocy, oop=code.fine_location_1 == "OP")[1]
            elif code.fine_location_2 == "CE":
                return calculate_neck_nij(c_fz, c_mocy, oop=code.fine_location_1 == "OP")[2]
            elif code.fine_location_2 == "TF":
                return calculate_neck_nij(c_fz, c_mocy, oop=code.fine_location_1 == "OP")[3]
            elif code.fine_location_2 == "TE":
                return calculate_neck_nij(c_fz, c_mocy, oop=code.fine_location_1 == "OP")[4]
    return None


def _build_vc(isomme: Isomme, code: Code) -> Channel | None:
    # Viscous Criterion (Chest and Abdomen) (min/max of fine_location_1=LE and fine_location_1=RI)
    if code.main_location == "VCCR":
        if code.filter_class == "X":
            channel = isomme.get_channel(code.set(main_location="CHST", physical_dimension="DS", filter_class="C"))
            if channel is not None:
                return calculate_vc(channel)[1]
            channel = isomme.get_channel(code.set(main_location="TRRI", physical_dimension="DS", filter_class="C"))
            if channel is not None:
                return calculate_vc(channel)[1]
            channel = isomme.get_channel(code.set(main_location="RIBS", physical_dimension="DS", filter_class="C"))
            if channel is not None:
                return calculate_vc(channel)[1]
        else:
            channel = isomme.get_channel(code.set(main_location="CHST", physical_dimension="DS"))
            if channel is not None:
                return calculate_vc(channel)[0]
            channel = isomme.get_channel(code.set(main_location="TRRI", physical_dimension="DS"))
            if channel is not None:
                return calculate_vc(channel)[0]
            channel = isomme.get_channel(code.set(main_location="RIBS", physical_dimension="DS"))
            if channel is not None:
                return calculate_vc(channel)[0]

        if code.fine_location_2 == "00":
            if code.filter_class == "X":
                channel_up = isomme.get_channel(code.set(fine_location_2="UP"))
                channel_mi = isomme.get_channel(code.set(fine_location_2="MI"))
                channel_lo = isomme.get_channel(code.set(fine_location_2="LO"))
                if channel_up is not None and channel_mi is not None and channel_lo is not None:
                    t = time_intersect(channel_up, channel_mi, channel_lo)
                    values = np.array([channel_up.get_data(t=t),
                                       channel_mi.get_data(t=t, unit=channel_up.unit),
                                       channel_lo.get_data(t=t, unit=channel_up.unit)])
                    idx_max_abs = np.argmax(np.abs(values), axis=0)
                    new_values = values[idx_max_abs, np.arange(values.shape[1])]
                    return Channel(code=channel_up.code.set(fine_location_2="00"),
                                   data=pd.DataFrame(new_values, index=t),
                                   unit=channel_up.unit,
                                   info=channel_up.info)

                channel_01 = isomme.get_channel(code.set(fine_location_2="01", filter_class="C"))
                channel_02 = isomme.get_channel(code.set(fine_location_2="02", filter_class="C"))
                channel_03 = isomme.get_channel(code.set(fine_location_2="03", filter_class="C"))
                if channel_01 is not None and channel_02 is not None and channel_03 is not None:
                    value_01 = channel_01.get_data()[np.argmax(np.abs(channel_01.get_data()))]
                    value_02 = channel_02.get_data(unit=channel_01.unit)[np.argmax(np.abs(channel_02.get_data(unit=channel_01.unit)))]
                    value_03 = channel_03.get_data(unit=channel_01.unit)[np.argmax(np.abs(channel_03.get_data(unit=channel_01.unit)))]
                    value = np.array([value_01, value_02, value_03])[np.argmax(np.abs([value_01, value_02, value_03]))]
                    return Channel(code=channel_01.code.set(fine_location_2="00", filter_class="X"),
                                   data=pd.DataFrame([value]),
                                   unit=channel_01.unit)

                channel_LO = isomme.get_channel(code.set(fine_location_2="LO", filter_class="C"))
                channel_UP = isomme.get_channel(code.set(fine_location_2="UP", filter_class="C"))
                if channel_LO is not None and channel_UP is not None:
                    value_left = channel_LO.get_data()[np.argmax(np.abs(channel_LO.get_data()))]
                    value_right = channel_UP.get_data(unit=channel_LO.unit)[np.argmax(np.abs(channel_UP.get_data(unit=channel_LO.unit)))]
                    value = np.array([value_left, value_right])[np.argmax(np.abs([value_left, value_right]))]
                    return Channel(code=channel_LO.code.set(fine_location_2="00", filter_class="X"),
                                   data=pd.DataFrame([value]),
                                   unit=channel_LO.unit)
            else:
                channel_up = isomme.get_channel(code.set(fine_location_2="UP"))
                channel_mi = isomme.get_channel(code.set(fine_location_2="MI"))
                channel_lo = isomme.get_channel(code.set(fine_location_2="LO"))
                if channel_up is not None and channel_mi is not None and channel_lo is not None:
                    t = time_intersect(channel_up, channel_mi, channel_lo)
                    values = np.array([channel_up.get_data(t=t),
                                       channel_mi.get_data(t=t, unit=channel_up.unit),
                                       channel_lo.get_data(t=t, unit=channel_up.unit)])
                    new_values = values[np.argmax(np.abs(values), axis=0), np.arange(values.shape[1])]
                    return Channel(code=channel_up.code.set(fine_location_2="00"),
                                   data=pd.DataFrame(new_values, index=t),
                                   unit=channel_up.unit,
                                   info=channel_up.info)

                channel_01 = isomme.get_channel(code.set(fine_location_2="01"))
                channel_02 = isomme.get_channel(code.set(fine_location_2="02"))
                channel_03 = isomme.get_channel(code.set(fine_location_2="03"))
                if channel_01 is not None and channel_02 is not None and channel_03 is not None:
                    t = time_intersect(channel_01, channel_02, channel_03)
                    values = np.array([channel_01.get_data(t=t),
                                       channel_02.get_data(t=t, unit=channel_01.unit),
                                       channel_03.get_data(t=t, unit=channel_01.unit)])
                    idx_max_abs = np.argmax(np.abs(values), axis=0)
                    new_values = values[idx_max_abs, np.arange(values.shape[1])]
                    return Channel(code=channel_01.code.set(fine_location_2="00"),
                                   data=pd.DataFrame(new_values, index=t),
                                   unit=channel_01.unit)

                channel_LO = isomme.get_channel(code.set(fine_location_2="LO"))
                channel_UP = isomme.get_channel(code.set(fine_location_2="UP"))
                if channel_LO is not None and channel_UP is not None:
                    t = time_intersect(channel_LO, channel_UP)
                    values = np.array([channel_LO.get_data(t=t), channel_UP.get_data(t=t, unit=channel_LO.unit)])
                    idx_max_abs = np.argmax(np.abs(values), axis=0)
                    new_values = values[idx_max_abs, np.arange(values.shape[1])]
                    return Channel(code=channel_LO.code.set(fine_location_2="00"),
                                   data=pd.DataFrame(new_values, index=t),
                                   unit=channel_LO.unit)

    if code.main_location == "VCAR":
        if code.filter_class == "X":
            channel = isomme.get_channel(code.set(main_location="ABDO", physical_dimension="DS", filter_class="C"))
            if channel is not None:
                return calculate_vc(channel)[1]
            channel = isomme.get_channel(code.set(main_location="ABRI", physical_dimension="DS", filter_class="C"))
            if channel is not None:
                return calculate_vc(channel)[1]
        else:
            channel = isomme.get_channel(code.set(main_location="ABDO", physical_dimension="DS"))
            if channel is not None:
                return calculate_vc(channel)[0]
            channel = isomme.get_channel(code.set(main_location="ABRI", physical_dimension="DS"))
            if channel is not None:
                return calculate_vc(channel)[0]

        if code.fine_location_2 == "00":
            if code.filter_class == "X":
                channel_01 = isomme.get_channel(code.set(fine_location_2="01", filter_class="C"))
                channel_02 = isomme.get_channel(code.set(fine_location_2="02", filter_class="C"))
                if channel_01 is not None and channel_02 is not None:
                    value_left = channel_01.get_data()[np.argmax(np.abs(channel_01.get_data()))]
                    value_right = channel_02.get_data(unit=channel_01.unit)[np.argmax(np.abs(channel_02.get_data(unit=channel_01.unit)))]
                    value = np.array([value_left, value_right])[np.argmax(np.abs([value_left, value_right]))]
                    return Channel(code=channel_01.code.set(fine_location_2="00", filter_class="X"),
                                   data=pd.DataFrame([value]),
                                   unit=channel_01.unit)
            else:
                channel_01 = isomme.get_channel(code.set(fine_location_2="01"))
                channel_02 = isomme.get_channel(code.set(fine_location_2="02"))
                if channel_01 is not None and channel_02 is not None:
                    t = time_intersect(channel_01, channel_02)
                    values = np.array([channel_01.get_data(t=t), channel_02.get_data(t=t, unit=channel_01.unit)])
                    idx_max_abs = np.argmax(np.abs(values), axis=0)
                    new_values = values[idx_max_abs, np.arange(values.shape[1])]
                    return Channel(code=channel_01.code.set(fine_location_2="00"),
                                   data=pd.DataFrame(new_values, index=t),
                                   unit=channel_01.unit)

    if code.fine_location_1 == "00":
        if code.filter_class == "X":
            channel_left = isomme.get_channel(code.set(fine_location_1="LE", filter_class="C"))
            channel_right = isomme.get_channel(code.set(fine_location_1="RI", filter_class="C"))
            if channel_left is not None and channel_right is not None:
                value_left = channel_left.get_data()[np.argmax(np.abs(channel_left.get_data()))]
                value_right = channel_right.get_data(unit=channel_left.unit)[np.argmax(np.abs(channel_right.get_data(unit=channel_left.unit)))]
                value = np.array([value_left, value_right])[np.argmax(np.abs([value_left, value_right]))]
                return Channel(code=channel_left.code.set(fine_location_1="00", filter_class="X"),
                               data=pd.DataFrame([value]),
                               unit=channel_left.unit)
        else:
            channel_left = isomme.get_channel(code.set(fine_location_1="LE"))
            channel_right = isomme.get_channel(code.set(fine_location_1="RI"))
            if channel_left is not None and channel_right is not None:
                t = time_intersect(channel_left, channel_right)
                values = np.array([channel_left.get_data(t=t),
                                   channel_right.get_data(t=t, unit=channel_left.unit)])
                idx_max_abs = np.argmax(np.abs(values), axis=0)
                new_values = values[idx_max_abs, np.arange(values.shape[1])]
                return Channel(code=channel_left.code.set(fine_location_1="00"),
                               data=pd.DataFrame(new_values, index=t),
                               unit=channel_left.unit)
    return None


def _build_kthc_min(isomme: Isomme, code: Code) -> Channel | None:
    channel_left = isomme.get_channel(code.set(fine_location_1="LE"))
    channel_right = isomme.get_channel(code.set(fine_location_1="RI"))
    if channel_left is not None and channel_right is not None:
        idx_min = np.argmin([channel_left.get_data()[0], channel_right.get_data()[0]], axis=0)
        channel_min = [channel_left, channel_right][idx_min]
        return Channel(code=channel_min.code.set(fine_location_1="00"),
                       data=channel_min.data,
                       unit=channel_min.unit,
                       info=channel_min.info)
    return None


def _build_kthc_femur_impulse(isomme: Isomme, code: Code) -> Channel | None:
    channel_foz = isomme.get_channel(code.set(main_location="FEMR", physical_dimension="FO", filter_class="B"))
    if channel_foz is not None:
        return calculate_femur_impulse(channel_foz)
    return None


def _build_tibia_index(isomme: Isomme, code: Code) -> Channel | None:
    if (code.fine_location_1) not in ("RU", "RL", "LU", "LL"): return None

    fine_location_1 = "RI" if code.fine_location_1[0] == "R" else "LE"
    fine_location_2 = "UP" if code.fine_location_1[1] == "U" else "LO"

    channel_MOX = isomme.get_channel(code.set(main_location="TIBI", fine_location_1=fine_location_1, fine_location_2=fine_location_2, physical_dimension="MO", direction="X"))
    channel_MOY = isomme.get_channel(code.set(main_location="TIBI", fine_location_1=fine_location_1, fine_location_2=fine_location_2, physical_dimension="MO", direction="Y"))
    channel_FOZ = isomme.get_channel(code.set(main_location="TIBI", fine_location_1=fine_location_1, fine_location_2=fine_location_2, physical_dimension="FO", direction="Z"))

    if channel_MOX is None or channel_MOY is None or channel_FOZ is None:
        return None

    channels = (channel_MOX, channel_MOY, channel_FOZ)
    if not all(channel.code.fine_location_3 in ("H3", "HF", "TH", "T3") for channel in channels):
        return None
    
    return calculate_tibia_index(channel_MOX, channel_MOY, channel_FOZ)


def _build_tibia_index_using_total_moment(isomme: Isomme, code: Code) -> Channel | None:
    if (code.fine_location_1) not in ("RU", "RL", "LU", "LL"): return None

    fine_location_1 = "RI" if code.fine_location_1[0] == "R" else "LE"
    fine_location_2 = "UP" if code.fine_location_1[1] == "U" else "LO"

    channel_MOX = isomme.get_channel(code.set(main_location="TIBI", fine_location_1=fine_location_1, fine_location_2=fine_location_2, physical_dimension="MO", direction="X"))
    channel_MOY = isomme.get_channel(code.set(main_location="TIBI", fine_location_1=fine_location_1, fine_location_2=fine_location_2, physical_dimension="MO", direction="Y"))
    channel_FOZ = isomme.get_channel(code.set(main_location="TIBI", fine_location_1=fine_location_1, fine_location_2=fine_location_2, physical_dimension="FO", direction="Z"))
    
    if channel_MOX is None or channel_MOY is None or channel_FOZ is None:
        return None

    channels = (channel_MOX, channel_MOY, channel_FOZ)
    if not all(c.code.fine_location_3 in ("H3", "T3") for c in channels):
        return None

    fine_location_2s = {channel.code.fine_location_2 for channel in channels}
    if len(fine_location_2s) != 1:
        return None
    fine_location_2 = fine_location_2s.pop()

    if (fine_location_2 == "UP"):
        channel_MOY_total = calculate_adjusted_upper_tibia_moment_My(channel_MOY=channel_MOY, channel_FOZ=channel_FOZ)
    elif (fine_location_2 == "LO"):
        channel_MOY_total = calculate_adjusted_lower_tibia_moment_My(channel_MOY=channel_MOY, channel_FOZ=channel_FOZ)
    else:
        return None
    
    if channel_MOY_total is None:
        return None

    return calculate_tibia_index_using_total_moment(channel_MOX, channel_MOY_total, channel_FOZ)


def _build_chest_pc_score(isomme: Isomme, code: Code) -> Channel | None:
    channel_le_up_ds = isomme.get_channel(code.set(fine_location_1="LE", fine_location_2="UP"))
    channel_ri_up_ds = isomme.get_channel(code.set(fine_location_1="RI", fine_location_2="UP"))
    channel_le_lo_ds = isomme.get_channel(code.set(fine_location_1="LE", fine_location_2="LO"))
    channel_ri_lo_ds = isomme.get_channel(code.set(fine_location_1="RI", fine_location_2="LO"))
    if channel_le_up_ds is not None and channel_ri_up_ds is not None and channel_le_lo_ds is not None and channel_ri_lo_ds is not None:
        return calculate_chest_pc_score(channel_le_up_ds=channel_le_up_ds,
                                        channel_ri_up_ds=channel_ri_up_ds,
                                        channel_le_lo_ds=channel_le_lo_ds,
                                        channel_ri_lo_ds=channel_ri_lo_ds)
    return None


def _build_chst_irtracc_min(isomme: Isomme, code: Code) -> Channel | None:
    channels = [isomme.get_channel(code.set(fine_location_1=fine_location_1, fine_location_2=fine_location_2)) for fine_location_1, fine_location_2 in (("LE", "UP"), ("RI", "UP"), ("LE", "LO"), ("RI", "LO"))]
    if all(channel is not None for channel in channels) and all(channel.code.fine_location_3 in ("TH", "T3", "00", "??") for channel in channels):
        time = time_intersect(*channels)
        values = np.min([channel.get_data(t=time, unit=channels[0].unit) for channel in channels], axis=0)
        return Channel(code=channels[0].code.set(fine_location_1="00", fine_location_2="00"),
                       data=pd.DataFrame(values, index=time),
                       unit=channels[0].unit)
    return None


def _build_abdo_irtracc_min(isomme: Isomme, code: Code) -> Channel | None:
    channels = [isomme.get_channel(code.set(fine_location_1=fine_location_1, fine_location_2=fine_location_2)) for fine_location_1, fine_location_2 in (("LE", "00"), ("RI", "00"))]
    if all(channel is not None for channel in channels) and all(channel.code.fine_location_3 in ("TH", "T3", "00", "??") for channel in channels):
        time = time_intersect(*channels)
        values = np.min([channel.get_data(t=time, unit=channels[0].unit) for channel in channels], axis=0)
        return Channel(code=channels[0].code.set(fine_location_1="00", fine_location_2="00"),
                       data=pd.DataFrame(values, index=time),
                       unit=channels[0].unit)
    return None


def _build_thor_irtracc(isomme: Isomme, code: Code) -> Channel | None:
    if code.physical_dimension == "DC":
        delta = 15.65 if code.fine_location_2 == "UP" else -15.65 if code.fine_location_2 == "LO" else 0  # [mm]
        if code.direction == "X":
            channel_dc0 = isomme.get_channel(code.set(direction="0"))
            channel_any = isomme.get_channel(code.set(physical_dimension="AN", direction="Y"))
            channel_anz = isomme.get_channel(code.set(physical_dimension="AN", direction="Z"))
            if channel_dc0 is not None and channel_any is not None and channel_anz is not None:
                time = time_intersect(channel_dc0, channel_any, channel_anz)
                channel_any = channel_any.adjust_to_range(target_range=(-45, 45), unit="deg")
                channel_anz = channel_anz.adjust_to_range(target_range=(-45, 45), unit="deg")
                values = delta * np.sin(channel_any.get_data(t=time, unit="rad")) + channel_dc0.get_data(t=time, unit="mm") * np.cos(channel_any.get_data(t=time, unit="rad")) * np.cos(channel_anz.get_data(t=time, unit="rad"))
                return Channel(code=channel_dc0.code.set(direction="X"),
                               data=pd.DataFrame(values, index=time),
                               unit="mm")
        if code.direction == "Y":
            channel_dc0 = isomme.get_channel(code.set(direction="0"))
            channel_anz = isomme.get_channel(code.set(physical_dimension="AN", direction="Z"))
            if channel_dc0 is not None and channel_anz is not None:
                time = time_intersect(channel_dc0, channel_anz)
                channel_anz = channel_anz.adjust_to_range(target_range=(-45, 45), unit="deg")
                values = channel_dc0.get_data(t=time, unit="mm") * np.sin(channel_anz.get_data(t=time, unit="rad"))
                return Channel(code=channel_dc0.code.set(direction="Y"),
                               data=pd.DataFrame(values, index=time),
                               unit="mm")
        if code.direction == "Z":
            channel_dc0 = isomme.get_channel(code.set(direction="0"))
            channel_any = isomme.get_channel(code.set(physical_dimension="AN", direction="Y"))
            channel_anz = isomme.get_channel(code.set(physical_dimension="AN", direction="Z"))
            if channel_dc0 is not None and channel_any is not None and channel_anz is not None:
                time = time_intersect(channel_dc0, channel_any, channel_anz)
                channel_any = channel_any.adjust_to_range(target_range=(-45, 45), unit="deg")
                channel_anz = channel_anz.adjust_to_range(target_range=(-45, 45), unit="deg")
                values = delta * np.cos((channel_any).get_data(t=time, unit="rad")) - channel_dc0.get_data(t=time, unit="mm") * np.sin(channel_any.get_data(t=time, unit="rad")) * np.cos(channel_anz.get_data(t=time, unit="rad"))
                return Channel(code=channel_dc0.code.set(direction="Z"),
                               data=pd.DataFrame(values, index=time),
                               unit="mm")
    if code.physical_dimension == "DS":
        if code.direction == "0":
            channel_dc0 = isomme.get_channel(code.set(physical_dimension="DC"))
            if channel_dc0 is not None:
                return (channel_dc0 - channel_dc0.get_data(t=0)).set_code(physical_dimension="DS")
        if code.direction == "X":
            channel_dcx = isomme.get_channel(code.set(physical_dimension="DC", direction="X"))
            if channel_dcx is not None:
                return (channel_dcx - channel_dcx.get_data(t=0)).set_code(physical_dimension="DS")
        if code.direction == "Y":
            channel_dcy = isomme.get_channel(code.set(physical_dimension="DC", direction="Y"))
            if channel_dcy is not None:
                return (channel_dcy - channel_dcy.get_data(t=0)).set_code(physical_dimension="DS")
        if code.direction == "Z":
            channel_dcz = isomme.get_channel(code.set(physical_dimension="DC", direction="Z"))
            if channel_dcz is not None:
                return (channel_dcz - channel_dcz.get_data(t=0)).set_code(physical_dimension="DS")
    return None


def _build_worldsid_trri_min(isomme: Isomme, code: Code) -> Channel | None:
    channel_01 = isomme.get_channel(code.set(fine_location_2="01"))
    channel_02 = isomme.get_channel(code.set(fine_location_2="02"))
    channel_03 = isomme.get_channel(code.set(fine_location_2="03"))
    if channel_01 is not None and channel_02 is not None and channel_03 is not None:
        time = time_intersect(channel_01, channel_02, channel_03)
        values = np.min([channel.get_data(t=time, unit=channel_01.unit) for channel in (channel_01, channel_02, channel_03)], axis=0)
        return Channel(code=channel_01.code.set(fine_location_2="00"),
                       data=pd.DataFrame(values, index=time),
                       unit=channel_01.unit,)  # TODO: info
    return None


def _build_worldsid_abri_min(isomme: Isomme, code: Code) -> Channel | None:
    channel_01 = isomme.get_channel(code.set(fine_location_2="01"))
    channel_02 = isomme.get_channel(code.set(fine_location_2="02"))
    if channel_01 is not None and channel_02 is not None:
        time = time_intersect(channel_01, channel_02)
        values = np.min([channel.get_data(t=time, unit=channel_01.unit) for channel in (channel_01, channel_02)], axis=0)
        return Channel(code=channel_01.code.set(fine_location_2="00"),
                       data=pd.DataFrame(values, index=time),
                       unit=channel_01.unit)  # TODO info
    return None


def _build_worldsid_rib_irtracc(isomme: Isomme, code: Code) -> Channel | None:
    if code.physical_dimension == "DC" and code.direction == "Y":
        channel_dc0 = isomme.get_channel(code.set(physical_dimension="DC", direction="0"))
        channel_anz = isomme.get_channel(code.set(physical_dimension="AN", direction="Z"))
        if channel_dc0 is not None and channel_anz is not None:
            t = time_intersect(channel_dc0, channel_anz)
            channel_anz = channel_anz.adjust_to_range(target_range=(-45, 45), unit="deg")
            values = channel_dc0.get_data(t=t) * np.cos(channel_anz.get_data(t=t, unit="rad"))
            return Channel(
                code=channel_dc0.code.set(physical_dimension="DC", direction="Y"),
                data=pd.DataFrame(values, index=t),
                unit=channel_dc0.unit,
                info=channel_dc0.info
            )
    if code.physical_dimension == "DS":
        channel_dc = isomme.get_channel(code.set(physical_dimension="DC"))
        if channel_dc is not None:
            return (channel_dc - channel_dc.get_data(t=0)).set_code(physical_dimension="DS")
    return None


def _build_olc(isomme: Isomme, code: Code) -> Channel | None:
    tmp = code.set(fine_location_1="??", fine_location_2="??")
    if code.filter_class == "X":
        tmp = code.set(filter_class="A")
    channel = isomme.get_channel(tmp)

    if channel is not None:
        olc, olc_visual = calculate_olc(channel)
        if code.filter_class == "X":
            return olc
        else:
            return olc_visual
    return None


# --------------------------------------------------------------------------------------- #
# The registry. Order is significant and mirrors the original if-cascade: get_channel
# returns the result of the first provider whose matches() is true and whose build()
# yields a channel (a None build result falls through to the next matching provider).
# --------------------------------------------------------------------------------------- #

PROVIDERS: list[ChannelProvider] = [
    # Resultant
    _FnProvider(
        lambda c: c.direction == "R" and c.filter_class != "X",
        _build_resultant),
    # BrIC
    _FnProvider(
        lambda c: c.main_location == "BRIC" and c.filter_class == "X",
        _build_bric),
    # HIC
    _FnProvider(
        lambda c: c.main_location == "HICR" and c.filter_class == "X",
        _build_hic),
    # xms
    _FnProvider(
        lambda c: fnmatch.fnmatch(c.fine_location_2, "[0-9][CS]") and c.filter_class == "X",
        _build_xms),
    # Damage
    _FnProvider(
        lambda c: c.fine_location_1 == "DA" and c.fine_location_2 == "MA" and c.physical_dimension == "AA",
        _build_damage),
    # Neck Total Moment
    _FnProvider(
        lambda c: c.main_location == "TMON",
        _build_neck_total_moment),
    # Neck NIJ
    _FnProvider(
        lambda c: c.main_location == "NIJC",
        _build_nij),
    # Shoulder Lateral Force (Y) (min/max of left and right)
    AggregatePairProvider(
        lambda c: c.main_location == "SHLD" and c.fine_location_1 == "00" and c.physical_dimension == "FO" and c.direction == "Y",
        vary="fine_location_1", members=("LE", "RI"), agg="max_abs", keep_info=True),
    # Viscous Criterion (Chest and Abdomen)
    _FnProvider(
        lambda c: c.main_location in ("VCCR", "VCAR"),
        _build_vc),
    # ES-2 / ES-2re Abdomen Force (Min. of front/middle/rear)
    AggregatePairProvider(
        lambda c: c.main_location == "ABDO" and c.fine_location_2 == "00" and c.physical_dimension == "FO" and c.direction == "Y",
        vary="fine_location_2", members=("RE", "MI", "FR"), agg="min", keep_info=True),
    # Acetabulum Compression (Maximum of left and right)
    AggregatePairProvider(
        lambda c: c.main_location == "ACTB" and c.fine_location_1 == "00" and c.fine_location_2 == "00" and c.physical_dimension == "FO" and c.direction == "R",
        vary="fine_location_1", members=("LE", "RI"), agg="min"),
    # KTH (minimum of left and right, whole-channel select)
    _FnProvider(
        lambda c: c.main_location == "KTHC" and c.physical_dimension == "IM" and c.fine_location_1 == "00" and c.filter_class == "X",
        _build_kthc_min),
    # KTH femur impulse
    _FnProvider(
        lambda c: c.main_location == "KTHC" and c.physical_dimension == "IM" and c.fine_location_1 != "00" and c.filter_class == "X",
        _build_kthc_femur_impulse),
    # Femur Compression (Minimum of left and right)
    AggregatePairProvider(
        lambda c: c.main_location == "FEMR" and c.fine_location_1 == "00" and c.fine_location_2 == "00" and c.physical_dimension == "FO" and c.direction == "Z",
        vary="fine_location_1", members=("LE", "RI"), agg="min"),
    # Knee Slider Compression / Displacement (Minimum of left and right)
    AggregatePairProvider(
        lambda c: c.main_location == "KNSL" and c.fine_location_1 == "00" and c.fine_location_2 == "00" and c.physical_dimension in ("FO", "DS") and c.direction == "X",
        vary="fine_location_1", members=("LE", "RI"), agg="min"),
    
    # Tibia Compression (Minimum of left and right)
    AggregatePairProvider(
        lambda c: c.main_location == "TIBI" and c.fine_location_1 == "00" and c.physical_dimension == "FO" and c.direction == "Z",
        vary="fine_location_1", members=("LE", "RI"), agg="min"),
    # Tibia Compression (Minimum of upper and lower)
    AggregatePairProvider(
        lambda c: c.main_location == "TIBI" and c.fine_location_2 == "00" and c.physical_dimension == "FO" and c.direction == "Z",
        vary="fine_location_2", members=("UP", "LO"), agg="min"), 
    
    # Tibia Index
    _FnProvider(
        lambda c: c.main_location == "TIIN" and c.fine_location_2 == "00" and c.physical_dimension == "00" and c.direction == "0",
        _build_tibia_index),
    _FnProvider(
        lambda c: c.main_location == "TIIN" and c.fine_location_2 == "TO" and c.physical_dimension == "00" and c.direction == "0",
        _build_tibia_index_using_total_moment),
    # Tibia Index (Maximum of left/right and upper/lower)
    AggregatePairProvider(
        lambda c: c.main_location == "TIIN" and c.fine_location_1 == "00" and c.physical_dimension == "00" and c.direction == "0",
        vary="fine_location_1", members=("LU", "LL", "RU", "RL"), agg="max"),
    AggregatePairProvider(
        lambda c: c.main_location == "TIIN" and c.fine_location_1 == "L0" and c.physical_dimension == "00" and c.direction == "0",
        vary="fine_location_1", members=("LU", "LL"), agg="max"),
    AggregatePairProvider(
        lambda c: c.main_location == "TIIN" and c.fine_location_1 == "R0" and c.physical_dimension == "00" and c.direction == "0",
        vary="fine_location_1", members=("RU", "RL"), agg="max"),
    AggregatePairProvider(
        lambda c: c.main_location == "TIIN" and c.fine_location_1 == "0U" and c.physical_dimension == "00" and c.direction == "0",
        vary="fine_location_1", members=("LU", "RU"), agg="max"),
    AggregatePairProvider(
        lambda c: c.main_location == "TIIN" and c.fine_location_1 == "0L" and c.physical_dimension == "00" and c.direction == "0",
        vary="fine_location_1", members=("LL", "RL"), agg="max"),
    
    # THOR Dummy Chest PCA Score
    _FnProvider(
        lambda c: c.main_location == "CHST" and c.fine_location_1 == "00" and c.fine_location_2 == "PC" and c.physical_dimension == "DS" and c.filter_class != "X",
        _build_chest_pc_score),
    # THOR Dummy Chest Displacement (Minimum of individual IR-TRACC displacement)
    _FnProvider(
        lambda c: c.main_location == "CHST" and c.fine_location_1 == "00" and c.fine_location_2 == "00" and c.physical_dimension == "DS",
        _build_chst_irtracc_min),
    # THOR Dummy Abdomen Displacement (Minimum of individual IR-TRACC displacement)
    _FnProvider(
        lambda c: c.main_location == "ABDO" and c.fine_location_1 == "00" and c.fine_location_2 == "00" and c.physical_dimension == "DS",
        _build_abdo_irtracc_min),
    # THOR Dummy Chest/Abdomen IR-TRACC Displacement
    _FnProvider(
        lambda c: ((c.main_location == "CHST" and c.fine_location_1 in ("LE", "RI") and c.fine_location_2 in ("UP", "LO")) or (c.main_location == "ABDO" and c.fine_location_1 in ("LE", "RI") and c.fine_location_2 == "00")) and c.fine_location_3 in ("TH", "T3"),
        _build_thor_irtracc),
    # WorldSid Dummy Chest Displacement (Minimum of individual IR-TRACC displacement)
    _FnProvider(
        lambda c: c.main_location == "TRRI" and c.fine_location_2 == "00" and c.fine_location_3 in ("WS", "??") and c.physical_dimension == "DS",
        _build_worldsid_trri_min),
    # WorldSid Dummy Abdomen Displacement (Minimum of individual IR-TRACC displacement)
    _FnProvider(
        lambda c: c.main_location == "ABRI" and c.fine_location_2 == "00" and c.fine_location_3 in ("WS", "??") and c.physical_dimension == "DS",
        _build_worldsid_abri_min),
    # WorldSid Dummy Rib IR-TRACC Lateral Length and Absolute/Lateral Displacement
    _FnProvider(
        lambda c: c.main_location in ("TRRI", "ABRI") and c.fine_location_3 in ("WS", "??"),
        _build_worldsid_rib_irtracc),
    # ES-2 / ES-2re Rib Deflection (Min. of upper/middle/lower)
    AggregatePairProvider(
        lambda c: c.main_location == "RIBS" and c.fine_location_2 == "00" and c.physical_dimension == "DS" and c.direction == "Y",
        vary="fine_location_2", members=("UP", "MI", "LO"), agg="min", keep_info=True),
    # Foot Resultant Acceleration (Max. of left and right)
    AggregatePairProvider(
        lambda c: c.main_location == "FOOT" and c.fine_location_1 == "00" and c.physical_dimension == "AC" and c.direction == "R",
        vary="fine_location_1", members=("LE", "RI"), agg="max", keep_info=True),
    # OLC
    _FnProvider(
        lambda c: c.fine_location_1 == "0O" and c.fine_location_2 == "LC" and c.physical_dimension == "VE",
        _build_olc),
]
