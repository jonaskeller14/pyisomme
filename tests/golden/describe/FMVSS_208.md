# FMVSS_208

| property | value |
| --- | --- |
| name | FMVSS 208 \| Adult Frontal Rigid-Barrier Occupant Protection |
| protocol | 2022-10-14 |
| protocols | 2022-10-14 |
| overall criterion | `Overall` |
| available_pages | Cover, Overall Compliance, Driver Compliance, Driver Result Values Chart, Driver Values Table, Driver Head Acceleration, Driver HIC15, Driver Neck Load, Driver Neck NIJ, Driver Chest, Driver Femur Axial Force, Front Passenger Compliance, Front Passenger Result Values Chart, Front Passenger Values Table, Front Passenger Head Acceleration, Front Passenger HIC15, Front Passenger Neck Load, Front Passenger Neck NIJ, Front Passenger Chest, Front Passenger Femur Axial Force |
| selected_pages | Cover, Overall Compliance, Driver Compliance, Driver Result Values Chart, Driver Values Table, Driver Head Acceleration, Driver HIC15, Driver Neck Load, Driver Neck NIJ, Driver Chest, Driver Femur Axial Force, Front Passenger Compliance, Front Passenger Result Values Chart, Front Passenger Values Table, Front Passenger Head Acceleration, Front Passenger HIC15, Front Passenger Neck Load, Front Passenger Neck NIJ, Front Passenger Chest, Front Passenger Femur Axial Force |

## `Overall` — Overall

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Overall` | S14.4-S15.3 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| p_driver | str | '1' | — | test report | Channel-code position of the driver. Defaults to the 'Driver position object 1' test-info field when the test carries it. |
| p_passenger | str | '3' | — | test report | Channel-code position of the front outboard passenger. Derived from p_driver ('1' for a right-hand-drive test) unless set explicitly. |

## `criterion_driver` — Driver

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Occupant` | S14.4-S15.3 (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| dummy_type | str | 'HF' | — | ISO-MME channel codes | ISO-MME dummy identifier for this occupant: 'H3' for a Hybrid III 50th-percentile male or 'HF' for a Hybrid III 5th-percentile female. Derived from channels at the occupant position; conservatively defaults to 'HF' when the channels are absent or ambiguous. |

## `criterion_driver/criterion_containment` — Dummy Containment

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Containment` | S6.1; S15.3.1 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| contained | bool | False | — | video / post-test inspection | Were all portions of the dummy contained within the outer surfaces of the passenger compartment? Defaults to False until positively confirmed. |

## `criterion_driver/criterion_hic15` — HIC 15

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HIC15` | S6.2(b); S15.3.2 | 1 (from limits) | — |

Limits for `?1HICR0015H300R?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 700 | True | green | upper | 1 | - |
| Fail | 700 | False | red | lower | 1 | - |

## `criterion_driver/criterion_chest_a3ms` — Chest a3ms

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_a3ms` | S6.3; S15.3.3 | 1 (from limits) | — |

Limits for `?1CHST003CH3ACR?`, `?1CHST????H3ACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 60 | True | green | upper | g0 | - |
| Fail | 60 | False | red | lower | g0 | - |

## `criterion_driver/criterion_chest_deflection` — Chest Deflection

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Deflection` | S6.4(b); S15.3.4 | 1 (from limits) | — |

Limits for `?1CHST000[03]H3DSX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -63 | False | red | upper | mm | - |
| Pass | -63 | True | green | lower | mm | - |

## `criterion_driver/criterion_nij` — Nij

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Nij` | S6.6(a); S15.3.6(a) | 1 (from limits) | — |

Limits for `?1NIJCIP00H300Y?`, `?1NIJCIPCFH300Y?`, `?1NIJCIPCEH300Y?`, `?1NIJCIPTFH300Y?`, `?1NIJCIPTEH300Y?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 1 | True | green | upper | 1 | - |
| Fail | 1 | False | red | lower | 1 | - |

## `criterion_driver/criterion_neck_tension` — Neck Tension Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Tension` | S6.6(b); S15.3.6(b) | 1 (from limits) | — |

Limits for `?1NECKUP00H3FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 4170 | True | green | upper | N | - |
| Fail | 4170 | False | red | lower | N | - |

## `criterion_driver/criterion_neck_compression` — Neck Compression Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Compression` | S6.6(c); S15.3.6(c) | 1 (from limits) | — |

Limits for `?1NECKUP00H3FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -4000 | False | red | upper | N | - |
| Pass | -4000 | True | green | lower | N | - |

## `criterion_driver/criterion_femur_axial_force` — Femur Axial Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Axial_Force` | S6.5; S15.3.5 | — | — |

## `criterion_driver/criterion_femur_axial_force/criterion_left` — Left Femur Axial Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Left` | S6.5; S15.3.5 (inherited) | 1 (from limits) | — |

Limits for `?1FEMRLE00H3FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -10008 | False | red | upper | N | - |
| Pass | -10008 | True | green | lower | N | - |

## `criterion_driver/criterion_femur_axial_force/criterion_right` — Right Femur Axial Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Right` | S6.5; S15.3.5 (inherited) | 1 (from limits) | — |

Limits for `?1FEMRRI00H3FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -10008 | False | red | upper | N | - |
| Pass | -10008 | True | green | lower | N | - |

## `criterion_passenger` — Front Passenger

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Occupant` | S14.4-S15.3 (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| dummy_type | str | 'HF' | — | ISO-MME channel codes | ISO-MME dummy identifier for this occupant: 'H3' for a Hybrid III 50th-percentile male or 'HF' for a Hybrid III 5th-percentile female. Derived from channels at the occupant position; conservatively defaults to 'HF' when the channels are absent or ambiguous. |

## `criterion_passenger/criterion_containment` — Dummy Containment

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Containment` | S6.1; S15.3.1 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| contained | bool | False | — | video / post-test inspection | Were all portions of the dummy contained within the outer surfaces of the passenger compartment? Defaults to False until positively confirmed. |

## `criterion_passenger/criterion_hic15` — HIC 15

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HIC15` | S6.2(b); S15.3.2 | 1 (from limits) | — |

Limits for `?3HICR0015H300R?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 700 | True | green | upper | 1 | - |
| Fail | 700 | False | red | lower | 1 | - |

## `criterion_passenger/criterion_chest_a3ms` — Chest a3ms

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_a3ms` | S6.3; S15.3.3 | 1 (from limits) | — |

Limits for `?3CHST003CH3ACR?`, `?3CHST????H3ACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 60 | True | green | upper | g0 | - |
| Fail | 60 | False | red | lower | g0 | - |

## `criterion_passenger/criterion_chest_deflection` — Chest Deflection

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Deflection` | S6.4(b); S15.3.4 | 1 (from limits) | — |

Limits for `?3CHST000[03]H3DSX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -63 | False | red | upper | mm | - |
| Pass | -63 | True | green | lower | mm | - |

## `criterion_passenger/criterion_nij` — Nij

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Nij` | S6.6(a); S15.3.6(a) | 1 (from limits) | — |

Limits for `?3NIJCIP00H300Y?`, `?3NIJCIPCFH300Y?`, `?3NIJCIPCEH300Y?`, `?3NIJCIPTFH300Y?`, `?3NIJCIPTEH300Y?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 1 | True | green | upper | 1 | - |
| Fail | 1 | False | red | lower | 1 | - |

## `criterion_passenger/criterion_neck_tension` — Neck Tension Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Tension` | S6.6(b); S15.3.6(b) | 1 (from limits) | — |

Limits for `?3NECKUP00H3FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 4170 | True | green | upper | N | - |
| Fail | 4170 | False | red | lower | N | - |

## `criterion_passenger/criterion_neck_compression` — Neck Compression Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Compression` | S6.6(c); S15.3.6(c) | 1 (from limits) | — |

Limits for `?3NECKUP00H3FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -4000 | False | red | upper | N | - |
| Pass | -4000 | True | green | lower | N | - |

## `criterion_passenger/criterion_femur_axial_force` — Femur Axial Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Axial_Force` | S6.5; S15.3.5 | — | — |

## `criterion_passenger/criterion_femur_axial_force/criterion_left` — Left Femur Axial Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Left` | S6.5; S15.3.5 (inherited) | 1 (from limits) | — |

Limits for `?3FEMRLE00H3FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -10008 | False | red | upper | N | - |
| Pass | -10008 | True | green | lower | N | - |

## `criterion_passenger/criterion_femur_axial_force/criterion_right` — Right Femur Axial Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Right` | S6.5; S15.3.5 (inherited) | 1 (from limits) | — |

Limits for `?3FEMRRI00H3FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -10008 | False | red | upper | N | - |
| Pass | -10008 | True | green | lower | N | - |
