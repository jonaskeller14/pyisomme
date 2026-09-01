# IIHS_Frontal_Moderate_Overlap

| property | value |
| --- | --- |
| name | IIHS \| Moderate Overlap Frontal Crashworthiness 2.0 |
| protocol | III |
| protocols | II, III |
| overall criterion | `Overall` |
| available_pages | Cover, Rating, Driver Rating Table, Driver Result Values Chart, Driver Values Table, Driver Head Acceleration, Driver HIC15, Driver Neck NIJ, Driver Neck Axial Load, Driver Neck Load Corridors, Driver Chest Injury Measures, Driver Femur Axial Force, Driver Tibia-Femur Displacement, Driver Tibia Index, Driver Tibia Axial Force, Driver Foot Acceleration, Rear Passenger Rating Table, Rear Passenger Result Values Chart, Rear Passenger Values Table, Rear Passenger Head Acceleration, Rear Passenger HIC15, Rear Passenger Neck NIJ, Rear Passenger Neck Axial Load, Rear Passenger Chest Measures, Rear Passenger Femur Axial Force |
| selected_pages | Cover, Rating, Driver Rating Table, Driver Result Values Chart, Driver Values Table, Driver Head Acceleration, Driver HIC15, Driver Neck NIJ, Driver Neck Axial Load, Driver Neck Load Corridors, Driver Chest Injury Measures, Driver Femur Axial Force, Driver Tibia-Femur Displacement, Driver Tibia Index, Driver Tibia Axial Force, Driver Foot Acceleration, Rear Passenger Rating Table, Rear Passenger Result Values Chart, Rear Passenger Values Table, Rear Passenger Head Acceleration, Rear Passenger HIC15, Rear Passenger Neck NIJ, Rear Passenger Neck Axial Load, Rear Passenger Chest Measures, Rear Passenger Femur Axial Force |

## `Overall` — Overall

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Overall` | Weighting principles for overall ratings / Table 9 | — | sum |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| p_driver | str | '1' | — | test report | Channel-code position of the H350M driver. |
| p_rear_passenger | str | '6' | — | test report | Channel-code position of the H35F rear occupant; derived from the driver side by default. |

## `criterion_driver` — Driver

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Driver` | Weighting principles for overall ratings / Table 9 (inherited) | — | sum |

## `criterion_driver/criterion_head_neck` — Head and neck

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_Neck` | Weighting principles for overall ratings / Table 9 (inherited) | — | min |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| hard_contact_downgrades | int | 0 | — | video and head acceleration | Rating levels required by the protocol's hard-contact flowchart. Use 0 when no qualifying contact occurred. |

## `criterion_driver/criterion_head_neck/criterion_hic_15` — HIC 15

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HIC_15` | Weighting principles for overall ratings / Table 9 (inherited) | 0 (from limits) | — |

Limits for `?1HICR0015??00RX`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 560 | 0 | green | upper | 1 | - |
| Acceptable | 700 | -2 | yellow | upper | 1 | - |
| Marginal | 840 | -10 | orange | upper | 1 | - |
| Poor | 840 | -20 | red | lower | 1 | - |

## `criterion_driver/criterion_head_neck/criterion_nij` — Nij

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Nij` | Weighting principles for overall ratings / Table 9 (inherited) | 0 (from limits) | — |

Limits for `?1NIJCIP00??00Y?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 0.8 | 0 | green | upper | 1 | - |
| Acceptable | 1 | -2 | yellow | upper | 1 | - |
| Marginal | 1.2 | -10 | orange | upper | 1 | - |
| Poor | 1.2 | -20 | red | lower | 1 | - |

## `criterion_driver/criterion_head_neck/criterion_neck_tension` — Neck axial tension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Tension` | Weighting principles for overall ratings / Table 9 (inherited) | 0 (from limits) | — |

Limits for `?1NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 2.6 | 0 | green | upper | kN | - |
| Acceptable | 3.3 | -2 | yellow | upper | kN | - |
| Marginal | 4 | -10 | orange | upper | kN | - |
| Poor | 4 | -20 | red | lower | kN | - |

## `criterion_driver/criterion_head_neck/criterion_neck_compression` — Neck compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Compression` | Weighting principles for overall ratings / Table 9 (inherited) | 0 (from limits) | — |

Limits for `?1NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -3.2 | 0 | green | lower | kN | - |
| Acceptable | -3.2 | -2 | yellow | upper | kN | - |
| Marginal | -4 | -10 | orange | upper | kN | - |
| Poor | -4.8 | -20 | red | upper | kN | - |

## `criterion_driver/criterion_head_neck/criterion_tension_corridor` — Neck tension duration corridor

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Tension_Corridor` | Weighting principles for overall ratings / Table 9 (inherited) | 0 (from limits) | — |

Limits for `?1NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | x=0:3.3, 0.01:3.185714286, 0.05:1.1, 0.1:1.1 | 0 | green | upper | kN | - |
| Acceptable | x=0:3.3, 0.01:3.185714286, 0.05:1.1, 0.1:1.1 | -2 | yellow | lower | kN | - |

## `criterion_driver/criterion_head_neck/criterion_compression_corridor` — Neck compression duration corridor

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Compression_Corridor` | Weighting principles for overall ratings / Table 9 (inherited) | 0 (from limits) | — |

Limits for `?1NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | x=0:-4, 0.01:-3.033333333, 0.05:-1.1, 0.1:-1.1 | 0 | green | lower | kN | - |
| Acceptable | x=0:-4, 0.01:-3.033333333, 0.05:-1.1, 0.1:-1.1 | -2 | yellow | upper | kN | - |

## `criterion_driver/criterion_head_neck/criterion_shear_corridor` — Neck shear duration corridor

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Shear_Corridor` | Weighting principles for overall ratings / Table 9 (inherited) | 0 (from limits) | — |

Limits for `?1NECKUP00??FOX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | x=0:-3.1, 0.01:-2.642857143, 0.05:-1.1, 0.1:-1.1 | 0 | green | lower | kN | - |
| Acceptable | x=0:-3.1, 0.01:-2.642857143, 0.05:-1.1, 0.1:-1.1 | -2 | yellow | upper | kN | - |
| Good | x=0:3.1, 0.01:2.46, 0.05:1.1, 0.1:1.1 | 0 | green | upper | kN | - |
| Acceptable | x=0:3.1, 0.01:2.46, 0.05:1.1, 0.1:1.1 | -2 | yellow | lower | kN | - |

## `criterion_driver/criterion_chest` — Chest

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest` | Weighting principles for overall ratings / Table 9 (inherited) | — | min |

## `criterion_driver/criterion_chest/criterion_acceleration` — Thoracic spine acceleration (3 ms)

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Thoracic_Spine_Acceleration` | Weighting principles for overall ratings / Table 9 (inherited) | 0 (from limits) | — |

Limits for `?1CHST003C??ACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 60 | 0 | green | upper | g0 | - |
| Acceptable | 75 | -2 | yellow | upper | g0 | - |
| Marginal | 90 | -10 | orange | upper | g0 | - |
| Poor | 90 | -20 | red | lower | g0 | - |

## `criterion_driver/criterion_chest/criterion_deflection` — Sternum deflection

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Sternum_Deflection` | Weighting principles for overall ratings / Table 9 (inherited) | 0 (from limits) | — |

Limits for `?1CHST0000??DSX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -50 | 0 | green | lower | mm | - |
| Acceptable | -50 | -2 | yellow | upper | mm | - |
| Marginal | -60 | -10 | orange | upper | mm | - |
| Poor | -75 | -20 | red | upper | mm | - |

## `criterion_driver/criterion_chest/criterion_deflection_rate` — Sternum deflection rate

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Sternum_Deflection_Rate` | Weighting principles for overall ratings / Table 9 (inherited) | 0 (from limits) | — |

Limits for `?1CHST0000??VEX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -6.6 | 0 | green | lower | m/s | - |
| Acceptable | -6.6 | -2 | yellow | upper | m/s | - |
| Marginal | -8.2 | -10 | orange | upper | m/s | - |
| Poor | -9.8 | -20 | red | upper | m/s | - |

## `criterion_driver/criterion_chest/criterion_vc` — Viscous criterion

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_VC` | Weighting principles for overall ratings / Table 9 (inherited) | 0 (from limits) | — |

Limits for `?1VCCR0000??VEX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 0.8 | 0 | green | upper | m/s | - |
| Acceptable | 1 | -2 | yellow | upper | m/s | - |
| Marginal | 1.2 | -10 | orange | upper | m/s | - |
| Poor | 1.2 | -20 | red | lower | m/s | - |

## `criterion_driver/criterion_thigh_hip` — Thigh and hip

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Thigh_Hip` | Weighting principles for overall ratings / Table 9 (inherited) | — | min |

## `criterion_driver/criterion_thigh_hip/criterion_left` — Left knee-thigh-hip injury risk

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_KTH_Left` | Weighting principles for overall ratings / Table 9 (inherited) | — | — |

## `criterion_driver/criterion_thigh_hip/criterion_right` — Right knee-thigh-hip injury risk

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_KTH_Right` | Weighting principles for overall ratings / Table 9 (inherited) | — | — |

## `criterion_driver/criterion_leg_foot` — Leg and foot

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Leg_Foot` | Weighting principles for overall ratings / Table 9 (inherited) | — | min |

## `criterion_driver/criterion_leg_foot/criterion_tibia_femur_displacement` — Tibia-femur displacement

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Tibia_Femur_Displacement` | Weighting principles for overall ratings / Table 9 (inherited) | 0 (from limits) | — |

Limits for `?1KNSL??00??DSX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -12 | 0 | green | lower | mm | - |
| Acceptable | -12 | -1 | yellow | upper | mm | - |
| Marginal | -15 | -4 | orange | upper | mm | - |
| Poor | -18 | -6 | red | upper | mm | - |

## `criterion_driver/criterion_leg_foot/criterion_tibia_index` — Tibia index

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Tibia_Index` | Weighting principles for overall ratings / Table 9 (inherited) | 0 (from limits) | — |

Limits for `?1TIIN??TO??000?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 0.8 | 0 | green | upper | 1 | - |
| Acceptable | 1 | -1 | yellow | upper | 1 | - |
| Marginal | 1.2 | -4 | orange | upper | 1 | - |
| Poor | 1.2 | -6 | red | lower | 1 | - |

## `criterion_driver/criterion_leg_foot/criterion_tibia_axial_force` — Tibia axial force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Tibia_Axial_Force` | Weighting principles for overall ratings / Table 9 (inherited) | 0 (from limits) | — |

Limits for `?1TIBI??LO??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -4 | 0 | green | lower | kN | - |
| Acceptable | -4 | -1 | yellow | upper | kN | - |
| Marginal | -6 | -4 | orange | upper | kN | - |
| Poor | -8 | -6 | red | upper | kN | - |

## `criterion_driver/criterion_leg_foot/criterion_foot_acceleration` — Foot acceleration

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Foot_Acceleration` | Weighting principles for overall ratings / Table 9 (inherited) | 0 (from limits) | — |

Limits for `?1FOOT??00??ACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 150 | 0 | green | upper | g0 | - |
| Acceptable | 200 | -1 | yellow | upper | g0 | - |
| Marginal | 260 | -4 | orange | upper | g0 | - |
| Poor | 260 | -6 | red | lower | g0 | - |

## `criterion_driver/criterion_restraints_kinematics` — Restraints and kinematics

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Restraints_Kinematics` | Weighting principles for overall ratings / Table 9 (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| demerits | int | 0 | — | video and postcrash inspection | Sum the H350M driver events in Table 3. |

## `criterion_rear_passenger` — Rear passenger

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Rear_Passenger` | Weighting principles for overall ratings / Table 9 (inherited) | — | sum |

## `criterion_rear_passenger/criterion_head_neck` — Head and neck

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_Neck` | Weighting principles for overall ratings / Table 9 (inherited) | — | min |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| hard_contact_over_70g | bool | False | — | video and head acceleration | Contact produced a resultant head acceleration above 70 g; downgrade one level. |
| interior_contact | bool | False | — | video | A primary-loading contact with the vehicle interior makes HIC-15 and Nij applicable. |

## `criterion_rear_passenger/criterion_head_neck/criterion_hic_15` — HIC 15 (contacts only)

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HIC_15` | Weighting principles for overall ratings / Table 9 (inherited) | 0 (from limits) | — |

Limits for `?6HICR0015??00RX`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 560 | 0 | green | upper | 1 | - |
| Acceptable | 700 | -2 | yellow | upper | 1 | - |
| Marginal | 840 | -10 | orange | upper | 1 | - |
| Poor | 840 | -20 | red | lower | 1 | - |

## `criterion_rear_passenger/criterion_head_neck/criterion_nij` — Nij (contacts only)

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Nij` | Weighting principles for overall ratings / Table 9 (inherited) | 0 (from limits) | — |

Limits for `?6NIJCIP00??00Y?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 0.8 | 0 | green | upper | 1 | - |
| Acceptable | 1 | -2 | yellow | upper | 1 | - |
| Marginal | 1.2 | -10 | orange | upper | 1 | - |
| Poor | 1.2 | -20 | red | lower | 1 | - |

## `criterion_rear_passenger/criterion_head_neck/criterion_neck_tension` — Neck axial tension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Tension` | Weighting principles for overall ratings / Table 9 (inherited) | 0 (from limits) | — |

Limits for `?6NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 2 | 0 | green | upper | kN | - |
| Acceptable | 2.4 | -2 | yellow | upper | kN | - |
| Marginal | 2.8 | -10 | orange | upper | kN | - |
| Poor | 2.8 | -20 | red | lower | kN | - |

## `criterion_rear_passenger/criterion_head_neck/criterion_neck_compression` — Neck compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck_Compression` | Weighting principles for overall ratings / Table 9 (inherited) | 0 (from limits) | — |

Limits for `?6NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -2 | 0 | green | lower | kN | - |
| Acceptable | -2 | -2 | yellow | upper | kN | - |
| Marginal | -2.5 | -10 | orange | upper | kN | - |
| Poor | -3 | -20 | red | upper | kN | - |

## `criterion_rear_passenger/criterion_chest` — Chest

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest` | Weighting principles for overall ratings / Table 9 (inherited) | — | min |

## `criterion_rear_passenger/criterion_chest/criterion_chest_index` — Chest Index

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Index` | Weighting principles for overall ratings / Table 9 (inherited) | 0 (from limits) | — |

Limits for `?6CHST0000??DSX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 35 | 0 | green | upper | mm | - |
| Acceptable | 40 | -2 | yellow | upper | mm | - |
| Marginal | 45 | -10 | orange | upper | mm | - |
| Poor | 45 | -20 | red | lower | mm | - |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| dynamic_belt_position_mm | float | 17 | mm | pressure mat | Vertical shoulder-belt centerline above the sternum potentiometer at maximum sternum deflection; Version III Appendix A automates this measurement. |

## `criterion_rear_passenger/criterion_chest/criterion_shoulder_belt_tension` — Shoulder belt tension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Shoulder_Belt_Tension` | Weighting principles for overall ratings / Table 9 (inherited) | 0 (from limits) | — |

Limits for `?6SEBE????B3FO[X0]?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 5.9 | 0 | green | upper | kN | - |
| Marginal | 5.9 | -10 | orange | lower | kN | - |

## `criterion_rear_passenger/criterion_thigh` — Thigh

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Thigh` | Weighting principles for overall ratings / Table 9 (inherited) | — | min |

## `criterion_rear_passenger/criterion_thigh/criterion_femur_compression` — Femur axial compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Compression` | Weighting principles for overall ratings / Table 9 (inherited) | 0 (from limits) | — |

Limits for `?6FEMR??00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -4.9 | 0 | green | lower | kN | - |
| Acceptable | -4.9 | -2 | yellow | upper | kN | - |
| Marginal | -6.2 | -6 | orange | upper | kN | - |
| Poor | -7.4 | -10 | red | upper | kN | - |

## `criterion_rear_passenger/criterion_restraints_kinematics` — Restraints and kinematics

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Restraints_Kinematics` | Weighting principles for overall ratings / Table 9 (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| demerits | int | 0 | — | video, pressure mat, and postcrash inspection | Sum the H35F rear-occupant events in Table 8. |

## `criterion_structure` — Vehicle structure

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Structure` | Weighting principles for overall ratings / Table 9 (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| integrity_failure | bool | False | — | postcrash inspection | Significant fuel, electrical, smoke, fire, or battery thermal event. |
| intrusion_rating | int | 4 | — | intrusion measurements | Initial Figure 7 category: 4=Good, 3=Acceptable, 2=Marginal, 1=Poor. |
| qualitative_downgrades | int | 0 | — | postcrash inspection | Number of one-category downgrades for adverse deformation observations. |
