"""Shared Hybrid III 50th-percentile frontal injury criteria for IIHS reports.

Small overlap Version VII Table 2 and Moderate Overlap 2.0 Version III Table 1
use the same H350M injury boundaries.  They live here once; each report supplies
its own component weights, restraints/kinematics, structure and overall cutoffs.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from pyisomme.calculate import calculate_femur_impulse
from pyisomme.channel import Channel
from pyisomme.limit import Limit
from pyisomme.limits import Limits
from pyisomme.report.criterion import Criterion, Role, sub
from pyisomme.report.iihs.limits import (
    Limit_A,
    Limit_G,
    Limit_M,
    Limit_P,
)
from pyisomme.report.manual import Manual, manual
from pyisomme.unit import Unit, g0


def _kth_demerits(force: float, impulse: float) -> tuple[float, str]:
    """IIHS H350M KTH force/impulse corridors (5%, 15%, 25% risk)."""
    boundaries = (
        (5.22, 5.69, 113.5, 0.0, Limit_G.color),
        (5.92, 7.69, 127.7, -2.0, Limit_A.color),
        (6.38, 8.92, 137.1, -6.0, Limit_M.color),
    )
    for force_low, force_high, impulse_limit, demerits, color in boundaries:
        if force <= force_low or (force <= force_high and impulse <= impulse_limit):
            return demerits, color
    return -10.0, Limit_P.color


class Criterion_HIC_15(Criterion):
    name = "HIC 15"
    validate_ignore = {
        "limit_flags": "discrete demerits use successive upper bounds with interpolation disabled",
    }

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}HICR0015??00RX")
        return [
            Limit_G(codes, lambda x: 560, y_unit=1, upper=True, rating=0),
            Limit_A(codes, lambda x: 700, y_unit=1, upper=True, rating=-2),
            Limit_M(codes, lambda x: 840, y_unit=1, upper=True, rating=-10),
            Limit_P(codes, lambda x: 840, y_unit=1, lower=True, rating=-20),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(self.ctx.code("?{p}HICR0015??00RX"))
        self.value = float(self.channel.get_data()[0])
        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
        self.color = self.limits.get_limit_min_color(self.channel)


class Criterion_Nij(Criterion):
    name = "Nij"
    validate_ignore = {
        "limit_flags": "discrete demerits use successive upper bounds with interpolation disabled",
    }

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}NIJCIP00??00Y?")
        return [
            Limit_G(codes, lambda x: 0.8, y_unit=1, upper=True, rating=0),
            Limit_A(codes, lambda x: 1.0, y_unit=1, upper=True, rating=-2),
            Limit_M(codes, lambda x: 1.2, y_unit=1, upper=True, rating=-10),
            Limit_P(codes, lambda x: 1.2, y_unit=1, lower=True, rating=-20),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(self.ctx.code("?{p}NIJCIP00??00YB"))
        self.value = float(np.max(self.channel.get_data()))
        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
        self.color = self.limits.get_limit_min_color(self.channel)


class Criterion_Neck_Tension(Criterion):
    name = "Neck axial tension"
    validate_ignore = {
        "limit_flags": "discrete demerits use successive upper bounds with interpolation disabled",
    }

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}NECKUP00??FOZ?")
        return [
            Limit_G(codes, lambda x: 2.6, y_unit="kN", upper=True, rating=0),
            Limit_A(codes, lambda x: 3.3, y_unit="kN", upper=True, rating=-2),
            Limit_M(codes, lambda x: 4.0, y_unit="kN", upper=True, rating=-10),
            Limit_P(codes, lambda x: 4.0, y_unit="kN", lower=True, rating=-20),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(
            self.ctx.code("?{p}NECKUP00??FOZB")
        ).convert_unit("kN")
        self.value = float(np.max(self.channel.get_data()))
        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
        self.color = self.limits.get_limit_min_color(self.channel)


class Criterion_Neck_Compression(Criterion):
    name = "Neck compression"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}NECKUP00??FOZ?")
        return [
            Limit_G(codes, lambda x: -3.2, y_unit="kN", lower=True, rating=0),
            Limit_A(codes, lambda x: -3.2, y_unit="kN", upper=True, rating=-2),
            Limit_M(codes, lambda x: -4.0, y_unit="kN", upper=True, rating=-10),
            Limit_P(codes, lambda x: -4.8, y_unit="kN", upper=True, rating=-20),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(
            self.ctx.code("?{p}NECKUP00??FOZB")
        ).convert_unit("kN")
        self.value = float(np.min(self.channel.get_data()))
        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
        self.color = self.limits.get_limit_min_color(self.channel)


class Criterion_Neck_Tension_Corridor(Criterion):
    name = "Neck tension duration corridor"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}NECKUP00??FOZ?")

        def corridor(x: float) -> float:
            return float(np.interp(x, [0, 0.035, 0.045], [3.3, 2.9, 1.1]))

        return [
            Limit_G(codes, corridor, x_unit="s", y_unit="kN", upper=True, rating=0),
            Limit_A(codes, corridor, x_unit="s", y_unit="kN", lower=True, rating=-2),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(
            self.ctx.code("?{p}NECKUP00??FOZB")
        ).convert_unit("kN")
        self.value = self.limits.get_limit_min_y(self.channel)
        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
        self.color = self.limits.get_limit_min_color(self.channel)


class Criterion_Neck_Compression_Corridor(Criterion):
    name = "Neck compression duration corridor"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}NECKUP00??FOZ?")

        def corridor(x: float) -> float:
            return float(np.interp(x, [0, 0.030], [-4.0, -1.1]))

        return [
            Limit_G(codes, corridor, x_unit="s", y_unit="kN", lower=True, rating=0),
            Limit_A(codes, corridor, x_unit="s", y_unit="kN", upper=True, rating=-2),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(
            self.ctx.code("?{p}NECKUP00??FOZB")
        ).convert_unit("kN")
        self.value = self.limits.get_limit_min_y(self.channel)
        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
        self.color = self.limits.get_limit_min_color(self.channel)


class Criterion_Neck_Shear_Corridor(Criterion):
    name = "Neck shear duration corridor"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}NECKUP00??FOX?")

        def positive(x: float) -> float:
            return float(np.interp(x, [0, 0.025, 0.035, 0.045], [3.1, 1.5, 1.5, 1.1]))

        def negative(x: float) -> float:
            return float(np.interp(x, [0, 0.035, 0.045], [-3.1, -1.5, -1.1]))

        return [
            Limit_G(codes, negative, x_unit="s", y_unit="kN", lower=True, rating=0),
            Limit_A(codes, negative, x_unit="s", y_unit="kN", upper=True, rating=-2),
            Limit_G(codes, positive, x_unit="s", y_unit="kN", upper=True, rating=0),
            Limit_A(codes, positive, x_unit="s", y_unit="kN", lower=True, rating=-2),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(
            self.ctx.code("?{p}NECKUP00??FOXB")
        ).convert_unit("kN")
        self.value = self.limits.get_limit_min_y(self.channel)
        positive = Limits(
            limit_list=[limit for limit in self.limits.limit_list if limit.func(0) > 0]
        )
        negative = Limits(
            limit_list=[limit for limit in self.limits.limit_list if limit.func(0) < 0]
        )
        positive_rating = positive.get_limit_min_rating(self.channel, interpolate=False)
        negative_rating = negative.get_limit_min_rating(self.channel, interpolate=False)
        if positive_rating <= negative_rating:
            self.rating = positive_rating
            self.color = positive.get_limit_min_color(self.channel)
        else:
            self.rating = negative_rating
            self.color = negative.get_limit_min_color(self.channel)


class Criterion_Head_Neck(Criterion):
    name = "Head and neck"
    role = Role.AGGREGATE
    aggregation = "min"
    hard_contact_downgrades: Manual[
        int,
        manual(
            0,
            source="video and head acceleration",
            doc=(
                "Rating levels required by the protocol's hard-contact flowchart. "
                "Use 0 when no qualifying contact occurred."
            ),
        ),
    ]

    criterion_hic_15 = sub(Criterion_HIC_15)
    criterion_nij = sub(Criterion_Nij)
    criterion_neck_tension = sub(Criterion_Neck_Tension)
    criterion_neck_compression = sub(Criterion_Neck_Compression)
    criterion_tension_corridor = sub(Criterion_Neck_Tension_Corridor)
    criterion_compression_corridor = sub(Criterion_Neck_Compression_Corridor)
    criterion_shear_corridor = sub(Criterion_Neck_Shear_Corridor)

    def calculation(self) -> None:
        if not 0 <= self.hard_contact_downgrades <= 3:
            raise ValueError("hard_contact_downgrades must be between 0 and 3")
        self.rating = self.min_of_children()
        for _ in range(self.hard_contact_downgrades):
            self.rating = {0.0: -2.0, -2.0: -10.0, -10.0: -20.0, -20.0: -20.0}.get(
                self.rating, np.nan
            )
        self.color = {
            0.0: Limit_G.color,
            -2.0: Limit_A.color,
            -10.0: Limit_M.color,
            -20.0: Limit_P.color,
        }.get(self.rating)


class Criterion_Thoracic_Spine_Acceleration(Criterion):
    name = "Thoracic spine acceleration (3 ms)"
    validate_ignore = {
        "limit_flags": "discrete demerits use successive upper bounds with interpolation disabled",
    }

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}CHST003C??ACR?")
        return [
            Limit_G(codes, lambda x: 60, y_unit=Unit(g0), upper=True, rating=0),
            Limit_A(codes, lambda x: 75, y_unit=Unit(g0), upper=True, rating=-2),
            Limit_M(codes, lambda x: 90, y_unit=Unit(g0), upper=True, rating=-10),
            Limit_P(codes, lambda x: 90, y_unit=Unit(g0), lower=True, rating=-20),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(
            self.ctx.code("?{p}CHST003C??ACRX")
        ).convert_unit(Unit(g0))
        self.value = float(self.channel.get_data()[0])
        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
        self.color = self.limits.get_limit_min_color(self.channel)


class Criterion_Sternum_Deflection(Criterion):
    name = "Sternum deflection"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}CHST0000??DSX?")
        return [
            Limit_G(codes, lambda x: -50, y_unit="mm", lower=True, rating=0),
            Limit_A(codes, lambda x: -50, y_unit="mm", upper=True, rating=-2),
            Limit_M(codes, lambda x: -60, y_unit="mm", upper=True, rating=-10),
            Limit_P(codes, lambda x: -75, y_unit="mm", upper=True, rating=-20),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(
            self.ctx.code("?{p}CHST0000??DSXC")
        ).convert_unit("mm")
        self.value = float(np.min(self.channel.get_data()))
        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
        self.color = self.limits.get_limit_min_color(self.channel)


class Criterion_Sternum_Deflection_Rate(Criterion):
    name = "Sternum deflection rate"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}CHST0000??VEX?")
        return [
            Limit_G(codes, lambda x: -6.6, y_unit="m/s", lower=True, rating=0),
            Limit_A(codes, lambda x: -6.6, y_unit="m/s", upper=True, rating=-2),
            Limit_M(codes, lambda x: -8.2, y_unit="m/s", upper=True, rating=-10),
            Limit_P(codes, lambda x: -9.8, y_unit="m/s", upper=True, rating=-20),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(
            self.ctx.code("?{p}CHST0000??VEXC")
        ).convert_unit("m/s")
        self.value = float(np.min(self.channel.get_data()))
        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
        self.color = self.limits.get_limit_min_color(self.channel)


class Criterion_Chest_VC(Criterion):
    name = "Viscous criterion"
    validate_ignore = {
        "limit_flags": "discrete demerits use successive upper bounds with interpolation disabled",
    }

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}VCCR0000??VEX?")
        return [
            Limit_G(codes, lambda x: 0.8, y_unit="m/s", upper=True, rating=0),
            Limit_A(codes, lambda x: 1.0, y_unit="m/s", upper=True, rating=-2),
            Limit_M(codes, lambda x: 1.2, y_unit="m/s", upper=True, rating=-10),
            Limit_P(codes, lambda x: 1.2, y_unit="m/s", lower=True, rating=-20),
        ]

    def calculation(self) -> None:
        raw_channel = self.require_channel(
            self.ctx.code("?{p}VCCR0000??VEXC")
        ).convert_unit("m/s")
        self.channel = Channel(
            raw_channel.code, pd.DataFrame(np.abs(raw_channel.data)), "m/s"
        )
        self.value = float(np.max(self.channel.get_data()))
        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
        self.color = self.limits.get_limit_min_color(self.channel)


class Criterion_Chest(Criterion):
    name = "Chest"
    role = Role.AGGREGATE
    aggregation = "min"

    criterion_acceleration = sub(Criterion_Thoracic_Spine_Acceleration)
    criterion_deflection = sub(Criterion_Sternum_Deflection)
    criterion_deflection_rate = sub(Criterion_Sternum_Deflection_Rate)
    criterion_vc = sub(Criterion_Chest_VC)

    def calculation(self) -> None:
        self.rating = self.min_of_children()
        self.color = {
            0.0: Limit_G.color,
            -2.0: Limit_A.color,
            -10.0: Limit_M.color,
            -20.0: Limit_P.color,
        }.get(self.rating)


class Criterion_KTH_Side(Criterion):
    side = "LE"
    impulse: float = np.nan

    def calculation(self) -> None:
        self.channel = self.require_channel(
            self.ctx.code(f"?{{p}}FEMR{self.side}00??FOZB")
        ).convert_unit("kN")
        self.value = abs(float(np.min(self.channel.get_data())))
        impulse_channel = calculate_femur_impulse(self.channel)
        self.impulse = abs(float(impulse_channel.get_data(unit="N s")[0]))
        self.rating, self.color = _kth_demerits(self.value, self.impulse)


class Criterion_KTH_Left(Criterion_KTH_Side):
    name = "Left knee-thigh-hip injury risk"
    side = "LE"


class Criterion_KTH_Right(Criterion_KTH_Side):
    name = "Right knee-thigh-hip injury risk"
    side = "RI"


class Criterion_Thigh_Hip(Criterion):
    name = "Thigh and hip"
    role = Role.AGGREGATE
    aggregation = "min"

    criterion_left = sub(Criterion_KTH_Left)
    criterion_right = sub(Criterion_KTH_Right)

    def calculation(self) -> None:
        self.rating = self.min_of_children()
        self.color = {
            0.0: Limit_G.color,
            -2.0: Limit_A.color,
            -6.0: Limit_M.color,
            -10.0: Limit_P.color,
        }.get(self.rating)


class Criterion_Tibia_Femur_Displacement(Criterion):
    name = "Tibia-femur displacement"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}KNSL??00??DSX?")
        return [
            Limit_G(codes, lambda x: -12, y_unit="mm", lower=True, rating=0),
            Limit_A(codes, lambda x: -12, y_unit="mm", upper=True, rating=-1),
            Limit_M(codes, lambda x: -15, y_unit="mm", upper=True, rating=-2),
            Limit_P(codes, lambda x: -18, y_unit="mm", upper=True, rating=-4),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(
            self.ctx.code("?{p}KNSL0000??DSXC")
        ).convert_unit("mm")
        self.value = abs(float(np.min(self.channel.get_data())))
        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
        self.color = self.limits.get_limit_min_color(self.channel)


class Criterion_Tibia_Index(Criterion):
    name = "Tibia index"
    validate_ignore = {
        "limit_flags": "discrete demerits use successive upper bounds with interpolation disabled",
    }

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}TIIN??TO??000?")
        return [
            Limit_G(codes, lambda x: 0.8, y_unit=1, upper=True, rating=0),
            Limit_A(codes, lambda x: 1.0, y_unit=1, upper=True, rating=-1),
            Limit_M(codes, lambda x: 1.2, y_unit=1, upper=True, rating=-2),
            Limit_P(codes, lambda x: 1.2, y_unit=1, lower=True, rating=-4),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(self.ctx.code("?{p}TIIN00TO??000B"))
        self.value = float(np.max(self.channel.get_data()))
        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
        self.color = self.limits.get_limit_min_color(self.channel)


class Criterion_Tibia_Axial_Force(Criterion):
    name = "Tibia axial force"

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}TIBI??LO??FOZ?")
        return [
            Limit_G(codes, lambda x: -4, y_unit="kN", lower=True, rating=0),
            Limit_A(codes, lambda x: -4, y_unit="kN", upper=True, rating=-1),
            Limit_M(codes, lambda x: -6, y_unit="kN", upper=True, rating=-2),
            Limit_P(codes, lambda x: -8, y_unit="kN", upper=True, rating=-4),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(
            self.ctx.code("?{p}TIBI00LO??FOZB")
        ).convert_unit("kN")
        self.value = abs(float(np.min(self.channel.get_data())))
        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
        self.color = self.limits.get_limit_min_color(self.channel)


class Criterion_Foot_Acceleration(Criterion):
    name = "Foot acceleration"
    validate_ignore = {
        "limit_flags": "discrete demerits use successive upper bounds with interpolation disabled",
    }

    def define_limits(self) -> list[Limit]:
        codes = self.ctx.codes("?{p}FOOT??00??ACR?")
        return [
            Limit_G(codes, lambda x: 150, y_unit=Unit(g0), upper=True, rating=0),
            Limit_A(codes, lambda x: 200, y_unit=Unit(g0), upper=True, rating=-1),
            Limit_M(codes, lambda x: 260, y_unit=Unit(g0), upper=True, rating=-2),
            Limit_P(codes, lambda x: 260, y_unit=Unit(g0), lower=True, rating=-4),
        ]

    def calculation(self) -> None:
        self.channel = self.require_channel(
            self.ctx.code("?{p}FOOT0000??ACRB"),
            filter=False,
        ).convert_unit(Unit(g0))
        self.value = float(np.max(np.abs(self.channel.get_data())))
        self.rating = self.limits.get_limit_min_rating(self.channel, interpolate=False)
        self.color = self.limits.get_limit_min_color(self.channel)


class Criterion_Leg_Foot(Criterion):
    name = "Leg and foot"
    role = Role.AGGREGATE
    aggregation = "min"

    criterion_tibia_femur_displacement = sub(Criterion_Tibia_Femur_Displacement)
    criterion_tibia_index = sub(Criterion_Tibia_Index)
    criterion_tibia_axial_force = sub(Criterion_Tibia_Axial_Force)
    criterion_foot_acceleration = sub(Criterion_Foot_Acceleration)

    def calculation(self) -> None:
        self.rating = self.min_of_children()
        if not np.isnan(self.rating):
            self.color = next(
                child.color
                for child in self.children_by_role()
                if child.rating == self.rating
            )


class Criterion_H350M_Injury(Criterion):
    name = "H350M injury measures"
    role = Role.AGGREGATE
    aggregation = "sum"

    criterion_head_neck = sub(Criterion_Head_Neck)
    criterion_chest = sub(Criterion_Chest)
    criterion_thigh_hip = sub(Criterion_Thigh_Hip)
    criterion_leg_foot = sub(Criterion_Leg_Foot)

    def calculation(self) -> None:
        self.rating = self.sum_of_children()
        self.value = -self.rating
