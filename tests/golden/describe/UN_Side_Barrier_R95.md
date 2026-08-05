# UN_Side_Barrier_R95

| property | value |
| --- | --- |
| name | UN-R95 \| Barrier Side Impact at 50 km/h |
| protocol | 12.09.2023 |
| protocols | 12.09.2023 |
| overall criterion | `Overall` |
| pages | Page_Cover, Page_Values_Chart, Page_Values_Table, Page_Head_Acceleration, Page_Chest_Lateral_Deflection, Page_Chest_Lateral_VC, Page_Pubic_Symphysis_Force, Page_Abdomen_Force |

## `Overall` — Overall

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Overall` | — | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| p | str | '1' | — | test report | Channel-code position of the struck-side occupant — the only occupant the regulation assesses. Defaults to the 'Driver position object 1' test-info field when the test carries it. |

## `criterion_dummy` — Dummy

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Dummy` | — | — | — |

## `criterion_dummy/criterion_hpc36` — Head Performance Criterion (HPC 36)

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HPC36` | — | 1 (from limits) | — |

Limits for `?1HICR0036??00RX`, `?1HICRCG36??00RX`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 1000 | True | green | upper | 1 | - |
| Fail | 1000 | False | red | lower | 1 | - |

## `criterion_dummy/criterion_chest_lateral_deflection` — Chest Lateral Deflection

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Lateral_Deflection` | — | 1 (from limits) | — |

Limits for `?1RIBS??????DSY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -42 | False | red | upper | mm | - |
| Pass | -42 | True | green | lower | mm | - |
| Fail | 42 | False | red | lower | mm | - |

## `criterion_dummy/criterion_chest_lateral_vc` — Chest Lateral VC

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Lateral_VC` | — | 1 (from limits) | — |

Limits for `?1VCCR00????VEY?`, `?1VCCRLE????VEY?`, `?1VCCRRI????VEY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -1 | False | red | upper | m/s | - |
| Pass | -1 | True | green | lower | m/s | - |
| Pass | 1 | True | green | upper | m/s | - |
| Fail | 1 | False | red | lower | m/s | - |

## `criterion_dummy/criterion_pubic_symphysis_force` — Pubic Symphysis Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Pubic_Symphysis_Force` | — | 1 (from limits) | — |

Limits for `?1PUBC0000??FOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -3.36 | False | red | upper | kN | - |
| Pass | -3.36 | True | green | lower | kN | - |
| Pass | 3.36 | True | green | upper | kN | - |
| Fail | 3.36 | False | red | lower | kN | - |

## `criterion_dummy/criterion_abdomen_force` — Abdomen Peak Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Abdomen_Force` | — | 1 (from limits) | — |

Limits for `?1ABDO??????FOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -2.5 | False | red | upper | kN | - |
| Pass | -2.5 | True | green | lower | kN | - |
