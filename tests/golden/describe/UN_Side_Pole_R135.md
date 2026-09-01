# UN_Side_Pole_R135

| property | value |
| --- | --- |
| name | UN-R135 \| Pole Side Impact at 32 km/h |
| protocol | 2016 |
| protocols | 2016 |
| overall criterion | `Overall` |
| available_pages | Cover, Values Chart, Values Table, Head Acceleration, HIC36, Shoulder Lateral Force, Chest Absolute Compression, Abdomen Resultant Compression, Spine T12 Acceleration, Pubic Symphysis Force |
| selected_pages | Cover, Values Chart, Values Table, Head Acceleration, HIC36, Shoulder Lateral Force, Chest Absolute Compression, Abdomen Resultant Compression, Spine T12 Acceleration, Pubic Symphysis Force |

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

## `criterion_dummy/criterion_hic_36` — HIC 36

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HIC_36` | — | 1 (from limits) | — |

Limits for `?1HICR0036??00RX`, `?1HICRCG36??00RX`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 1000 | True | green | upper | 1 | - |
| Fail | 1000 | False | red | lower | 1 | - |

## `criterion_dummy/criterion_shoulder_lateral_force` — Shoulder Lateral Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Shoulder_Lateral_Force` | — | 1 (from limits) | — |

Limits for `?1SHLD0000??FOY?`, `?1SHLDLE00??FOY?`, `?1SHLDRI00??FOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -3 | False | red | upper | kN | - |
| Pass | -3 | True | green | lower | kN | - |
| Pass | 3 | True | green | upper | kN | - |
| Fail | 3 | False | red | lower | kN | - |

## `criterion_dummy/criterion_chest_resultant_compression` — Chest Resultant Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Resultant_Compression` | — | 1 (from limits) | — |

Limits for `?1TRRI??0[0123]??DSR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -55 | False | red | upper | mm | - |
| Pass | -55 | True | green | lower | mm | - |

## `criterion_dummy/criterion_abdomen_resultant_compression` — Abdomen Resultant Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Abdomen_Resultant_Compression` | — | 1 (from limits) | — |

Limits for `?1ABRI??0[012]??DSR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -65 | False | red | upper | mm | - |
| Pass | -65 | True | green | lower | mm | - |

## `criterion_dummy/criterion_spine_t12_a3ms` — Spine T12 Acceleration a3ms

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Spine_T12_a3ms` | — | 1 (from limits) | — |

Limits for `11THSP123C??ACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 75 | True | green | upper | g0 | - |
| Fail | 75 | False | red | lower | g0 | - |

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
