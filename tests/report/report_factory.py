from __future__ import annotations

from typing import Callable

from pyisomme import Channel, Isomme, create_sample
from pyisomme.report import (
    FMVSS_208,
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
                    create_sample(code="11HEAD0000H3ACRA", y_range=(0, 100)).scale_y(scale_y),
                    create_sample(code="11HICR0015H300RX", y_range=(0, 500)).scale_y(scale_y),
                    create_sample(code="11HEAD003CH3ACRX", y_range=(0, 100)).scale_y(scale_y),
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
                    create_sample(code="13HICR0015H300RX", y_range=(0, 500)).scale_y(scale_y),
                    create_sample(code="13HEAD003CH3ACRX", y_range=(0, 100)).scale_y(scale_y),
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
                    create_sample(code="11HICR0015H300RX", y_range=(0, 500)).scale_y(scale_y),
                    create_sample(code="11HEAD003CH3ACRX", y_range=(0, 100)).scale_y(scale_y),
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
                    create_sample(code="11HICR0015H300RX", y_range=(0, 500)).scale_y(scale_y),
                    create_sample(code="11HEAD0000H3ACXA", mode="sin", y_range=(-500, 500)).scale_y(scale_y),
                    create_sample(code="11HEAD0000H3ACYA", mode="sin", y_range=(-500, 500)).scale_y(scale_y),
                    create_sample(code="11HEAD0000H3ACZA", mode="sin", y_range=(-500, 500)).scale_y(scale_y),
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
                    create_sample(code="11HICR0015H300RX", y_range=(0, 500)).scale_y(scale_y),
                    create_sample(code="11HEAD0000H3ACRA", y_range=(0, 100)).scale_y(scale_y),
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
                    create_sample(code="11HICR0015H300RX", y_range=(0, 500)).scale_y(scale_y),
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
                    create_sample(code="11HICR0015H300RX", y_range=(0, 500)).scale_y(scale_y),
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
                    create_sample(code="11HICR0015H300RX", y_range=(0, 500)).scale_y(scale_y),
                    create_sample(code="11NECKUP00H3FOZB", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="11TRRILE01H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11TRRILE02H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11TRRILE03H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11ABRILE01H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11ABRILE02H3DSYC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11ACTBLE00H3FOYB", y_range=(0, 1000)).scale_y(scale_y),
                    create_sample(code="11ILUMLE00H3FOYB", y_range=(0, 1000)).scale_y(scale_y),
                    create_sample(code="16HICR0015H300RX", y_range=(0, 500)).scale_y(scale_y),
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
                    create_sample(code="11HICR0036H300RX", y_range=(0, 500)).scale_y(scale_y),
                    create_sample(code="11HEAD003CH3ACRX", y_range=(0, 100)).scale_y(scale_y),
                    create_sample(code="11NECKUP00H3FOZA", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="11NECKUP00H3FOXA", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="11NECKUP00H3MOYB", y_range=(-20, 20)).scale_y(scale_y),
                    create_sample(code="11CHST0000H3DSXC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11VCCR0003H3VEXC", y_range=(-0.5, 0.5)).scale_y(scale_y),
                    create_sample(code="11FEMR0000H3FOZB", y_range=(-2000, 0)).scale_y(scale_y),
                    create_sample(code="13HICR0036H300RX", y_range=(0, 500)).scale_y(scale_y),
                    create_sample(code="13HEAD003CH3ACRX", y_range=(0, 100)).scale_y(scale_y),
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
                    create_sample(code="11HICR0036H300RX", y_range=(0, 500)).scale_y(scale_y),
                    create_sample(code="11HEAD003CH3ACRX", y_range=(0, 100)).scale_y(scale_y),
                    create_sample(code="11NECKUP00H3FOZA", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="11NECKUP00H3FOXA", y_range=(-1000, 1000)).scale_y(scale_y),
                    create_sample(code="11NECKUP00H3MOYB", y_range=(-20, 20)).scale_y(scale_y),
                    create_sample(code="11CHST0000H3DSXC", y_range=(-0.03, 0)).scale_y(scale_y),
                    create_sample(code="11VCCR0003H3VEXC", y_range=(-0.5, 0.5)).scale_y(scale_y),
                    create_sample(code="11FEMR0000H3FOZB", y_range=(-2000, 0)).scale_y(scale_y),
                    create_sample(code="11TIBI0000H3FOZB", y_range=(-2000, 5)).scale_y(scale_y),
                    create_sample(code="11TIIN0000H3000B", y_range=(0, 0.5)).scale_y(scale_y),
                    create_sample(code="11KNSL0000H3DSXC", y_range=(-0.01, 0)).scale_y(scale_y),
                    create_sample(code="13HICR0036H300RX", y_range=(0, 500)).scale_y(scale_y),
                    create_sample(code="13HEAD003CH3ACRX", y_range=(0, 100)).scale_y(scale_y),
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
                    create_sample(code="11HICR0036H300RX", y_range=(0, 500)).scale_y(scale_y),
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
                    create_sample(code="11HICR0036H300RX", y_range=(0, 500)).scale_y(scale_y),
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


REPORT_FACTORIES: dict[type[BaseReport], Callable[[], BaseReport]] = {
    # Reports
    Correlation: build_correlation,
    EuroNCAP_Frontal_50kmh: build_euroncap_frontal_50kmh,
    EuroNCAP_Frontal_MPDB: build_euroncap_frontal_mpdb,
    EuroNCAP_Side_Barrier: build_euroncap_side_barrier,
    EuroNCAP_Side_FarSide: build_euroncap_side_farside,
    EuroNCAP_Side_Pole: build_euroncap_side_pole,
    FMVSS_208: build_fmvss_208,
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
