# IIHS_Frontal_Small_Overlap

| property | value |
| --- | --- |
| name | IIHS \| Frontal Impact against Small Overlap Barrier with 25% Overlap at 64 km/h |
| protocol | VII |
| protocols | VII |
| overall criterion | `Overall` |
| pages | Page_Cover, Page_Driver_Result_Values_Chart, Page_Driver_Rating_Table, Page_Driver_Values_Table, Page_Driver_Head_Acceleration, Page_Driver_Neck_NIJ, Page_Driver_Neck_Load, Page_Driver_Neck_Load_Corridor, Page_Driver_Femur_Axial_Force, Page_Driver_Tibia_Compression, Page_Driver_Tibia_Index_Total, Page_Driver_Foot_Acceleration |

## `Overall` — Overall

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Overall` | — | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| p_driver | str | '1' | — | test report | Channel-code position of the driver. Defaults to the 'Driver position object 1' test-info field when the test carries it. |

## `criterion_driver` — Driver

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Driver` | — | — | — |

## `criterion_driver/criterion_head_neck` — Head & Neck

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_Neck` | — | — | — |

## `criterion_driver/criterion_head_neck/criterion_hic_15` — HIC 15

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HIC_15` | — | 0 (from limits) | — |

Limits for `?1HICR??15??00RX`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 560 | 0 | green | upper | 1 | - |
| Acceptable | 560 | -2 | yellow | lower | 1 | - |
| Marginal | 700 | -10 | orange | lower | 1 | - |
| Poor | 840 | -20 | red | lower | 1 | - |

## `criterion_driver/criterion_head_neck/criterion_nij` — NIJ

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_NIJ` | — | 0 (from limits) | — |

Limits for `?1NIJCIP????00Y?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 0.8 | 0 | green | upper | 1 | - |
| Acceptable | 0.8 | -2 | yellow | lower | 1 | - |
| Marginal | 1 | -10 | orange | lower | 1 | - |
| Poor | 1.2 | -20 | red | lower | 1 | - |

## `criterion_driver/criterion_head_neck/criterion_fz_tension` — Neck Fz Tension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Fz_Tension` | — | 0 (from limits) | — |

Limits for `?1NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 2.6 | 0 | green | upper | kN | - |
| Acceptable | 2.6 | -2 | yellow | lower | kN | - |
| Marginal | 3.3 | -10 | orange | lower | kN | - |
| Poor | 4 | -20 | red | lower | kN | - |

## `criterion_driver/criterion_head_neck/criterion_fz_compression` — Neck Fz Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Fz_Compression` | — | 0 (from limits) | — |

Limits for `?1NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -3.2 | 0 | green | lower | kN | - |
| Acceptable | -3.2 | -2 | yellow | upper | kN | - |
| Marginal | -4 | -10 | orange | upper | kN | - |
| Poor | -4.8 | -20 | red | upper | kN | - |

## `criterion_driver/criterion_head_neck/criterion_fz_tension_corridor` — Neck Fz Tension Corridor

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Fz_Tension_Corridor` | — | 0 (from limits) | — |

Limits for `?1NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | x=0:3.3, 0.01:3.299885714, 0.05:3.299428571, 0.1:3.298857143 | 0 | green | upper | kN | - |
| Acceptable | x=0:3.3, 0.01:3.299885714, 0.05:3.299428571, 0.1:3.298857143 | -2 | yellow | lower | kN | - |

## `criterion_driver/criterion_head_neck/criterion_fz_compression_corridor` — Neck Fz Compression Corridor

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Fz_Compression_Corridor` | — | 0 (from limits) | — |

Limits for `?1NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | x=0:-4, 0.01:-3.999033333, 0.05:-3.995166667, 0.1:-3.990333333 | 0 | green | lower | kN | - |
| Acceptable | x=0:-4, 0.01:-3.999033333, 0.05:-3.995166667, 0.1:-3.990333333 | -2 | yellow | upper | kN | - |

## `criterion_driver/criterion_head_neck/criterion_fx_shear_corridor` — Neck Fx Shear Corridor

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Fx_Shear_Corridor` | — | 0 (from limits) | — |

Limits for `?1NECKUP00??FOX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | x=0:-3.1, 0.01:-3.09936, 0.05:-3.0968, 0.1:-3.0936 | 0 | green | lower | kN | - |
| Acceptable | x=0:-3.1, 0.01:-3.09936, 0.05:-3.0968, 0.1:-3.0936 | -2 | yellow | upper | kN | - |
| Good | x=0:3.1, 0.01:3.09936, 0.05:3.0968, 0.1:3.0936 | 0 | green | upper | kN | - |
| Acceptable | x=0:3.1, 0.01:3.09936, 0.05:3.0968, 0.1:3.0936 | -2 | yellow | lower | kN | - |

## `criterion_driver/criterion_chest` — Chest

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest` | — | — | — |

## `criterion_driver/criterion_chest/criterion_acceleration` — Thoracic Spine Acceleration (3ms)

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Acceleration` | — | 0 (from limits) | — |

Limits for `?1CHST003C??ACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 60 | 0 | green | upper | g0 | - |
| Acceptable | 60 | -2 | yellow | lower | g0 | - |
| Marginal | 75 | -10 | orange | lower | g0 | - |
| Poor | 90 | -20 | red | lower | g0 | - |

## `criterion_driver/criterion_chest/criterion_deflection` — Sternum Deflection

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Deflection` | — | 0 (from limits) | — |

Limits for `11CHST0000??DSX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -50 | 0 | green | lower | mm | - |
| Acceptable | -50 | -2 | yellow | upper | mm | - |
| Marginal | -60 | -10 | orange | upper | mm | - |
| Poor | -75 | -20 | red | upper | mm | - |

## `criterion_driver/criterion_chest/criterion_deflection_rate` — Sternum Deflection Rate

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Deflection_Rate` | — | 0 (from limits) | — |

Limits for `11CHST0000??VEX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -6.6 | 0 | green | lower | m/s | - |
| Acceptable | -6.6 | -2 | yellow | upper | m/s | - |
| Marginal | -8.2 | -10 | orange | upper | m/s | - |
| Poor | -9.8 | -20 | red | upper | m/s | - |

## `criterion_driver/criterion_chest/criterion_vc` — Viscous Criterion

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_VC` | — | 0 (from limits) | — |

Limits for `?1VCCR0000??VEX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Poor | -1.2 | -20 | red | upper | m/s | - |
| Marginal | -1.2 | -10 | orange | lower | m/s | - |
| Acceptable | -1 | -2 | yellow | lower | m/s | - |
| Good | -0.8 | 0 | green | lower | m/s | - |
| Good | 0.8 | 0 | green | upper | m/s | - |
| Acceptable | 0.8 | -2 | yellow | lower | m/s | - |
| Marginal | 1 | -10 | orange | lower | m/s | - |
| Poor | 1.2 | -20 | red | lower | m/s | - |

## `criterion_driver/criterion_thigh_hip` — Tight & Hip

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Thigh_Hip` | — | — | — |

## `criterion_driver/criterion_thigh_hip/criterion_kth` — Knee Thigh Hip Injury Risk (KTH)

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_KTH` | — | 6 (from limits) | — |

Limits for `?1KTHC??????00??`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | inf | 0 | green | upper | N*s | - |
| Acceptable | inf | -2 | yellow | lower | N*s | - |
| Marginal | inf | 6 | orange | lower | N*s | - |
| Poor | inf | -10 | red | lower | N*s | - |

## `criterion_driver/criterion_leg_foot` — Leg & Foot

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Leg_Foot` | — | — | — |

## `criterion_driver/criterion_leg_foot/criterion_tibia_femur_displacement` — Tibia/Femur Displacement

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Tibia_Femur_Displacemnt` | — | — | — |

## `criterion_driver/criterion_leg_foot/criterion_tibia_index` — Tibia Index

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Tibia_Index` | — | 0 (from limits) | — |

Limits for `?1TIIN??TO??000?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 0.8 | 0 | green | upper | 1 | - |
| Acceptable | 0.8 | -1 | yellow | lower | 1 | - |
| Marginal | 1 | -2 | orange | lower | 1 | - |
| Poor | 1.2 | -4 | red | lower | 1 | - |

## `criterion_driver/criterion_leg_foot/criterion_tibia_axial_force` — Tibia Axial Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Tibia_Axial_Force` | — | 0 (from limits) | — |

Limits for `?1TIBI??LO??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -4 | 0 | green | lower | kN | - |
| Acceptable | -4 | -1 | yellow | upper | kN | - |
| Marginal | -6 | -2 | orange | upper | kN | - |
| Poor | -8 | -4 | red | upper | kN | - |

## `criterion_driver/criterion_leg_foot/criterion_foot_acceleration` — Foot Acceleration

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Foot_Acceleration` | — | 0 (from limits) | — |

Limits for `?1FOOT0000??AC??`, `?1FOOTLE00??AC??`, `?1FOOTRI00??AC??`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 150 | 0 | green | upper | g0 | - |
| Acceptable | 150 | -1 | yellow | lower | g0 | - |
| Marginal | 200 | -2 | orange | lower | g0 | - |
| Poor | 260 | -4 | red | lower | g0 | - |
