# UN_Frontal_56kmh_ODB_R94

| property | value |
| --- | --- |
| name | UN-R94 \| Frontal-Impact against ODB with 40 % Overlap at 56 km/h |
| protocol | 2022 |
| protocols | 2022 |
| overall criterion | `Overall` |
| available_pages | Cover, Rating, Driver Result Values Chart, Driver Values Table, Driver Head Acceleration, Driver Neck Load, Driver Chest Deflection, Driver Femur Axial Force, Driver Knee Slider Compression, Driver Tibia Compression, Driver Tibia Index, Passenger Result Values Chart, Passenger Values Table, Passenger Head Acceleration, Passenger Neck Load, Passenger Chest Deflection, Passenger Femur Axial Force, Passenger Knee Slider Compression, Passenger Tibia Compression, Passenger Tibia Index |
| selected_pages | Cover, Rating, Driver Result Values Chart, Driver Values Table, Driver Head Acceleration, Driver Neck Load, Driver Chest Deflection, Driver Femur Axial Force, Driver Knee Slider Compression, Driver Tibia Compression, Driver Tibia Index, Passenger Result Values Chart, Passenger Values Table, Passenger Head Acceleration, Passenger Neck Load, Passenger Chest Deflection, Passenger Femur Axial Force, Passenger Knee Slider Compression, Passenger Tibia Compression, Passenger Tibia Index |

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
| Pass | x=0:3.3, 0.01:3.299885714, 0.05:3.299428571, 0.1:3.298857143 | True | green | upper | kN | - |
| Fail | x=0:3.3, 0.01:3.299885714, 0.05:3.299428571, 0.1:3.298857143 | False | red | lower | kN | - |

## `criterion_driver/criterion_neck_fx_shear` — Neck Fx shear

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Fx_shear` | — | 1 (from limits) | — |

Limits for `?1NECKUP00??FOX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | x=0:-3.1, 0.01:-3.09936, 0.05:-3.0968, 0.1:-3.0936 | False | red | upper | kN | - |
| Pass | x=0:-3.1, 0.01:-3.09936, 0.05:-3.0968, 0.1:-3.0936 | True | green | lower | kN | - |
| Pass | x=0:3.1, 0.01:3.09936, 0.05:3.0968, 0.1:3.0936 | True | green | upper | kN | - |
| Fail | x=0:3.1, 0.01:3.09936, 0.05:3.0968, 0.1:3.0936 | False | red | lower | kN | - |

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
| Fail | x=0:-9.07, 0.01:-9.06851, 0.05:-9.06255, 0.1:-9.0551 | False | red | upper | kN | - |
| Pass | x=0:-9.07, 0.01:-9.06851, 0.05:-9.06255, 0.1:-9.0551 | True | green | lower | kN | - |

## `criterion_driver/criterion_tibia_compression` — Tibia Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Tibia_Compression` | — | 1 (from limits) | — |

Limits for `?1TIBI??????FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -8 | False | red | upper | kN | - |
| Pass | -8 | True | green | lower | kN | - |

## `criterion_driver/criterion_tibia_index` — Tibia Index

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Tibia_Index` | — | 1 (from limits) | — |

Limits for `?1TIIN??00??000?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 1.3 | True | green | upper | 1 | - |
| Fail | 1.3 | False | red | lower | 1 | - |

## `criterion_driver/criterion_knee_slider_compression` — Knee Slider Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Knee_Slider_Compression` | — | 1 (from limits) | — |

Limits for `?1KNSL??00??DSX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -15 | False | red | upper | mm | - |
| Pass | -15 | True | green | lower | mm | - |

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
| Pass | x=0:3.3, 0.01:3.299885714, 0.05:3.299428571, 0.1:3.298857143 | True | green | upper | kN | - |
| Fail | x=0:3.3, 0.01:3.299885714, 0.05:3.299428571, 0.1:3.298857143 | False | red | lower | kN | - |

## `criterion_passenger/criterion_neck_fx_shear` — Neck Fx shear

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Fx_shear` | — | 1 (from limits) | — |

Limits for `?3NECKUP00??FOX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | x=0:-3.1, 0.01:-3.09936, 0.05:-3.0968, 0.1:-3.0936 | False | red | upper | kN | - |
| Pass | x=0:-3.1, 0.01:-3.09936, 0.05:-3.0968, 0.1:-3.0936 | True | green | lower | kN | - |
| Pass | x=0:3.1, 0.01:3.09936, 0.05:3.0968, 0.1:3.0936 | True | green | upper | kN | - |
| Fail | x=0:3.1, 0.01:3.09936, 0.05:3.0968, 0.1:3.0936 | False | red | lower | kN | - |

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
| Fail | -42 | False | red | upper | mm | - |
| Pass | -42 | True | green | lower | mm | - |

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
| Fail | x=0:-9.07, 0.01:-9.06851, 0.05:-9.06255, 0.1:-9.0551 | False | red | upper | kN | - |
| Pass | x=0:-9.07, 0.01:-9.06851, 0.05:-9.06255, 0.1:-9.0551 | True | green | lower | kN | - |

## `criterion_passenger/criterion_tibia_compression` — Tibia Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Tibia_Compression` | — | 1 (from limits) | — |

Limits for `?3TIBI??????FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -8 | False | red | upper | kN | - |
| Pass | -8 | True | green | lower | kN | - |

## `criterion_passenger/criterion_tibia_index` — Tibia Index

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Tibia_Index` | — | 1 (from limits) | — |

Limits for `?3TIIN??00??000?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 1.3 | True | green | upper | 1 | - |
| Fail | 1.3 | False | red | lower | 1 | - |

## `criterion_passenger/criterion_knee_slider_compression` — Knee Slider Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Knee_Slider_Compression` | — | 1 (from limits) | — |

Limits for `?3KNSL??00??DSX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Fail | -15 | False | red | upper | mm | - |
| Pass | -15 | True | green | lower | mm | - |
