# UN_Frontal_50kmh_R137

| property | value |
| --- | --- |
| name | UN-R137 \| Frontal-Impact against Rigid Wall with 100 % Overlap at 50 km/h |
| protocol | 2023 |
| protocols | 2016, 2023 |
| overall criterion | `Overall` |
| available_pages | Cover, Rating, Driver Result Values Chart, Driver Values Table, Driver Head Acceleration, Driver Neck Load, Driver Chest Deflection, Driver Femur Axial Force, Passenger Result Values Chart, Passenger Values Table, Passenger Head Acceleration, Passenger Neck Load, Passenger Chest Deflection, Passenger Femur Axial Force |
| selected_pages | Cover, Rating, Driver Result Values Chart, Driver Values Table, Driver Head Acceleration, Driver Neck Load, Driver Chest Deflection, Driver Femur Axial Force, Passenger Result Values Chart, Passenger Values Table, Passenger Head Acceleration, Passenger Neck Load, Passenger Chest Deflection, Passenger Femur Axial Force |

## `Overall` — Overall

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Overall` | — | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| p_driver | str | '1' | — | test report | Channel-code position of the driver. Defaults to the 'Driver position object 1' test-info field when the test carries it. |
| p_passenger | str | '3' | — | test report | Channel-code position of the front passenger. Derived from p_driver ('1' for a right-hand-drive test) unless set explicitly. |

## `criterion_driver` — Driver

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Driver` | — | — | — |

## `criterion_driver/criterion_hpc36` — Head Performance Criterion (HPC 36)

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HPC36` | — | 1 (from limits) | — |

Limits for `?1HICR0036??00RX`, `?1HICRCG36??00RX`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 1000 | True | green | upper | 1 | - |
| Fail | 1000 | False | red | lower | 1 | - |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| head_contact | bool | True | — | video | Was head contact observed? Without it HPC 36 is not assessed and passes. |

## `criterion_driver/criterion_head_a3ms` — Head a3ms

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_a3ms` | — | 1 (from limits) | — |

Limits for `?1HEAD003C??ACR?`, `?1HEADCG3C??ACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 80 | True | green | upper | g0 | - |
| Fail | 80 | False | red | lower | g0 | - |

## `criterion_driver/criterion_neck_fz_tension` — Neck Fz tension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Fz_tension` | — | 1 (from limits) | — |

Limits for `?1NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 3.3 | True | green | upper | kN | - |
| Fail | 3.3 | False | red | lower | kN | - |

## `criterion_driver/criterion_neck_fx_shear` — Neck Fx shear

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Fx_shear` | — | 1 (from limits) | — |

Limits for `?1NECKUP00??FOX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | 3.1 | False | red | lower | kN | - |
| Pass | 3.1 | True | green | upper | kN | - |
| Pass | -3.1 | True | green | lower | kN | - |
| Fail | -3.1 | False | red | upper | kN | - |

## `criterion_driver/criterion_neck_my_extension` — Neck My extension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_My_extension` | — | 1 (from limits) | — |

Limits for `?1NECKUP00??MOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | -57 | True | green | lower | Nm | - |
| Fail | -57 | False | red | upper | Nm | - |

## `criterion_driver/criterion_chest_deflection` — Chest Deflection

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Deflection` | — | 1 (from limits) | — |

Limits for `?1CHST000[03]??DSX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -42 | False | red | upper | mm | - |
| Pass | -42 | True | green | lower | mm | - |

## `criterion_driver/criterion_chest_vc` — Chest VC

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_VC` | — | 1 (from limits) | — |

Limits for `?1VCCR000[03]??VEX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -1 | False | red | upper | m/s | - |
| Pass | -1 | True | green | lower | m/s | - |
| Pass | 1 | True | green | upper | m/s | - |
| Fail | 1 | False | red | lower | m/s | - |

## `criterion_driver/criterion_femur_compression` — Femur Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Compression` | — | 1 (from limits) | — |

Limits for `?1FEMR??00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -9.07 | False | red | upper | kN | - |
| Pass | -9.07 | True | green | lower | kN | - |

## `criterion_passenger` — Passenger

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Passenger` | — | — | — |

## `criterion_passenger/criterion_hpc36` — Head Performance Criterion (HPC 36)

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HPC36` | — | 1 (from limits) | — |

Limits for `?3HICR0036??00RX`, `?3HICRCG36??00RX`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 1000 | True | green | upper | 1 | - |
| Fail | 1000 | False | red | lower | 1 | - |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| head_contact | bool | True | — | video | Was head contact observed? Without it HPC 36 is not assessed and passes. |

## `criterion_passenger/criterion_head_a3ms` — Head a3ms

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_a3ms` | — | 1 (from limits) | — |

Limits for `?3HEAD003C??ACR?`, `?3HEADCG3C??ACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 80 | True | green | upper | g0 | - |
| Fail | 80 | False | red | lower | g0 | - |

## `criterion_passenger/criterion_neck_fz_tension` — Neck Fz tension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Fz_tension` | — | 1 (from limits) | — |

Limits for `?3NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 2.9 | True | green | upper | kN | - |
| Fail | 2.9 | False | red | lower | kN | - |

## `criterion_passenger/criterion_neck_fx_shear` — Neck Fx shear

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Fx_shear` | — | 1 (from limits) | — |

Limits for `?3NECKUP00??FOX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | 2.9 | False | red | lower | kN | - |
| Pass | 2.9 | True | green | upper | kN | - |
| Pass | -2.9 | True | green | lower | kN | - |
| Fail | -2.9 | False | red | upper | kN | - |

## `criterion_passenger/criterion_neck_my_extension` — Neck My extension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_My_extension` | — | 1 (from limits) | — |

Limits for `?3NECKUP00??MOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | -57 | True | green | lower | Nm | - |
| Fail | -57 | False | red | upper | Nm | - |

## `criterion_passenger/criterion_chest_deflection` — Chest Deflection

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Deflection` | — | 1 (from limits) | — |

Limits for `?3CHST000[03]??DSX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -34 | False | red | upper | mm | - |
| Pass | -34 | True | green | lower | mm | - |

## `criterion_passenger/criterion_chest_vc` — Chest VC

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_VC` | — | 1 (from limits) | — |

Limits for `?3VCCR000[03]??VEX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -1 | False | red | upper | m/s | - |
| Pass | -1 | True | green | lower | m/s | - |
| Pass | 1 | True | green | upper | m/s | - |
| Fail | 1 | False | red | lower | m/s | - |

## `criterion_passenger/criterion_femur_compression` — Femur Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Compression` | — | 1 (from limits) | — |

Limits for `?3FEMR??00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -7 | False | red | upper | kN | - |
| Pass | -7 | True | green | lower | kN | - |
