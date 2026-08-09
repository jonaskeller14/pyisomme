# FMVSS_208

| property | value |
| --- | --- |
| name | FMVSS 208 \| Adult Frontal Rigid-Barrier Occupant Protection |
| protocol | 2022-10-14 |
| protocols | 2022-10-14 |
| overall criterion | `Overall` |
| available_pages | Page_Cover, Page_Overall_Compliance, Page_Driver_Compliance, Page_Driver_Result_Values_Chart, Page_Driver_Values_Table, Page_Driver_Head_Acceleration, Page_Driver_Neck_Load, Page_Driver_Nij, Page_Driver_Chest, Page_Driver_Femur_Axial_Force, Page_Passenger_Compliance, Page_Passenger_Result_Values_Chart, Page_Passenger_Values_Table, Page_Passenger_Head_Acceleration, Page_Passenger_Neck_Load, Page_Passenger_Nij, Page_Passenger_Chest, Page_Passenger_Femur_Axial_Force |
| selected_pages | Page_Cover, Page_Overall_Compliance, Page_Driver_Compliance, Page_Driver_Result_Values_Chart, Page_Driver_Values_Table, Page_Driver_Head_Acceleration, Page_Driver_Neck_Load, Page_Driver_Nij, Page_Driver_Chest, Page_Driver_Femur_Axial_Force, Page_Passenger_Compliance, Page_Passenger_Result_Values_Chart, Page_Passenger_Values_Table, Page_Passenger_Head_Acceleration, Page_Passenger_Neck_Load, Page_Passenger_Nij, Page_Passenger_Chest, Page_Passenger_Femur_Axial_Force |

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

Limits for `?1HICR0015HF00R?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 700 | True | green | upper | 1 | - |
| Fail | 700 | False | red | lower | 1 | - |

## `criterion_driver/criterion_chest_a3ms` — Chest a3ms

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_a3ms` | S6.3; S15.3.3 | 1 (from limits) | — |

Limits for `?1CHST003CHFACR?`, `?1CHST????HFACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 60 | True | green | upper | g0 | - |
| Fail | 60 | False | red | lower | g0 | - |

## `criterion_driver/criterion_chest_deflection` — Chest Deflection

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Deflection` | S6.4(b); S15.3.4 | 1 (from limits) | — |

Limits for `?1CHST000[03]HFDSX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -52 | False | red | upper | mm | - |
| Pass | -52 | True | green | lower | mm | - |

## `criterion_driver/criterion_nij` — Nij

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Nij` | S6.6(a); S15.3.6(a) | 1 (from limits) | — |

Limits for `?1NIJCIP00HF00Y?`, `?1NIJCIPCFHF00Y?`, `?1NIJCIPCEHF00Y?`, `?1NIJCIPTFHF00Y?`, `?1NIJCIPTEHF00Y?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 1 | True | green | upper | 1 | - |
| Fail | 1 | False | red | lower | 1 | - |

## `criterion_driver/criterion_neck_tension` — Neck Tension Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Tension` | S6.6(b); S15.3.6(b) | 1 (from limits) | — |

Limits for `?1NECKUP00HFFOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 2620 | True | green | upper | N | - |
| Fail | 2620 | False | red | lower | N | - |

## `criterion_driver/criterion_neck_compression` — Neck Compression Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Compression` | S6.6(c); S15.3.6(c) | 1 (from limits) | — |

Limits for `?1NECKUP00HFFOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -2520 | False | red | upper | N | - |
| Pass | -2520 | True | green | lower | N | - |

## `criterion_driver/criterion_femur_axial_force` — Femur Axial Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Axial_Force` | S6.5; S15.3.5 | — | — |

## `criterion_driver/criterion_femur_axial_force/criterion_left` — Left Femur Axial Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Left` | S6.5; S15.3.5 (inherited) | 1 (from limits) | — |

Limits for `?1FEMRLE00HFFOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -6805 | False | red | upper | N | - |
| Pass | -6805 | True | green | lower | N | - |

## `criterion_driver/criterion_femur_axial_force/criterion_right` — Right Femur Axial Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Right` | S6.5; S15.3.5 (inherited) | 1 (from limits) | — |

Limits for `?1FEMRRI00HFFOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -6805 | False | red | upper | N | - |
| Pass | -6805 | True | green | lower | N | - |

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

Limits for `?3HICR0015HF00R?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 700 | True | green | upper | 1 | - |
| Fail | 700 | False | red | lower | 1 | - |

## `criterion_passenger/criterion_chest_a3ms` — Chest a3ms

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_a3ms` | S6.3; S15.3.3 | 1 (from limits) | — |

Limits for `?3CHST003CHFACR?`, `?3CHST????HFACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 60 | True | green | upper | g0 | - |
| Fail | 60 | False | red | lower | g0 | - |

## `criterion_passenger/criterion_chest_deflection` — Chest Deflection

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Deflection` | S6.4(b); S15.3.4 | 1 (from limits) | — |

Limits for `?3CHST000[03]HFDSX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -52 | False | red | upper | mm | - |
| Pass | -52 | True | green | lower | mm | - |

## `criterion_passenger/criterion_nij` — Nij

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Nij` | S6.6(a); S15.3.6(a) | 1 (from limits) | — |

Limits for `?3NIJCIP00HF00Y?`, `?3NIJCIPCFHF00Y?`, `?3NIJCIPCEHF00Y?`, `?3NIJCIPTFHF00Y?`, `?3NIJCIPTEHF00Y?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 1 | True | green | upper | 1 | - |
| Fail | 1 | False | red | lower | 1 | - |

## `criterion_passenger/criterion_neck_tension` — Neck Tension Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Tension` | S6.6(b); S15.3.6(b) | 1 (from limits) | — |

Limits for `?3NECKUP00HFFOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 2620 | True | green | upper | N | - |
| Fail | 2620 | False | red | lower | N | - |

## `criterion_passenger/criterion_neck_compression` — Neck Compression Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Compression` | S6.6(c); S15.3.6(c) | 1 (from limits) | — |

Limits for `?3NECKUP00HFFOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -2520 | False | red | upper | N | - |
| Pass | -2520 | True | green | lower | N | - |

## `criterion_passenger/criterion_femur_axial_force` — Femur Axial Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Axial_Force` | S6.5; S15.3.5 | — | — |

## `criterion_passenger/criterion_femur_axial_force/criterion_left` — Left Femur Axial Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Left` | S6.5; S15.3.5 (inherited) | 1 (from limits) | — |

Limits for `?3FEMRLE00HFFOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -6805 | False | red | upper | N | - |
| Pass | -6805 | True | green | lower | N | - |

## `criterion_passenger/criterion_femur_axial_force/criterion_right` — Right Femur Axial Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Right` | S6.5; S15.3.5 (inherited) | 1 (from limits) | — |

Limits for `?3FEMRRI00HFFOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -6805 | False | red | upper | N | - |
| Pass | -6805 | True | green | lower | N | - |
