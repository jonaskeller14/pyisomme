from __future__ import annotations

from math import pi
from typing import Callable

from pyisomme import Channel, Isomme, create_sample
from pyisomme.report import (
    FMVSS_208,
    FMVSS_214,
    Correlation,
    EuroNCAP,
    EuroNCAP_Frontal_50kmh,
    EuroNCAP_Frontal_MPDB,
    EuroNCAP_Side_Barrier,
    EuroNCAP_Side_FarSide,
    EuroNCAP_Side_Pole,
    IIHS_Frontal_Moderate_Overlap,
    IIHS_Frontal_Small_Overlap,
    IIHS_Side_Impact,
    UN_Frontal_50kmh_R137,
    UN_Frontal_56kmh_ODB_R94,
    UN_Side_Barrier_R95,
    UN_Side_Pole_R135,
)
from pyisomme.report.base_report import BaseReport
from pyisomme.report.meta_report import MetaReport
from pyisomme.unit import Unit, g0


def build_head_acceleration_channels(
    test_object: str = "1",
    position: str = "1",
    seed: int = 0,
    scale_y: float = 1.0,
) -> list[Channel]:
    """Build only measured XYZ head acceleration; derived channels stay lazy."""
    channels = [
        create_sample(
            code="11HEAD0000H3ACXA",
            mode="pulse",
            y_range=(0, -500),
            noise_per=0.01,
            seed=seed,
        ),
        create_sample(
            code="11HEAD0000H3ACYA",
            mode="pulse",
            y_range=(0, -150),
            noise_per=0.01,
            seed=seed,
        ),
        create_sample(
            code="11HEAD0000H3ACZA",
            mode="sin",
            y_range=(100, -100),
            noise_per=0.01,
            seed=seed,
        ),
    ]
    return [
        channel.scale_y(scale_y).set_code(
            test_object=test_object, position=position
        )
        for channel in channels
    ]


def build_hf_channels(
    test_object: str = "1", position: str = "1", seed: int = 0, scale_y: float = 1.0
) -> list[Channel]:
    # fmt: off
    channels = [
        create_sample(code="11HEAD0000HFACXA", mode="pulse", y_range=(0, -500), noise_per=0.01, seed=seed),
        create_sample(code="11HEAD0000HFACYA", mode="pulse", y_range=(0, -150), noise_per=0.01, seed=seed),
        create_sample(code="11HEAD0000HFACZA", mode="sin", y_range=(100, -100), noise_per=0.01, seed=seed),
        create_sample(code="11NECKUP00HFMOYB", mode="sin", y_range=(-15,20), unit="Nm"),
        create_sample(code="11NECKUP00HFFOXA", mode="sin", y_range=(-300,400), unit="N"),
        create_sample(code="11NECKUP00HFFOZA", mode="pulse", y_range=(0,1200), unit="N"),
        create_sample(code="11CHST0000HFDSXB", mode="pulse", y_range=(0, -30), unit="mm", noise_per=0.01),
        create_sample(code="11FEMRLE00HFFOZB", mode="sin", y_range=(400,-1000), unit="N", noise_per=0.01),
        create_sample(code="11FEMRRI00HFFOZB", mode="sin", y_range=(400,-1000), unit="N", noise_per=0.01),
    ]
    # fmt: on
    return [
        c.scale_y(scale_y).set_code(test_object=test_object, position=position)
        for c in channels
    ]


def build_h3_channels(
    test_object: str = "1", position: str = "1", seed: int = 0, scale_y: float = 1.0
) -> list[Channel]:
    # fmt: off
    channels = [
        create_sample(code="11HEAD0000H3ACXA", mode="pulse", y_range=(0, -500), noise_per=0.01, seed=seed),
        create_sample(code="11HEAD0000H3ACYA", mode="pulse", y_range=(0, -150), noise_per=0.01, seed=seed),
        create_sample(code="11HEAD0000H3ACZA", mode="sin", y_range=(100, -100), noise_per=0.01, seed=seed),
        create_sample(code="11NECKUP00H3MOYB", mode="sin", y_range=(-15,20), unit="Nm"),
        create_sample(code="11NECKUP00H3FOXA", mode="sin", y_range=(-300,400), unit="N"),
        create_sample(code="11NECKUP00H3FOZA", mode="pulse", y_range=(0,1200), unit="N"),
        create_sample(code="11CHST0000H3DSXB", mode="pulse", y_range=(0, -30), unit="mm", noise_per=0.01),
        create_sample(code="11FEMRLE00H3FOZB", mode="sin", y_range=(500,-1100), unit="N", noise_per=0.01),
        create_sample(code="11FEMRRI00H3FOZB", mode="sin", y_range=(500,-1100), unit="N", noise_per=0.01),
    ]
    # fmt: on
    return [
        c.scale_y(scale_y).set_code(test_object=test_object, position=position)
        for c in channels
    ]


def build_seatbelt_channels(
    test_object: str = "1", position: str = "1", seed: int = 0, scale_y: float = 1.0
) -> list[Channel]:
    # fmt: off
    channels = [
        create_sample(code="11SEBE0000B1FOXD", mode="pulse", y_range=(0, 1000), unit="N", noise_per=0.01, seed=seed),
        create_sample(code="11SEBE0000B2FOXD", mode="pulse", y_range=(0, 2000), unit="N", noise_per=0.01, seed=seed),
        create_sample(code="11SEBE0000B3FOXD", mode="pulse", y_range=(0, 3000), unit="N", noise_per=0.01, seed=seed),
        create_sample(code="11SEBE0000B4FOXD", mode="pulse", y_range=(0, 4000), unit="N", noise_per=0.01, seed=seed),
        create_sample(code="11SEBE0000B5FOXD", mode="pulse", y_range=(0, 5000), unit="N", noise_per=0.01, seed=seed),
        create_sample(code="11SEBE0000B6FOXD", mode="pulse", y_range=(0, 6000), unit="N", noise_per=0.01, seed=seed),
    ]
    # fmt: on
    return [
        channel.scale_y(scale_y).set_code(test_object=test_object, position=position)
        for channel in channels
    ]


def build_vehicle_channels(
    test_object: str = "1", seed: int = 0, scale_y: float = 1.0
) -> list[Channel]:
    # fmt: off
    channels = [
        create_sample(
            code="10VEHCCG0000ACXA",
            mode="pulse",
            t_range=(0.0, 0.3, 3001),
            y_range=(0.0, -100.0),
            unit="m/s^2",
            noise_per=0.01,
            seed=seed,
        ),
    ]
    # fmt: on
    return [
        channel.scale_y(scale_y).set_code(test_object=test_object)
        for channel in channels
    ]


def _build_correlation_channels(
    amplitude: float,
    phase: float,
    frequency_offset: float,
    unique_suffix: str,
) -> list[Channel]:
    # fmt: off
    return [

        create_sample(code="11HEAD0000H3ACXA", t_range=(0, 0.2, 2001), y_range=(-1, 1), frequency=8 + frequency_offset, seed=0,)
        .scale_y(amplitude)
        .offset_x(phase),
        create_sample(code="11HEAD0000H3ACYA", t_range=(0, 0.2, 2001), y_range=(-1, 1), frequency=12 + frequency_offset, seed=0,)
        .scale_y(amplitude)
        .offset_x(phase),
        create_sample(code="11HEAD0000H3ACZA", t_range=(0, 0.2, 2001), y_range=(-1, 1), frequency=16 + frequency_offset, seed=0,)
        .scale_y(amplitude)
        .offset_x(phase),
        create_sample(code=f"11CHST0000H3DSX{unique_suffix}", t_range=(0, 0.2, 2001), y_range=(-1, 1), frequency=4, seed=0,),
    ]
    # fmt: on


def build_correlation() -> Correlation:
    return Correlation(
        isomme_list=[
            Isomme(
                test_number=f"v{index}",
                channels=_build_correlation_channels(
                    amplitude=amplitude,
                    phase=phase,
                    frequency_offset=frequency_offset,
                    unique_suffix=str(index),
                ),
            )
            for index, (amplitude, phase, frequency_offset) in enumerate(
                ((1.0, 0.0, 0.0), (1.08, 0.001, 0.3), (0.8, -0.002, 1.0)),
                1,
            )
        ]
    )


def build_euroncap_frontal_mpdb() -> EuroNCAP_Frontal_MPDB:
    SCALES_Y = [0.5, 1, 2]
    # fmt: off
    return EuroNCAP_Frontal_MPDB(
        isomme_list=[
            Isomme(
                test_number=f"v{idx}",
                channels=[
                    *build_head_acceleration_channels(position="1", scale_y=scale_y),
                    create_sample(code="11HEADDAMAH3AARA", y_range=(0, 1)).scale_y(scale_y),
                    create_sample(code="11NECKUP00H3MOYB", y_range=(-20, 20)).scale_y(scale_y),
                    create_sample(code="11NECKUP00H3FOZA", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="11NECKUP00H3FOXA", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="11CHST0000H3DSXC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11SEBE0000B3FOXD", y_range=(0, 3000)).scale_y(scale_y),
                    create_sample(code="11ABDO0000H3DSXC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11ACTB0000H3FORB", y_range=(0, 1000)).scale_y(scale_y),
                    create_sample(code="11FEMR0000H3FOZB", y_range=(-2000, 0)).scale_y(scale_y),
                    create_sample(code="11KNSL0000H3DSXC", y_range=(-0.01, 0)).scale_y(scale_y),
                    create_sample(code="11TIIN0000H3000B", y_range=(0, 0.5)).scale_y(scale_y),
                    create_sample(code="11TIBI0000H3FOZB", y_range=(-2000, 5)).scale_y(scale_y),
                    *build_head_acceleration_channels(position="3", scale_y=scale_y),
                    create_sample(code="13NECKUP00H3FOXA", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="13NECKUP00H3FOZA", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="13NECKUP00H3MOYB", y_range=(-20, 20)).scale_y(scale_y),
                    create_sample(code="13CHST0003H3DSXC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="13VCCR0003H3VEXC", y_range=(-0.5, 0.5)).scale_y(scale_y),
                    create_sample(code="13SEBE0000B3FOXD", y_range=(0, 3000)).scale_y(scale_y),
                    create_sample(code="13FEMR0000H3FOZB", y_range=(-2000, 0)).scale_y(scale_y),
                    create_sample(code="13KNSL0000H3DSXC", y_range=(-0.01, 0)).scale_y(scale_y),
                    create_sample(code="13TIIN0000H3000B", y_range=(0, 0.5)).scale_y(scale_y),
                    create_sample(code="13TIBI0000H3FOZB", y_range=(-2000, 5)).scale_y(scale_y),
                    create_sample(code="M1MBAR000000VEXA", mode="linear", y_range=(20, 0), unit="m/s").scale_y(scale_y),
                ],
            )
            for idx, scale_y in enumerate(SCALES_Y, 1)
        ]
    )
    # fmt: on


def build_euroncap_side_barrier() -> EuroNCAP_Side_Barrier:
    SCALES_Y = [0.5, 1, 2]
    # fmt: off
    return EuroNCAP_Side_Barrier(
        isomme_list=[
            Isomme(
                test_number=f"v{idx}",
                channels=[
                    *build_head_acceleration_channels(position="1", scale_y=scale_y),
                    create_sample(code="11TRRI0000H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11VCCR0000H3VEYC", y_range=(-0.5, 0.5)).scale_y(scale_y),
                    create_sample(code="11SHLD0000H3FOYB", y_range=(0, 1000)).scale_y(scale_y),
                    create_sample(code="11ABRI0000H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11VCAR0000H3VEYC", y_range=(-0.5, 0.5)).scale_y(scale_y),
                    create_sample(code="11PUBC0000H3FOYB", y_range=(0, 1000)).scale_y(scale_y),
                ],
            )
            for idx, scale_y in enumerate(SCALES_Y, 1)
        ]
    )
    # fmt: on


def build_euroncap_side_farside() -> EuroNCAP_Side_FarSide:
    SCALES_Y = [0.5, 1, 2]
    # fmt: off
    return EuroNCAP_Side_FarSide(
        isomme_list=[
            Isomme(
                test_number=f"v{idx}",
                channels=[
                    *build_head_acceleration_channels(position="1", scale_y=scale_y),
                    create_sample(code="11HEAD0000H3AVXA", mode="sin", y_range=(-10, 10)).scale_y(scale_y),
                    create_sample(code="11HEAD0000H3AVYA", mode="sin", y_range=(-10, 10)).scale_y(scale_y),
                    create_sample(code="11HEAD0000H3AVZA", mode="sin", y_range=(-10, 10)).scale_y(scale_y),
                    create_sample(code="11NECKUP00H3FOZA", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="11TMONUP00H3MOXB", y_range=(-20, 20)).scale_y(scale_y),
                    create_sample(code="11TMONUP00H3MOYB", y_range=(-20, 20)).scale_y(scale_y),
                    create_sample(code="11NECKLO00H3FOZA", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="11TMONLO00H3MOXB", y_range=(-20, 20)).scale_y(scale_y),
                    create_sample(code="11TMONLO00H3MOYB", y_range=(-20, 20)).scale_y(scale_y),
                    create_sample(code="11TRRI0000H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11TRRILE01H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11TRRIRI01H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11TRRILE02H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11TRRIRI02H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11TRRILE03H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11TRRIRI03H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11ABRI0000H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11ABRILE01H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11ABRIRI01H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11ABRILE02H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11ABRIRI02H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11PUBC0000H3FOYB", y_range=(0, 1000)).scale_y(scale_y),
                    create_sample(code="11LUSP0000H3FOYB", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="11LUSP0000H3FOZB", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="11LUSP0000H3MOXB", y_range=(-20, 20)).scale_y(scale_y),
                ],
            )
            for idx, scale_y in enumerate(SCALES_Y, 1)
        ]
    )
    # fmt: on


def build_euroncap_side_pole() -> EuroNCAP_Side_Pole:
    SCALES_Y = [0.5, 1, 2]
    # fmt: off
    return EuroNCAP_Side_Pole(
        isomme_list=[
            Isomme(
                test_number=f"v{idx}",
                channels=[
                    *build_head_acceleration_channels(position="1", scale_y=scale_y),
                    create_sample(code="11TRRI0000H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11VCCR0000H3VEYC", y_range=(-0.5, 0.5)).scale_y(scale_y),
                    create_sample(code="11SHLD0000H3FOYB", y_range=(0, 1000)).scale_y(scale_y),
                    create_sample(code="11ABRI0000H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11VCAR0000H3VEYC", y_range=(-0.5, 0.5)).scale_y(scale_y),
                    create_sample(code="11PUBC0000H3FOYB", y_range=(0, 1000)).scale_y(scale_y),
                ],
            )
            for idx, scale_y in enumerate(SCALES_Y, 1)
        ]
    )
    # fmt: on


def build_iihs_frontal_small_overlap() -> IIHS_Frontal_Small_Overlap:
    SCALES_Y = [0.5, 1, 2]
    # fmt: off
    return IIHS_Frontal_Small_Overlap(
        isomme_list=[
            Isomme(
                test_number=f"v{idx}",
                channels=[
                    # H3 is the IIHS small-overlap H350M dummy.  Supply raw
                    # measurements only; report pages request their CFC-filtered
                    # and calculated variants (including resultant/HIC and NIJ).
                    *[
                        create_sample(code=f"11HEAD0000H3AC{axis}X", mode=mode, y_range=y_range, noise_per=0.01, seed=idx).scale_y(scale_y)
                        for axis, mode, y_range in (
                            ("X", "pulse", (6, -483)),
                            ("Y", "pulse", (-4, -137)),
                            ("Z", "sin", (94, -108)),
                        )
                    ],
                    create_sample(code="11NECKUP00H3FOZX", y_range=(-900, 1000), unit="N", frequency=13, noise=15, seed=idx).scale_y(scale_y),
                    create_sample(code="11NECKUP00H3FOXX", y_range=(-872, 914), unit="N").scale_y(scale_y),
                    create_sample(code="11NECKUP00H3MOYX", y_range=(-35, 45), unit="Nm", frequency=13, noise=2, seed=idx + 10, phase_offset=pi / 2).scale_y(scale_y),
                    create_sample(code="11CHST0000H3ACRX", y_range=(5, 91)).scale_y(scale_y),
                    create_sample(code="11CHST0000H3DSXX", y_range=(-0.028, 0.002), unit="m").scale_y(scale_y),
                    create_sample(code="11CHST0000H3VEXX", y_range=(-0.46, 0.04), unit="m/s").scale_y(scale_y),
                    create_sample(code="11VCCR0000H3VEXX", y_range=(-0.41, 0.48), unit="m/s").scale_y(scale_y),
                    create_sample(code="11FEMRLE00H3FOZX", y_range=(-1840, 62), unit="N").scale_y(scale_y),
                    create_sample(code="11FEMRRI00H3FOZX", y_range=(-2115, 84), unit="N").scale_y(scale_y),
                    create_sample(code="11KNSL0000H3DSXX", y_range=(-0.011, 0.001), unit="m").scale_y(scale_y),
                    create_sample(code="11KNSLLE00H3DSXX", y_range=(-0.009, 0.002), unit="m").scale_y(scale_y),
                    create_sample(code="11KNSLRI00H3DSXX", y_range=(-0.013, 0.001), unit="m").scale_y(scale_y),
                    create_sample(code="11TIIN00TOH3000X", y_range=(0.03, 0.47)).scale_y(scale_y),
                    *[
                        create_sample(code=f"11TIIN{side}H3000X", y_range=y_range).scale_y(scale_y)
                        for side, y_range in (
                            ("LUTO", (0.02, 0.43)),
                            ("RUTO", (0.04, 0.51)),
                            ("LLTO", (0.01, 0.39)),
                            ("RLTO", (0.05, 0.48)),
                        )
                    ],
                    create_sample(code="11TIBI00LOH3FOZX", y_range=(-1930, 7), unit="N").scale_y(scale_y),
                    create_sample(code="11TIBILELOH3FOZX", y_range=(-1775, 11), unit="N").scale_y(scale_y),
                    create_sample(code="11TIBIRILOH3FOZX", y_range=(-2180, 4), unit="N").scale_y(scale_y),
                    create_sample(code="11FOOTLE00H3ACRX", y_range=(0, 92)).scale_y(scale_y),
                    create_sample(code="11FOOTRI00H3ACRX", y_range=(0, 105)).scale_y(scale_y),
                ],
            )
            for idx, scale_y in enumerate(SCALES_Y, 1)
        ]
    )
    # fmt: on


def build_iihs_frontal_moderate_overlap() -> IIHS_Frontal_Moderate_Overlap:
    SCALES_Y = [0.5, 1, 2]
    # fmt: off
    return IIHS_Frontal_Moderate_Overlap(
        isomme_list=[
            Isomme(
                test_number=f"v{idx}",
                channels=[
                    *build_head_acceleration_channels(position="1", scale_y=scale_y),
                    create_sample(code="11NIJCIP00H300YB", y_range=(0, 0.5)).scale_y(scale_y),
                    create_sample(code="11NECKUP00H3FOZB", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="11NECKUP00H3FOXB", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="11CHST003C00ACRX", y_range=(0, 100)).scale_y(scale_y),
                    create_sample(code="11CHST0000H3DSXC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11CHST0000H3VEXC", y_range=(-0.5, 0.5)).scale_y(scale_y),
                    create_sample(code="11VCCR0000H3VEXC", y_range=(-0.5, 0.5)).scale_y(scale_y),
                    create_sample(code="11FEMRLE00H3FOZB", y_range=(-2000, 0)).scale_y(scale_y),
                    create_sample(code="11FEMRRI00H3FOZB", y_range=(-2000, 0)).scale_y(scale_y),
                    create_sample(code="11KNSL0000H3DSXC", y_range=(-0.01, 0)).scale_y(scale_y),
                    create_sample(code="11TIIN00TOH3000B", y_range=(0, 0.5)).scale_y(scale_y),
                    create_sample(code="11TIBI00LOH3FOZB", y_range=(-2000, 5)).scale_y(scale_y),
                    create_sample(code="11FOOT0000H3ACRB", y_range=(0, 100)).scale_y(scale_y),
                    *build_head_acceleration_channels(position="6", scale_y=scale_y),
                    create_sample(code="16NECKUP00H3FOZB", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="16CHST0000H3DSXC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="16SEBE0000B3FOXC", y_range=(0, 3000)).scale_y(scale_y),
                    create_sample(code="16FEMR0000H3FOZB", y_range=(-2000, 0)).scale_y(scale_y),
                ],
            )
            for idx, scale_y in enumerate(SCALES_Y, 1)
        ]
    )
    # fmt: on


def build_iihs_side_impact() -> IIHS_Side_Impact:
    SCALES_Y = [0.5, 1, 2]
    # fmt: off
    report = IIHS_Side_Impact(
        isomme_list=[
            Isomme(
                test_number=f"v{idx}",
                channels=[
                    *build_head_acceleration_channels(position="1", scale_y=scale_y),
                    create_sample(code="11NECKUP00H3FOZB", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="11TRRILE01H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11TRRILE02H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11TRRILE03H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11ABRILE01H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11ABRILE02H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11ACTBLE00H3FOYB", y_range=(0, 1000)).scale_y(scale_y),
                    create_sample(code="11ILUMLE00H3FOYB", y_range=(0, 1000)).scale_y(scale_y),
                    *build_head_acceleration_channels(position="6", scale_y=scale_y),
                    create_sample(code="16NECKUP00H3FOZB", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="16TRRILE01H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="16TRRILE02H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="16TRRILE03H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="16ABRILE01H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="16ABRILE02H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="16ACTBLE00H3FOYB", y_range=(0, 1000)).scale_y(scale_y),
                    create_sample(code="16ILUMLE00H3FOYB", y_range=(0, 1000)).scale_y(scale_y),
                ],
            )
            for idx, scale_y in enumerate(SCALES_Y, 1)
        ]
    )
    # fmt: on
    for isomme in report.isomme_list:
        report.overall(isomme).criterion_structure.b_pillar_to_seat_centerline_cm = 20.0

    return report
    # fmt: on


def build_un_frontal_50kmh_r137() -> UN_Frontal_50kmh_R137:
    SCALES_Y = [0.5, 1, 2]
    # fmt: off
    return UN_Frontal_50kmh_R137(
        isomme_list=[
            Isomme(
                test_number=f"v{idx}",
                channels=[
                    *build_head_acceleration_channels(position="1", scale_y=scale_y),
                    create_sample(code="11NECKUP00H3FOZA", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="11NECKUP00H3FOXA", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="11NECKUP00H3MOYB", y_range=(-20, 20)).scale_y(scale_y),
                    create_sample(code="11CHST0000H3DSXC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11VCCR0003H3VEXC", y_range=(-0.5, 0.5)).scale_y(scale_y),
                    create_sample(code="11FEMR0000H3FOZB", y_range=(-2000, 0)).scale_y(scale_y),
                    *build_head_acceleration_channels(position="3", scale_y=scale_y),
                    create_sample(code="13NECKUP00H3FOZA", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="13NECKUP00H3FOXA", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="13NECKUP00H3MOYB", y_range=(-20, 20)).scale_y(scale_y),
                    create_sample(code="13CHST0000H3DSXC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="13VCCR0003H3VEXC", y_range=(-0.5, 0.5)).scale_y(scale_y),
                    create_sample(code="13FEMR0000H3FOZB", y_range=(-2000, 0)).scale_y(scale_y),
                ],
            )
            for idx, scale_y in enumerate(SCALES_Y, 1)
        ]
    )
    # fmt: on


def build_un_frontal_56kmh_odb_r94() -> UN_Frontal_56kmh_ODB_R94:
    SCALES_Y = [0.5, 1, 2]
    # fmt: off
    return UN_Frontal_56kmh_ODB_R94(
        isomme_list=[
            Isomme(
                test_number=f"v{idx}",
                channels=[
                    *build_head_acceleration_channels(position="1", scale_y=scale_y),
                    create_sample(code="11NECKUP00H3FOZA", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="11NECKUP00H3FOXA", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="11NECKUP00H3MOYB", y_range=(-20, 20)).scale_y(scale_y),
                    create_sample(code="11CHST0000H3DSXC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11VCCR0003H3VEXC", y_range=(-0.5, 0.5)).scale_y(scale_y),
                    create_sample(code="11FEMR0000H3FOZB", y_range=(-2000, 0)).scale_y(scale_y),
                    create_sample(code="11TIBI0000H3FOZB", y_range=(-2000, 5)).scale_y(scale_y),
                    create_sample(code="11TIIN0000H3000B", y_range=(0, 0.5)).scale_y(scale_y),
                    create_sample(code="11KNSL0000H3DSXC", y_range=(-0.01, 0)).scale_y(scale_y),
                    *build_head_acceleration_channels(position="3", scale_y=scale_y),
                    create_sample(code="13NECKUP00H3FOZA", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="13NECKUP00H3FOXA", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="13NECKUP00H3MOYB", y_range=(-20, 20)).scale_y(scale_y),
                    create_sample(code="13CHST0000H3DSXC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="13VCCR0003H3VEXC", y_range=(-0.5, 0.5)).scale_y(scale_y),
                    create_sample(code="13FEMR0000H3FOZB", y_range=(-2000, 0)).scale_y(scale_y),
                    create_sample(code="13TIBI0000H3FOZB", y_range=(-2000, 5)).scale_y(scale_y),
                    create_sample(code="13TIIN0000H3000B", y_range=(0, 0.5)).scale_y(scale_y),
                    create_sample(code="13KNSL0000H3DSXC", y_range=(-0.01, 0)).scale_y(scale_y),
                ],
            )
            for idx, scale_y in enumerate(SCALES_Y, 1)
        ]
    )
    # fmt: on


def build_un_side_pole_r135() -> UN_Side_Pole_R135:
    SCALES_Y = [0.5, 1, 2]
    # fmt: off
    return UN_Side_Pole_R135(
        isomme_list=[
            Isomme(
                test_number=f"v{idx}",
                channels=[
                    *build_head_acceleration_channels(position="1", scale_y=scale_y),
                    create_sample(code="11SHLD0000H3FOYB", y_range=(0, 1000)).scale_y(scale_y),
                    create_sample(code="11TRRI0000H3DSRB", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11ABRI0000H3DSRB", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11THSP123CH3ACRX", y_range=(0, 100)).scale_y(scale_y),
                    create_sample(code="11PUBC0000H3FOYB", y_range=(0, 1000)).scale_y(scale_y),
                ],
            )
            for idx, scale_y in enumerate(SCALES_Y, 1)
        ]
    )
    # fmt: on


def build_un_side_barrier_r95() -> UN_Side_Barrier_R95:
    SCALES_Y = [0.5, 1, 2]
    # fmt: off
    return UN_Side_Barrier_R95(
        isomme_list=[
            Isomme(
                test_number=f"v{idx}",
                channels=[
                    *build_head_acceleration_channels(position="1", scale_y=scale_y),
                    create_sample(code="11RIBSLE00H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11VCCRLE00H3VEYC", y_range=(-0.5, 0.5)).scale_y(scale_y),
                    create_sample(code="11PUBC0000H3FOYB", y_range=(0, 1000)).scale_y(scale_y),
                    create_sample(code="11ABDOLE00H3FOYB", y_range=(0, 1000)).scale_y(scale_y),
                ],
            )
            for idx, scale_y in enumerate(SCALES_Y, 1)
        ]
    )
    # fmt: on


def build_euro_ncap() -> MetaReport:
    """Build the available EuroNCAP MetaReport from the standard fixtures."""
    return EuroNCAP(
        frontal_50kmh=build_euroncap_frontal_50kmh(),
        frontal_mpdb=build_euroncap_frontal_mpdb(),
        side_pole=build_euroncap_side_pole(),
        side_barrier=build_euroncap_side_barrier(),
        side_farside=build_euroncap_side_farside(),
    )


def build_euroncap_frontal_50kmh() -> EuroNCAP_Frontal_50kmh:
    SCALES_Y = [1, 1.5]
    return EuroNCAP_Frontal_50kmh(
        isomme_list=[
            Isomme(
                test_number=f"v{idx}",
                channels=build_vehicle_channels(seed=idx, scale_y=scale_y)
                + build_seatbelt_channels(position="1", seed=idx, scale_y=scale_y)
                + build_seatbelt_channels(position="3", seed=idx, scale_y=scale_y)
                + build_seatbelt_channels(position="6", seed=idx, scale_y=scale_y)
                + build_hf_channels(position="1", seed=idx, scale_y=scale_y)
                + build_hf_channels(position="3", seed=idx, scale_y=scale_y)
                + build_hf_channels(position="6", seed=idx, scale_y=scale_y),
            )
            for idx, scale_y in enumerate(SCALES_Y, 1)
        ]
    )


def build_fmvss_208() -> FMVSS_208:
    SCALES_Y = [0.5, 2, 10]
    return FMVSS_208(
        isomme_list=[
            Isomme(
                test_number=f"v{idx}",
                channels=build_vehicle_channels(seed=idx, scale_y=scale_y)
                + build_h3_channels(position="1", seed=idx, scale_y=scale_y)
                + build_h3_channels(position="3", seed=idx, scale_y=scale_y)
                + [
                    create_sample(code="11CHST003CH3ACRX", y_range=(0, 100)).scale_y(
                        scale_y
                    ),
                    create_sample(code="13CHST003CH3ACRX", y_range=(0, 100)).scale_y(
                        scale_y
                    ),
                ],
            )
            for idx, scale_y in enumerate(SCALES_Y, 1)
        ]
    )


def build_fmvss_214_occupant_channels(
    dummy_type: str, position: str, scale_y: float
) -> list[Channel]:
    common = [
        create_sample(
            code=f"1{position}HEAD0000{dummy_type}ACXA",
            mode="pulse",
            y_range=(0, -500),
            noise_per=0.01,
        ),
        create_sample(
            code=f"1{position}HEAD0000{dummy_type}ACYA",
            mode="pulse",
            y_range=(0, -150),
            noise_per=0.01,
        ),
        create_sample(
            code=f"1{position}HEAD0000{dummy_type}ACZA",
            mode="sin",
            y_range=(100, -100),
            noise_per=0.01,
        ),
    ]
    if dummy_type == "ER":
        channels = common + [
            *[
                create_sample(
                    code=f"1{position}RIBSLE{level}ERDSYC",
                    y_range=(0, 30),
                    unit="mm",
                )
                for level in ("UP", "MI", "LO")
            ],
            *[
                create_sample(
                    code=f"1{position}ABDOLE{location}ERFOYB",
                    y_range=(0, 700),
                    unit="N",
                )
                for location in ("FR", "MI", "RE")
            ],
            create_sample(
                code=f"1{position}PUBC0000ERFOYB",
                y_range=(0, 5000),
                unit="N",
            ),
        ]
    else:
        channels = common + [
            create_sample(
                code=f"1{position}SPINLO00S2ACRB",
                y_range=(0, 70),
                unit=Unit(g0),
            ),
            create_sample(
                code=f"1{position}ACTBLE00S2FOYB",
                y_range=(0, 2400),
                unit="N",
            ),
            create_sample(
                code=f"1{position}ILUMLE00S2FOYB",
                y_range=(0, 2400),
                unit="N",
            ),
        ]
    return [channel.scale_y(scale_y) for channel in channels]


def build_fmvss_214() -> FMVSS_214:
    report = FMVSS_214(
        isomme_list=[
            Isomme(
                test_number="barrier-es2re-sid-iis",
                channels=(
                    build_fmvss_214_occupant_channels("ER", "1", 0.5)
                    + build_fmvss_214_occupant_channels("S2", "6", 0.5)
                ),
            ),
            Isomme(
                test_number="pole-es2re",
                channels=(
                    build_fmvss_214_occupant_channels("ER", "3", 0.5)
                    + build_fmvss_214_occupant_channels("S2", "4", 10)
                ),
            ),
            Isomme(
                test_number="pole-sid-iis",
                channels=(
                    build_fmvss_214_occupant_channels("S2", "1", 1.5)
                    + build_fmvss_214_occupant_channels("S2", "6", 10)
                ),
            ),
        ]
    )
    for isomme in report.isomme_list:
        overall = report.overall(isomme)
        if str(isomme.test_number).startswith("pole-"):
            # Rear SID-IIs data is deliberately present and far above every limit.
            # The manual pole load-case selection must keep it out of compliance.
            overall.impact_type = "pole"
        door = report.overall(isomme).criterion_door_integrity
        door.struck_door_remained_attached = True
        door.unstruck_doors_remained_latched = True
        door.latches_hinges_and_anchorages_remained_attached = True
    return report


REPORT_FACTORIES: dict[type[BaseReport], Callable[[], BaseReport]] = {
    # Reports
    Correlation: build_correlation,
    EuroNCAP_Frontal_50kmh: build_euroncap_frontal_50kmh,
    EuroNCAP_Frontal_MPDB: build_euroncap_frontal_mpdb,
    EuroNCAP_Side_Barrier: build_euroncap_side_barrier,
    EuroNCAP_Side_FarSide: build_euroncap_side_farside,
    EuroNCAP_Side_Pole: build_euroncap_side_pole,
    FMVSS_208: build_fmvss_208,
    FMVSS_214: build_fmvss_214,
    IIHS_Frontal_Small_Overlap: build_iihs_frontal_small_overlap,
    IIHS_Frontal_Moderate_Overlap: build_iihs_frontal_moderate_overlap,
    IIHS_Side_Impact: build_iihs_side_impact,
    UN_Frontal_50kmh_R137: build_un_frontal_50kmh_r137,
    UN_Frontal_56kmh_ODB_R94: build_un_frontal_56kmh_odb_r94,
    UN_Side_Pole_R135: build_un_side_pole_r135,
    UN_Side_Barrier_R95: build_un_side_barrier_r95,
    # MetaReports
    EuroNCAP: build_euro_ncap,
}
