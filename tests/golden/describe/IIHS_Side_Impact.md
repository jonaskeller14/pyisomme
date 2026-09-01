# IIHS_Side_Impact

| property | value |
| --- | --- |
| name | IIHS \| Side Impact Crashworthiness |
| protocol | IV |
| protocols | IV |
| overall criterion | `Overall` |
| available_pages | Cover, Overall Rating, Driver Ratings, Driver Values Chart, Driver Values Table, Driver Head Acceleration, Driver HIC15, Driver Neck Axial Load, Driver Rib Deflection, Driver Rib Deflection Rate, Driver Viscous Criterion, Driver Pelvis Force, Rear Passenger Ratings, Rear Passenger Values Chart, Rear Passenger Values Table, Rear Passenger Head Acceleration, Rear Passenger HIC15, Rear Passenger Neck Axial Load, Rear Passenger Rib Deflection, Rear Passenger Rib Deflection Rate, Rear Passenger Viscous Criterion, Rear Passenger Pelvis Force |
| selected_pages | Cover, Overall Rating, Driver Ratings, Driver Values Chart, Driver Values Table, Driver Head Acceleration, Driver HIC15, Driver Neck Axial Load, Driver Rib Deflection, Driver Rib Deflection Rate, Driver Viscous Criterion, Driver Pelvis Force, Rear Passenger Ratings, Rear Passenger Values Chart, Rear Passenger Values Table, Rear Passenger Head Acceleration, Rear Passenger HIC15, Rear Passenger Neck Axial Load, Rear Passenger Rib Deflection, Rear Passenger Rib Deflection Rate, Rear Passenger Viscous Criterion, Rear Passenger Pelvis Force |

## `Overall` — Overall

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Overall` | Injury measures and rating boundaries / Tables 1 and 3 | — | sum |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| p_driver | str | '1' | — | test report | Channel-code position of the driver SID-IIs dummy. Defaults to the 'Driver position object 1' test-info field when available. |
| p_rear_passenger | str | '6' | — | test report | Channel-code position of the left-rear passenger SID-IIs dummy; derived from the driver side. |

## `criterion_driver` — Driver

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Occupant` | Injury measures and rating boundaries / Tables 1 and 3 (inherited) | — | sum |

## `criterion_driver/criterion_head_neck` — Head and neck

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_Neck` | Injury measures and rating boundaries / Tables 1 and 3 (inherited) | — | min |

## `criterion_driver/criterion_head_neck/criterion_hic_15` — HIC15

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HIC_15` | Injury measures and rating boundaries / Tables 1 and 3 (inherited) | 0 (from limits) | — |

Limits for `?1HICR0015??00RX`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 623 | 0 | green | upper | 1 | - |
| Acceptable | 779 | -2 | yellow | upper | 1 | - |
| Marginal | 935 | -10 | orange | upper | 1 | - |
| Poor | 935 | -35 | red | lower | 1 | - |

## `criterion_driver/criterion_head_neck/criterion_neck_tension` — Neck axial tension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Tension` | Injury measures and rating boundaries / Tables 1 and 3 (inherited) | 0 (from limits) | — |

Limits for `?1NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 2.1 | 0 | green | upper | kN | - |
| Acceptable | 2.5 | -2 | yellow | upper | kN | - |
| Marginal | 2.9 | -10 | orange | upper | kN | - |
| Poor | 2.9 | -35 | red | lower | kN | - |

## `criterion_driver/criterion_head_neck/criterion_neck_compression` — Neck axial compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Compression` | Injury measures and rating boundaries / Tables 1 and 3 (inherited) | 0 (from limits) | — |

Limits for `?1NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -2.5 | 0 | green | lower | kN | - |
| Acceptable | -2.5 | -2 | yellow | upper | kN | - |
| Marginal | -3 | -10 | orange | upper | kN | - |
| Poor | -3.5 | -35 | red | upper | kN | - |

## `criterion_driver/criterion_torso` — Torso

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Torso` | Injury measures and rating boundaries / Tables 1 and 3 (inherited) | — | min |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| shoulder_bottoming | bool | False | — | high-speed video and postcrash inspection | True when shoulder excursion exceeds 60 mm or the shoulder bottoms out. |

## `criterion_driver/criterion_torso/criterion_rib_deflection` — Average peak rib deflection

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Rib_Deflection` | Injury measures and rating boundaries / Tables 1 and 3 (inherited) | 0 (from limits) | — |

Limits for `?1TRRILE01??DSYC`, `?1TRRILE02??DSYC`, `?1TRRILE03??DSYC`, `?1ABRILE01??DSYC`, `?1ABRILE02??DSYC`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 28 | 0 | green | upper | mm | - |
| Acceptable | 38 | -2 | yellow | upper | mm | - |
| Marginal | 48 | -10 | orange | upper | mm | - |
| Poor | 48 | -35 | red | lower | mm | - |

## `criterion_driver/criterion_torso/criterion_rib_deflection_rate` — Rib deflection rate

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Rib_Deflection_Rate` | Injury measures and rating boundaries / Tables 1 and 3 (inherited) | 0 (from limits) | — |

Limits for `?1TRRILE01??VEY?`, `?1TRRILE02??VEY?`, `?1TRRILE03??VEY?`, `?1ABRILE01??VEY?`, `?1ABRILE02??VEY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 8.2 | 0 | green | upper | m/s | - |
| Acceptable | 9.8 | -2 | yellow | upper | m/s | - |
| Marginal | 11.5 | -10 | orange | upper | m/s | - |
| Poor | 11.5 | -35 | red | lower | m/s | - |

## `criterion_driver/criterion_torso/criterion_viscous_criterion` — Viscous criterion

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Viscous_Criterion` | Injury measures and rating boundaries / Tables 1 and 3 (inherited) | 0 (from limits) | — |

Limits for `?1VCCRLE01??VEY?`, `?1VCCRLE02??VEY?`, `?1VCCRLE03??VEY?`, `?1VCARLE01??VEY?`, `?1VCARLE02??VEY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 1 | 0 | green | upper | m/s | - |
| Acceptable | 1.2 | -2 | yellow | upper | m/s | - |
| Marginal | 1.4 | -10 | orange | upper | m/s | - |
| Poor | 1.4 | -35 | red | lower | m/s | - |

## `criterion_driver/criterion_pelvis` — Pelvis

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Pelvis` | Injury measures and rating boundaries / Tables 1 and 3 (inherited) | 0 (from limits) | — |

Limits for `?1ACTBLE00??FOY?`, `?1ILUMLE00??FOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 4 | 0 | green | upper | kN | - |
| Acceptable | 5 | -2 | yellow | upper | kN | - |
| Marginal | 6 | -6 | orange | upper | kN | - |
| Poor | 6 | -10 | red | lower | kN | - |

## `criterion_driver/criterion_head_protection` — Head protection

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_Protection` | Injury measures and rating boundaries / Tables 1 and 3 (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| direct_mdb_contact | bool | False | — | high-speed video and physical evidence | The head directly contacts the moving deformable barrier. |
| head_acceleration_over_70g | bool | False | — | head resultant acceleration | The resultant head acceleration exceeds 70 g during the relevant event. |
| head_contained | bool | True | — | high-speed video | The head remains contained and protected by the side head-protection system. |
| head_protection_system_equipped | bool | True | — | high-speed video and postcrash inspection | A side head-protection system is equipped for this seating position. |
| interior_contact | bool | False | — | high-speed video and physical evidence | The head contacts vehicle interior hard structure or bottoms out the airbag. |

## `criterion_rear_passenger` — Rear passenger

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Occupant` | Injury measures and rating boundaries / Tables 1 and 3 (inherited) | — | sum |

## `criterion_rear_passenger/criterion_head_neck` — Head and neck

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_Neck` | Injury measures and rating boundaries / Tables 1 and 3 (inherited) | — | min |

## `criterion_rear_passenger/criterion_head_neck/criterion_hic_15` — HIC15

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HIC_15` | Injury measures and rating boundaries / Tables 1 and 3 (inherited) | 0 (from limits) | — |

Limits for `?6HICR0015??00RX`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 623 | 0 | green | upper | 1 | - |
| Acceptable | 779 | -2 | yellow | upper | 1 | - |
| Marginal | 935 | -10 | orange | upper | 1 | - |
| Poor | 935 | -35 | red | lower | 1 | - |

## `criterion_rear_passenger/criterion_head_neck/criterion_neck_tension` — Neck axial tension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Tension` | Injury measures and rating boundaries / Tables 1 and 3 (inherited) | 0 (from limits) | — |

Limits for `?6NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 2.1 | 0 | green | upper | kN | - |
| Acceptable | 2.5 | -2 | yellow | upper | kN | - |
| Marginal | 2.9 | -10 | orange | upper | kN | - |
| Poor | 2.9 | -35 | red | lower | kN | - |

## `criterion_rear_passenger/criterion_head_neck/criterion_neck_compression` — Neck axial compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Compression` | Injury measures and rating boundaries / Tables 1 and 3 (inherited) | 0 (from limits) | — |

Limits for `?6NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -2.5 | 0 | green | lower | kN | - |
| Acceptable | -2.5 | -2 | yellow | upper | kN | - |
| Marginal | -3 | -10 | orange | upper | kN | - |
| Poor | -3.5 | -35 | red | upper | kN | - |

## `criterion_rear_passenger/criterion_torso` — Torso

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Torso` | Injury measures and rating boundaries / Tables 1 and 3 (inherited) | — | min |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| shoulder_bottoming | bool | False | — | high-speed video and postcrash inspection | True when shoulder excursion exceeds 60 mm or the shoulder bottoms out. |

## `criterion_rear_passenger/criterion_torso/criterion_rib_deflection` — Average peak rib deflection

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Rib_Deflection` | Injury measures and rating boundaries / Tables 1 and 3 (inherited) | 0 (from limits) | — |

Limits for `?6TRRILE01??DSYC`, `?6TRRILE02??DSYC`, `?6TRRILE03??DSYC`, `?6ABRILE01??DSYC`, `?6ABRILE02??DSYC`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 28 | 0 | green | upper | mm | - |
| Acceptable | 38 | -2 | yellow | upper | mm | - |
| Marginal | 48 | -10 | orange | upper | mm | - |
| Poor | 48 | -35 | red | lower | mm | - |

## `criterion_rear_passenger/criterion_torso/criterion_rib_deflection_rate` — Rib deflection rate

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Rib_Deflection_Rate` | Injury measures and rating boundaries / Tables 1 and 3 (inherited) | 0 (from limits) | — |

Limits for `?6TRRILE01??VEY?`, `?6TRRILE02??VEY?`, `?6TRRILE03??VEY?`, `?6ABRILE01??VEY?`, `?6ABRILE02??VEY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 8.2 | 0 | green | upper | m/s | - |
| Acceptable | 9.8 | -2 | yellow | upper | m/s | - |
| Marginal | 11.5 | -10 | orange | upper | m/s | - |
| Poor | 11.5 | -35 | red | lower | m/s | - |

## `criterion_rear_passenger/criterion_torso/criterion_viscous_criterion` — Viscous criterion

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Viscous_Criterion` | Injury measures and rating boundaries / Tables 1 and 3 (inherited) | 0 (from limits) | — |

Limits for `?6VCCRLE01??VEY?`, `?6VCCRLE02??VEY?`, `?6VCCRLE03??VEY?`, `?6VCARLE01??VEY?`, `?6VCARLE02??VEY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 1 | 0 | green | upper | m/s | - |
| Acceptable | 1.2 | -2 | yellow | upper | m/s | - |
| Marginal | 1.4 | -10 | orange | upper | m/s | - |
| Poor | 1.4 | -35 | red | lower | m/s | - |

## `criterion_rear_passenger/criterion_pelvis` — Pelvis

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Pelvis` | Injury measures and rating boundaries / Tables 1 and 3 (inherited) | 0 (from limits) | — |

Limits for `?6ACTBLE00??FOY?`, `?6ILUMLE00??FOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 4 | 0 | green | upper | kN | - |
| Acceptable | 5 | -2 | yellow | upper | kN | - |
| Marginal | 6 | -6 | orange | upper | kN | - |
| Poor | 6 | -10 | red | lower | kN | - |

## `criterion_rear_passenger/criterion_head_protection` — Head protection

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_Protection` | Injury measures and rating boundaries / Tables 1 and 3 (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| direct_mdb_contact | bool | False | — | high-speed video and physical evidence | The head directly contacts the moving deformable barrier. |
| head_acceleration_over_70g | bool | False | — | head resultant acceleration | The resultant head acceleration exceeds 70 g during the relevant event. |
| head_contained | bool | True | — | high-speed video | The head remains contained and protected by the side head-protection system. |
| head_protection_system_equipped | bool | True | — | high-speed video and postcrash inspection | A side head-protection system is equipped for this seating position. |
| interior_contact | bool | False | — | high-speed video and physical evidence | The head contacts vehicle interior hard structure or bottoms out the airbag. |

## `criterion_structure` — Vehicle structure

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Structure` | Injury measures and rating boundaries / Tables 1 and 3 (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| b_pillar_to_seat_centerline_cm | float | nan | cm | postcrash intrusion measurement | Minimum longitudinal B-pillar distance relative to the driver seat centerline. |
| door_opened | bool | False | — | postcrash inspection | A door opening occurred during the impact and requires a one-category downgrade. |
| integrity_failure | bool | False | — | postcrash inspection | Significant fuel leak, electrical compromise, smoke, fire, or battery thermal event. |
