# FMVSS_214

| property | value |
| --- | --- |
| name | FMVSS 214 \| Side Impact Protection |
| protocol | 2026-07-06 |
| protocols | 2026-07-06 |
| overall criterion | `Overall` |
| available_pages | Cover, Report Status, Manual Inputs, Overall Compliance, Front Occupant Values Chart, Front Occupant Values Table, Front Occupant HIC36, Front Occupant Head Acceleration, Front Occupant Chest Deflection, Front Occupant Abdomen Force, Front Occupant Lower Spine Acceleration, Front Occupant Pelvis Force, Rear Occupant Values Chart, Rear Occupant Values Table, Rear Occupant HIC36, Rear Occupant Head Acceleration, Rear Occupant Lower Spine Acceleration, Rear Occupant Pelvis Force |
| selected_pages | Cover, Report Status, Manual Inputs, Overall Compliance, Front Occupant Values Chart, Front Occupant Values Table, Front Occupant HIC36, Front Occupant Head Acceleration, Front Occupant Chest Deflection, Front Occupant Abdomen Force, Front Occupant Lower Spine Acceleration, Front Occupant Pelvis Force, Rear Occupant Values Chart, Rear Occupant Values Table, Rear Occupant HIC36, Rear Occupant Head Acceleration, Rear Occupant Lower Spine Acceleration, Rear Occupant Pelvis Force |

## `Overall` — Overall

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Overall` | S7.2-S7.3; S9.2 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| impact_type | str | 'pole' | — | test report / ISO-MME channel codes | 'barrier' for the moving deformable barrier test or 'pole' for the vehicle-to-pole test. Derived as barrier when a rear SID-IIs position is detected; otherwise pole. |
| p_front | str | '1' | — | test report / ISO-MME channel codes | Channel-code position of the struck-side front occupant. Derived from ER/E2/S2 channels at a front outboard position when available. |
| p_rear | str | '6' | — | test report / ISO-MME channel codes | Channel-code position of the struck-side rear occupant in a barrier test. Derived from rear S2 channels or from the side of p_front. |

## `criterion_front_occupant` — Front Occupant

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Occupant` | S7.2-S7.3; S9.2 (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| dummy_type | str | 'ER' | — | ISO-MME channel codes | 'ER' for an ES-2/ES-2re occupant or 'S2' for a SID-IIs occupant. E2 and ER channel identifiers are both mapped to the ES-2re requirement family. |

## `criterion_front_occupant/criterion_hic36` — HIC 36

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HIC36` | S7.2.5(a), S7.2.6(a); S9.2.1(a), S9.2.2(a) | 1 (from limits) | — |

Limits for `?1HICR0036??00RX`, `?1HICRCG36??00RX`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 1000 | True | green | upper | 1 | - |
| Fail | 1000 | False | red | lower | 1 | - |

## `criterion_front_occupant/criterion_es2re_rib_deflection` — Maximum Rib Deflection

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_ES2re_Rib_Deflection` | S7.2.5(b); S9.2.1(b) | 1 (from limits) | — |

Limits for `?1RIBS??????DSY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 44 | True | green | upper | mm | - |
| Fail | 44 | False | red | lower | mm | - |

## `criterion_front_occupant/criterion_es2re_abdominal_force` — Sum of Abdominal Forces

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_ES2re_Abdominal_Force` | S7.2.5(c)(1); S9.2.1(c)(1) | 1 (from limits) | — |

Limits for `?1ABDO??????FOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 2500 | True | green | upper | N | - |
| Fail | 2500 | False | red | lower | N | - |

## `criterion_front_occupant/criterion_es2re_pubic_symphysis_force` — Pubic Symphysis Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_ES2re_Pubic_Symphysis_Force` | S7.2.5(c)(2); S9.2.1(c)(2) | 1 (from limits) | — |

Limits for `?1PUBC0000??FOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 6000 | True | green | upper | N | - |
| Fail | 6000 | False | red | lower | N | - |

## `criterion_front_occupant/criterion_sid_iis_lower_spine_acceleration` — Lower Spine Resultant Acceleration

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_SID_IIs_Lower_Spine_Acceleration` | S7.2.6(b); S9.2.2(b) | 1 (from limits) | — |

Limits for `?1SPINLO00??ACR?`, `?1LUSP0000??ACR?`, `?1SPIN0000??ACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 82 | True | green | upper | g0 | - |
| Fail | 82 | False | red | lower | g0 | - |

## `criterion_front_occupant/criterion_sid_iis_pelvic_force` — Sum of Acetabular and Iliac Pelvic Forces

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_SID_IIs_Pelvic_Force` | S7.2.6(c); S9.2.2(c) | 1 (from limits) | — |

Limits for `?1ACTB??????FOY?`, `?1ILUM??????FOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 5525 | True | green | upper | N | - |
| Fail | 5525 | False | red | lower | N | - |

## `criterion_rear_occupant` — Rear Occupant

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Rear_Occupant` | S7.2-S7.3; S9.2 (inherited) | — | — |

## `criterion_rear_occupant/criterion_hic36` — HIC 36

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HIC36` | S7.2.5(a), S7.2.6(a); S9.2.1(a), S9.2.2(a) | 1 (from limits) | — |

Limits for `?6HICR0036??00RX`, `?6HICRCG36??00RX`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 1000 | True | green | upper | 1 | - |
| Fail | 1000 | False | red | lower | 1 | - |

## `criterion_rear_occupant/criterion_es2re_rib_deflection` — Maximum Rib Deflection

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_ES2re_Rib_Deflection` | S7.2.5(b); S9.2.1(b) | 1 (from limits) | — |

Limits for `?6RIBS??????DSY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 44 | True | green | upper | mm | - |
| Fail | 44 | False | red | lower | mm | - |

## `criterion_rear_occupant/criterion_es2re_abdominal_force` — Sum of Abdominal Forces

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_ES2re_Abdominal_Force` | S7.2.5(c)(1); S9.2.1(c)(1) | 1 (from limits) | — |

Limits for `?6ABDO??????FOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 2500 | True | green | upper | N | - |
| Fail | 2500 | False | red | lower | N | - |

## `criterion_rear_occupant/criterion_es2re_pubic_symphysis_force` — Pubic Symphysis Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_ES2re_Pubic_Symphysis_Force` | S7.2.5(c)(2); S9.2.1(c)(2) | 1 (from limits) | — |

Limits for `?6PUBC0000??FOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 6000 | True | green | upper | N | - |
| Fail | 6000 | False | red | lower | N | - |

## `criterion_rear_occupant/criterion_sid_iis_lower_spine_acceleration` — Lower Spine Resultant Acceleration

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_SID_IIs_Lower_Spine_Acceleration` | S7.2.6(b); S9.2.2(b) | 1 (from limits) | — |

Limits for `?6SPINLO00??ACR?`, `?6LUSP0000??ACR?`, `?6SPIN0000??ACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 82 | True | green | upper | g0 | - |
| Fail | 82 | False | red | lower | g0 | - |

## `criterion_rear_occupant/criterion_sid_iis_pelvic_force` — Sum of Acetabular and Iliac Pelvic Forces

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_SID_IIs_Pelvic_Force` | S7.2.6(c); S9.2.2(c) | 1 (from limits) | — |

Limits for `?6ACTB??????FOY?`, `?6ILUM??????FOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 5525 | True | green | upper | N | - |
| Fail | 5525 | False | red | lower | N | - |

## `criterion_door_integrity` — Door Integrity

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Door_Integrity` | S7.3; S9.2.3 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| latches_hinges_and_anchorages_remained_attached | bool | False | — | post-test inspection | No latch separated from its striker; no hinge component separated; and no latch or hinge system pulled out of its anchorage. |
| struck_door_remained_attached | bool | False | — | video / post-test inspection | The door struck by the barrier or pole did not separate totally. |
| unstruck_doors_remained_latched | bool | False | — | video / post-test inspection | Every unstruck door remained engaged in its latched position. |
