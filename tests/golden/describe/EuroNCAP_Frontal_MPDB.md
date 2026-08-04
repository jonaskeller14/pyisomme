# EuroNCAP_Frontal_MPDB

| property | value |
| --- | --- |
| name | Euro NCAP \| Frontal-Impact against MPDB with 50 % Overlap at 50/50 km/h |
| protocol | 9.3 |
| protocols | 9.3 |
| overall criterion | `Overall` |
| pages | Page_Cover, Page_Rating_Table, Page_Driver_Result_Values_Chart, Page_Driver_Rating_Table, Page_Driver_Values_Table, Page_Driver_Belt, Page_Driver_Head_Acceleration, Page_Driver_Head_Damage, Page_Driver_Neck_Load, Page_Driver_Chest_Compression, Page_Driver_Abdomen_Compression, Page_Driver_Femur_Axial_Force, Page_Driver_Knee_Slider_Compression, Page_Driver_Tibia_Compression, Page_Driver_Tibia_Index, Page_Passenger_Result_Values_Chart, Page_Passenger_Rating_Table, Page_Passenger_Values_Table, Page_Passenger_Belt, Page_Passenger_Head_Acceleration, Page_Passenger_Neck_Load, Page_Passenger_Chest_Deflection, Page_Passenger_Femur_Axial_Force, Page_Passenger_Knee_Slider_Compression, Page_Passenger_Tibia_Compression, Page_Passenger_Tibia_Index, Page_OLC, Page_OLC_Trolley |

## `Overall` — Overall

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Overall` | §3 | 8 | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| p_driver | int | 1 | — | test report | Channel-code position of the driver. Defaults to the 'Driver position object 1' test-info field when the test carries it. |
| p_passenger | int | 3 | — | test report | Channel-code position of the front passenger. Derived from p_driver (1 for a right-hand-drive test) unless set explicitly. |

## `criterion_driver` — Driver

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Driver` | §3 (inherited) | 16 | sum |

## `criterion_driver/criterion_head_neck` — Head & Neck

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_Neck` | §3.1.1 | 4 | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| steering_wheel_airbag_exists | bool | True | — | test report | Is a steering-wheel airbag fitted? Without one the head & neck box scores 0. |

## `criterion_driver/criterion_head_neck/criterion_head` — Head

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head` | §3.1.1 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| hard_contact | bool | True | — | video | Was hard head contact observed? A head-acceleration peak above 80 g forces this to True regardless (Appendix A2: 'video OR curve'). |

## `criterion_driver/criterion_head_neck/criterion_head/criterion_hic_15` — HIC 15

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HIC_15` | §3.1.1 (inherited) | 4 (from limits) | — |

Limits for `?1HICR0015??00RX`, `?1HICRCG15??00RX`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 500 | 4 | green | upper | 1 | - |
| Adequate | 500 | 4 | yellow | lower | 1 | - |
| Marginal | 566.667 | 2.669 | orange | lower | 1 | - |
| Weak | 633.333 | 1.329 | brown | lower | 1 | - |
| Poor | 700 | 0 | red | — | 1 | - |
| Capping | 700 | -inf | gray | lower | 1 | - |

## `criterion_driver/criterion_head_neck/criterion_head/criterion_head_a3ms` — Head a3ms

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_a3ms` | §3.1.1 (inherited) | 4 (from limits) | — |

Limits for `?1HEAD003C??ACR?`, `?1HEADCG3C??ACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 72 | 4 | green | upper | g0 | - |
| Adequate | 72 | 4 | yellow | lower | g0 | - |
| Marginal | 74.667 | 2.669 | orange | lower | g0 | - |
| Weak | 77.333 | 1.329 | brown | lower | g0 | - |
| Poor | 80 | 0 | red | — | g0 | - |
| Capping | 80 | -inf | gray | lower | g0 | - |

## `criterion_driver/criterion_head_neck/criterion_head/criterion_damage` — Modifier for Brain Injury - DAMAGE

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_DAMAGE` | §3.2.1.1 | 0 (from limits) | — |

Limits for `?1HEADDAMA??AAR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| 0 pt. Modifier | 0.42 | 0 | green | upper | rad/s^2 | - |
| -1 pt. Modifier | 0.42 | -1 | orange | lower | rad/s^2 | - |
| -2 pt. Modifier | 0.47 | -2 | red | lower | rad/s^2 | - |

## `criterion_driver/criterion_head_neck/criterion_head/criterion_UnstableAirbagContact` — Modifier for Unstable Airbag Contact

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_UnstableAirbagContact` | §3.2.1.1 | — | — |

## `criterion_driver/criterion_head_neck/criterion_head/criterion_HazardousAirbagDeployment` — Modifier for Hazardous Airbag Deployment

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HazardousAirbagDeployment` | §3.2.1.1 | — | — |

## `criterion_driver/criterion_head_neck/criterion_head/criterion_IncorrectAirbagDeployment` — Modifier for Incorrect Airbag Deployment

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_IncorrectAirbagDeployment` | §3.2.1.1 | — | — |

## `criterion_driver/criterion_head_neck/criterion_head/criterion_DisplacementSteeringColumn` — Modifier for Displacement of Steering Column

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_DisplacementSteeringColumn` | §3.2.1.1 | — | — |

## `criterion_driver/criterion_head_neck/criterion_neck` — Neck

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck` | §3.1.2 | — | — |

## `criterion_driver/criterion_head_neck/criterion_neck/criterion_my_extension` — Neck My extension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_My_Extension` | §3.1.2 (inherited) | 4 (from limits) | — |

Limits for `?1NECKUP00??MOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -42 | 4 | green | lower | Nm | - |
| Adequate | -42 | 4 | yellow | upper | Nm | - |
| Marginal | -47 | 2.669 | orange | upper | Nm | - |
| Weak | -52 | 1.329 | brown | upper | Nm | - |
| Poor | -57 | 0 | red | — | Nm | - |
| Capping | -57 | -inf | gray | upper | Nm | - |

## `criterion_driver/criterion_head_neck/criterion_neck/criterion_fz_tension` — Neck Fz tension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Fz_Tension` | §3.1.2 (inherited) | 4 (from limits) | — |

Limits for `?1NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 2.7 | 4 | green | upper | kN | - |
| Adequate | 2.7 | 4 | yellow | lower | kN | - |
| Marginal | 2.9 | 2.669 | orange | lower | kN | - |
| Weak | 3.1 | 1.329 | brown | lower | kN | - |
| Poor | 3.3 | 0 | red | — | kN | - |
| Capping | 3.3 | -inf | gray | lower | kN | - |

## `criterion_driver/criterion_head_neck/criterion_neck/criterion_fx_shear` — Neck Fx shear

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Fx_Shear` | §3.1.2 (inherited) | 4 (from limits) | — |

Limits for `?1NECKUP00??FOX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 1.9 | 4 | green | upper | kN | - |
| Adequate | 1.9 | 4 | yellow | lower | kN | - |
| Marginal | 2.3 | 2.669 | orange | lower | kN | - |
| Weak | 2.7 | 1.329 | brown | lower | kN | - |
| Poor | 3.1 | 0 | red | — | kN | - |
| Capping | 3.1 | -inf | gray | lower | kN | - |
| Good | -1.9 | 4 | green | lower | kN | - |
| Adequate | -1.9 | 4 | yellow | upper | kN | - |
| Marginal | -2.3 | 2.669 | orange | upper | kN | - |
| Weak | -2.7 | 1.329 | brown | upper | kN | - |
| Poor | -3.1 | 0 | red | — | kN | - |
| Capping | -3.1 | -inf | gray | upper | kN | - |

## `criterion_driver/criterion_chest_abdomen` — Chest and Abdomen

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Abdomen` | §3.1.3 | 4 | — |

## `criterion_driver/criterion_chest_abdomen/criterion_chest` — Chest

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest` | §3.1.3.1 | — | — |

## `criterion_driver/criterion_chest_abdomen/criterion_chest/criterion_chest_compression` — Chest Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Compression` | §3.1.3.1 (inherited) | 4 (from limits) | — |

Limits for `?1CHST??????DSX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Capping | -60 | -inf | gray | upper | mm | - |
| Poor | -60 | 0 | red | — | mm | - |
| Weak | -51.667 | 1.329 | brown | upper | mm | - |
| Marginal | -43.333 | 2.669 | orange | upper | mm | - |
| Adequate | -35 | 4 | yellow | upper | mm | - |
| Good | -35 | 4 | green | lower | mm | - |

## `criterion_driver/criterion_chest_abdomen/criterion_chest/criterion_shoulder_belt_load` — Modifier Shoulder Belt Load

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_ShoulderBeltLoad` | §3.1.3.1 (inherited) | 0 (from limits) | — |

Limits for `?1SEBE????B3FO[X0]?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| 0 pt. Modifier | 6 | 0 | green | upper | kN | - |
| -2 pt. Modifier | 6 | -2 | red | lower | kN | - |

## `criterion_driver/criterion_chest_abdomen/criterion_chest/criterion_SteeringWheelContact` — Modifier Chest Steering Wheel Contact

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_SteeringWheelContact` | §3.2.1.2 | — | — |

## `criterion_driver/criterion_chest_abdomen/criterion_chest/criterion_DisplacementAPillar` — Modifier for Displacement of the A Pillar

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_DisplacementAPillar` | §3.2.1.2 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| displacement_a_pillar | float | 0 | mm | measurement | Rearward displacement of the driver's front door pillar, 100 mm below the lowest level of the side window aperture. No penalty up to 100 mm, −2 points above 200 mm, linear in between (driver only). |

## `criterion_driver/criterion_chest_abdomen/criterion_chest/criterion_CompartmentIntegrity` — Modifier for Integrity of the Passenger Compartment

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_CompartmentIntegrity` | §3.2.1.2 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| compartment_integrity_compromised | bool | False | — | test report | Structural integrity of the passenger compartment compromised — door latch/hinge failure, door buckling, cross facia rail to A pillar separation, or severe loss of door aperture strength. −1 point (driver only). |

## `criterion_driver/criterion_chest_abdomen/criterion_abdomen` — Abdomen

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Abdomen` | §3.1.3.2 | — | — |

## `criterion_driver/criterion_chest_abdomen/criterion_abdomen/criterion_abdomen_compression` — Abdomen Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Abdomen_Compression` | §3.1.3.2 (inherited) | 4 (from limits) | — |

Limits for `?1ABDO??????DSX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Poor | -88 | 0 | red | upper | mm | - |
| Good | -88 | 4 | green | lower | mm | - |

## `criterion_driver/criterion_knee_femur_pelvis` — Knee, Femur and Pelvis

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Knee_Femur_Pelvis` | §3.1.4 | 4 | — |

## `criterion_driver/criterion_knee_femur_pelvis/criterion_pelvis` — Pelvis

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Pelvis` | §3.1.4.1 | — | — |

## `criterion_driver/criterion_knee_femur_pelvis/criterion_pelvis/criterion_acetabulum_force` — Acetabulum Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Acetabulum_Force` | §3.1.4.1 (inherited) | 4 (from limits) | — |

Limits for `?1ACTB??00??FOR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Poor | -4.1 | 0 | red | upper | kN | - |
| Weak | -3.827 | 1.329 | brown | upper | kN | - |
| Marginal | -3.553 | 2.669 | orange | upper | kN | - |
| Adequate | -3.28 | 4 | yellow | upper | kN | - |
| Good | -3.28 | 4 | green | lower | kN | - |

## `criterion_driver/criterion_knee_femur_pelvis/criterion_femur` — Femur

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur` | §3.1.4 (inherited) | — | — |

## `criterion_driver/criterion_knee_femur_pelvis/criterion_femur/criterion_femur_compression` — Femur Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Compression` | §3.1.4 (inherited) | 4 (from limits) | — |

Limits for `?1FEMR??00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -3.8 | 4 | green | lower | kN | - |
| Adequate | -3.8 | 4 | yellow | upper | kN | - |
| Marginal | x=0:-5.557, 0.01:-5.556496, 0.05:-5.55448, 0.1:-5.55196 | 2.669 | orange | upper | kN | - |
| Weak | x=0:-7.313, 0.01:-7.311994, 0.05:-7.30797, 0.1:-7.30294 | 1.329 | brown | upper | kN | - |
| Poor | x=0:-9.07, 0.01:-9.06849, 0.05:-9.06245, 0.1:-9.0549 | 0 | red | upper | kN | - |

## `criterion_driver/criterion_knee_femur_pelvis/criterion_knee` — Knee

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Knee` | §3.1.4 (inherited) | — | — |

## `criterion_driver/criterion_knee_femur_pelvis/criterion_knee/criterion_knee_slider_compression` — Knee Slider Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Knee_Slider_Compression` | §3.1.4 (inherited) | 4 (from limits) | — |

Limits for `?1KNSL??00??DSX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Poor | -15 | 0 | red | upper | mm | - |
| Weak | -12 | 1.329 | brown | upper | mm | - |
| Marginal | -9 | 2.669 | orange | upper | mm | - |
| Adequate | -6 | 4 | yellow | upper | mm | - |
| Good | -6 | 4 | green | lower | mm | - |

## `criterion_driver/criterion_knee_femur_pelvis/criterion_submarining` — Submarining

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Submarining` | §3.1.4 (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| submarining | bool | False | — | video | Pelvis slid under the lap belt. Caps the femur box at 0 points. |

## `criterion_driver/criterion_knee_femur_pelvis/criterion_VariableContact` — Modifier for Variable Contact

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_VariableContact` | §3.2.1.4 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| variable_contact_left | bool | False | — | knee mapping | Over the left knee's contact area, femur loads above 3.8 kN and/or knee slider displacements above 6 mm would be expected. −1 point. |
| variable_contact_right | bool | False | — | knee mapping | Over the right knee's contact area, femur loads above 3.8 kN and/or knee slider displacements above 6 mm would be expected. −1 point. |

## `criterion_driver/criterion_knee_femur_pelvis/criterion_ConcentratedLoading` — Modifier for Concentrated Loading

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_ConcentratedLoading` | §3.2.1.4 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| concentrated_loading_left | bool | False | — | knee mapping | Structures in the left knee impact area could concentrate forces on part of the knee. −1 point. |
| concentrated_loading_right | bool | False | — | knee mapping | Structures in the right knee impact area could concentrate forces on part of the knee. −1 point. |

## `criterion_driver/criterion_lowerleg_foot_ankle` — Lower Leg, Foot and Ankle

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_LowerLeg_Foot_Ankle` | §3.1.5 | 4 | — |

## `criterion_driver/criterion_lowerleg_foot_ankle/criterion_tibia_index` — Tibia Index

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Tibia_Index` | §3.1.5.1 | 4 (from limits) | — |

Limits for `?1TIIN??00??000?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 0.4 | 4 | green | upper | 1 | - |
| Adequate | 0.4 | 4 | yellow | lower | 1 | - |
| Marginal | 0.7 | 2.669 | orange | lower | 1 | - |
| Weak | 1 | 1.329 | brown | lower | 1 | - |
| Poor | 1.3 | 0 | red | lower | 1 | - |

## `criterion_driver/criterion_lowerleg_foot_ankle/criterion_tibia_compression` — Tibia Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Tibia_Compression` | §3.1.5.1 | 4 (from limits) | — |

Limits for `?1TIBI??????FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Poor | -8 | 0 | red | upper | kN | - |
| Weak | -6 | 1.329 | brown | upper | kN | - |
| Marginal | -4 | 2.669 | orange | upper | kN | - |
| Adequate | -2 | 4 | yellow | upper | kN | - |
| Good | -2 | 4 | green | lower | kN | - |

## `criterion_driver/criterion_lowerleg_foot_ankle/criterion_pedal_rearward_displacement` — Pedal Rearward Displacement

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Pedal_Rearward_Displacement` | §3.1.5.2 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| pedal_rearward_displacement | float | 0 | mm | measurement | Rearward displacement of the pedal (4 points below 100 mm, 0 above 200 mm). |

## `criterion_driver/criterion_lowerleg_foot_ankle/criterion_PedalUpwardDisplacement` — Modifier for Upward Displacement of the Worst Performing Pedal

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_PedalUpwardDisplacement` | §3.2.1.5 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| pedal_upward_displacement | float | 0 | mm | measurement | Upward static displacement of the worst performing pedal. No penalty up to 90 % of the 80 mm EEVC limit, −1 point beyond 110 %, linear in between. |

## `criterion_driver/criterion_lowerleg_foot_ankle/criterion_FootwellRupture` — Modifier for Footwell Rupture

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_FootwellRupture` | §3.2.1.6 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| footwell_rupture | bool | False | — | test report | Significant rupture of the footwell area, usually separation of spot welded seams. −1 point. |

## `criterion_driver/criterion_lowerleg_foot_ankle/criterion_PedalBlocking` — Modifier for Pedal Blocking

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_PedalBlocking` | §3.2.1.6 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| blocked_pedal_rearward_displacement | float | 0 | mm | measurement | Rearward displacement of a 'blocked' pedal relative to the pre-test measurement. A pedal is blocked when its forward movement under a 200 N load is below 25 mm. Sliding scale 0 to −1 point between 50 mm and 175 mm. |

## `criterion_passenger` — Passenger

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Passenger` | §3 (inherited) | 16 | sum |

## `criterion_passenger/criterion_head_neck` — Head and Neck

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_Neck` | §3.1.6 | 4 | — |

## `criterion_passenger/criterion_head_neck/criterion_head` — Head

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head` | §3.1.6.1 | — | — |

## `criterion_passenger/criterion_head_neck/criterion_head/criterion_hic_15` — HIC 15

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HIC_15` | §3.1.6.1 (inherited) | 4 (from limits) | — |

Limits for `?3HICR0015??00RX`, `?3HICRCG15??00RX`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 500 | 4 | green | upper | 1 | - |
| Adequate | 500 | 4 | yellow | lower | 1 | - |
| Marginal | 566.667 | 2.669 | orange | lower | 1 | - |
| Weak | 633.333 | 1.329 | brown | lower | 1 | - |
| Poor | 700 | 0 | red | — | 1 | - |
| Capping | 700 | -inf | gray | lower | 1 | - |

## `criterion_passenger/criterion_head_neck/criterion_head/criterion_head_a3ms` — Head a3ms

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_a3ms` | §3.1.6.1 (inherited) | 4 (from limits) | — |

Limits for `?3HEAD003C??ACR?`, `?3HEADCG3C??ACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 72 | 4 | green | upper | g0 | - |
| Adequate | 72 | 4 | yellow | lower | g0 | - |
| Marginal | 74.667 | 2.669 | orange | lower | g0 | - |
| Weak | 77.333 | 1.329 | brown | lower | g0 | - |
| Poor | 80 | 0 | red | — | g0 | - |
| Capping | 80 | -inf | gray | lower | g0 | - |

## `criterion_passenger/criterion_head_neck/criterion_head/criterion_UnstableAirbagContact` — Modifier for Unstable Airbag Contact

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_UnstableAirbagContact` | §3.2.1.1 | — | — |

## `criterion_passenger/criterion_head_neck/criterion_head/criterion_HazardousAirbagDeployment` — Modifier for Hazardous Airbag Deployment

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HazardousAirbagDeployment` | §3.2.1.1 | — | — |

## `criterion_passenger/criterion_head_neck/criterion_head/criterion_IncorrectAirbagDeployment` — Modifier for Incorrect Airbag Deployment

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_IncorrectAirbagDeployment` | §3.2.1.1 | — | — |

## `criterion_passenger/criterion_head_neck/criterion_neck` — Neck

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck` | §3.1.6.2 | — | — |

## `criterion_passenger/criterion_head_neck/criterion_neck/criterion_fx_shear` — Neck Fx shear

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Fx_Shear` | §3.1.6.2 (inherited) | 4 (from limits) | — |

Limits for `?3NECKUP00??FOX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | x=0:1.9, 0.01:1.89972, 0.05:1.8986, 0.1:1.8972 | 4 | green | upper | kN | - |
| Adequate | x=0:1.9, 0.01:1.89972, 0.05:1.8986, 0.1:1.8972 | 4 | yellow | lower | kN | - |
| Marginal | x=0:2.3, 0.01:2.2996, 0.05:2.298, 0.1:2.296 | 2.669 | orange | lower | kN | - |
| Weak | x=0:2.7, 0.01:2.69948, 0.05:2.6974, 0.1:2.6948 | 1.329 | brown | lower | kN | - |
| Poor | x=0:3.1, 0.01:3.09936, 0.05:3.0968, 0.1:3.0936 | 0 | red | — | kN | - |
| Capping | x=0:3.1, 0.01:3.09936, 0.05:3.0968, 0.1:3.0936 | -inf | gray | lower | kN | - |
| Good | x=0:-1.9, 0.01:-1.89972, 0.05:-1.8986, 0.1:-1.8972 | 4 | green | lower | kN | - |
| Adequate | x=0:-1.9, 0.01:-1.89972, 0.05:-1.8986, 0.1:-1.8972 | 4 | yellow | upper | kN | - |
| Marginal | x=0:-2.3, 0.01:-2.2996, 0.05:-2.298, 0.1:-2.296 | 2.669 | orange | upper | kN | - |
| Weak | x=0:-2.7, 0.01:-2.69948, 0.05:-2.6974, 0.1:-2.6948 | 1.329 | brown | upper | kN | - |
| Poor | x=0:-3.1, 0.01:-3.09936, 0.05:-3.0968, 0.1:-3.0936 | 0 | red | — | kN | - |
| Capping | x=0:-3.1, 0.01:-3.09936, 0.05:-3.0968, 0.1:-3.0936 | -inf | gray | upper | kN | - |

## `criterion_passenger/criterion_head_neck/criterion_neck/criterion_fz_tension` — Fz Tension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Fz_Tension` | §3.1.6.2 (inherited) | 4 (from limits) | — |

Limits for `?3NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | x=0:2.7, 0.01:2.699885714, 0.05:2.699428571, 0.1:2.698857143 | 4 | green | upper | kN | - |
| Adequate | x=0:2.7, 0.01:2.699885714, 0.05:2.699428571, 0.1:2.698857143 | 4 | yellow | lower | kN | - |
| Marginal | x=0:2.9, 0.01:2.899885714, 0.05:2.899428571, 0.1:2.898857143 | 2.669 | orange | lower | kN | - |
| Weak | x=0:3.1, 0.01:3.099885714, 0.05:3.099428571, 0.1:3.098857143 | 1.329 | brown | lower | kN | - |
| Poor | x=0:3.3, 0.01:3.299885714, 0.05:3.299428571, 0.1:3.298857143 | 0 | red | — | kN | - |
| Capping | x=0:3.3, 0.01:3.299885714, 0.05:3.299428571, 0.1:3.298857143 | -inf | gray | lower | kN | - |

## `criterion_passenger/criterion_head_neck/criterion_neck/criterion_my_extension` — My Extension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_My_Extension` | §3.1.6.2 (inherited) | 4 (from limits) | — |

Limits for `?3NECKUP00??MOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -42 | 4 | green | lower | Nm | - |
| Adequate | -42 | 4 | yellow | upper | Nm | - |
| Marginal | -47 | 2.669 | orange | upper | Nm | - |
| Weak | -52 | 1.329 | brown | upper | Nm | - |
| Poor | -57 | 0 | red | — | Nm | - |
| Capping | -57 | -inf | gray | upper | Nm | - |

## `criterion_passenger/criterion_chest` — Chest

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest` | §3.1.7 | 4 | — |

## `criterion_passenger/criterion_chest/criterion_chest_compression` — Chest Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Compression` | §3.1.7 (inherited) | 4 (from limits) | — |

Limits for `?3CHST000[03]??DSX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Capping | -42 | -inf | gray | upper | mm | - |
| Poor | -42 | 0 | red | — | mm | - |
| Weak | -35.333 | 1.329 | brown | upper | mm | - |
| Marginal | -28.667 | 2.669 | orange | upper | mm | - |
| Adequate | -22 | 4 | yellow | upper | mm | - |
| Good | -22 | 4 | green | lower | mm | - |

## `criterion_passenger/criterion_chest/criterion_chest_vc` — Chest VC

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_VC` | §3.1.7 (inherited) | 4 (from limits) | — |

Limits for `?3VCCR000[03]??VEX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 0.5 | 4 | green | upper | m/s | - |
| Adequate | 0.5 | 4 | yellow | lower | m/s | - |
| Marginal | 0.667 | 2.669 | orange | lower | m/s | - |
| Weak | 0.833 | 1.329 | brown | lower | m/s | - |
| Poor | 1 | 0 | red | — | m/s | - |
| Capping | 1 | -inf | gray | lower | m/s | - |

## `criterion_passenger/criterion_chest/criterion_shoulder_belt_load` — Modifier Shoulder Belt Load

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_ShoulderBeltLoad` | §3.1.7 (inherited) | 0 (from limits) | — |

Limits for `?3SEBE????B3FO[X0]?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| 0 pt. Modifier | 6 | 0 | green | upper | kN | - |
| -2 pt. Modifier | 6 | -2 | red | lower | kN | - |

## `criterion_passenger/criterion_knee_femur_pelvis` — Knee, Femur and Pelvis

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Knee_Femur_Pelvis` | §3.1.8 | 4 | — |

## `criterion_passenger/criterion_knee_femur_pelvis/criterion_femur_compression` — Femur Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Compression` | §3.1.8 (inherited) | 4 (from limits) | — |

Limits for `?3FEMR??00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -3.8 | 4 | green | lower | kN | - |
| Adequate | -3.8 | 4 | yellow | upper | kN | - |
| Marginal | x=0:-5.557, 0.01:-5.556496, 0.05:-5.55448, 0.1:-5.55196 | 2.669 | orange | upper | kN | - |
| Weak | x=0:-7.313, 0.01:-7.311994, 0.05:-7.30797, 0.1:-7.30294 | 1.329 | brown | upper | kN | - |
| Poor | x=0:-9.07, 0.01:-9.06849, 0.05:-9.06245, 0.1:-9.0549 | 0 | red | upper | kN | - |

## `criterion_passenger/criterion_knee_femur_pelvis/criterion_knee_slider_compression` — Knee Slider Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Knee_Slider_Compression` | §3.1.8 (inherited) | 4 (from limits) | — |

Limits for `?3KNSL??00??DSX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Poor | -15 | 0 | red | upper | mm | - |
| Weak | -12 | 1.329 | brown | upper | mm | - |
| Marginal | -9 | 2.669 | orange | upper | mm | - |
| Adequate | -6 | 4 | yellow | upper | mm | - |
| Good | -6 | 4 | green | lower | mm | - |

## `criterion_passenger/criterion_knee_femur_pelvis/criterion_VariableContact` — Modifier for Variable Contact

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_VariableContact` | §3.2.1.4 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| variable_contact_left | bool | False | — | knee mapping | Over the left knee's contact area, femur loads above 3.8 kN and/or knee slider displacements above 6 mm would be expected. −1 point. |
| variable_contact_right | bool | False | — | knee mapping | Over the right knee's contact area, femur loads above 3.8 kN and/or knee slider displacements above 6 mm would be expected. −1 point. |

## `criterion_passenger/criterion_knee_femur_pelvis/criterion_ConcentratedLoading` — Modifier for Concentrated Loading

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_ConcentratedLoading` | §3.2.1.4 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| concentrated_loading_left | bool | False | — | knee mapping | Structures in the left knee impact area could concentrate forces on part of the knee. −1 point. |
| concentrated_loading_right | bool | False | — | knee mapping | Structures in the right knee impact area could concentrate forces on part of the knee. −1 point. |

## `criterion_passenger/criterion_lowerleg` — Lower Leg

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_LowerLeg` | §3.1.9 | 4 | — |

## `criterion_passenger/criterion_lowerleg/criterion_tibia_index` — Tibia Index

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Tibia_Index` | §3.1.5.1 | 4 (from limits) | — |

Limits for `?3TIIN??00??000?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 0.4 | 4 | green | upper | 1 | - |
| Adequate | 0.4 | 4 | yellow | lower | 1 | - |
| Marginal | 0.7 | 2.669 | orange | lower | 1 | - |
| Weak | 1 | 1.329 | brown | lower | 1 | - |
| Poor | 1.3 | 0 | red | lower | 1 | - |

## `criterion_passenger/criterion_lowerleg/criterion_tibia_compression` — Tibia Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Tibia_Compression` | §3.1.5.1 | 4 (from limits) | — |

Limits for `?3TIBI??????FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Poor | -8 | 0 | red | upper | kN | - |
| Weak | -6 | 1.329 | brown | upper | kN | - |
| Marginal | -4 | 2.669 | orange | upper | kN | - |
| Adequate | -2 | 4 | yellow | upper | kN | - |
| Good | -2 | 4 | green | lower | kN | - |

## `criterion_door_opening_during_impact` — Door Opening During Impact

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_DoorOpeningDuringImpact` | §3 (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| number_of_door_openings_during_impact | int | 0 | — | test report | How many doors opened during the impact. −1 point each. |

## `criterion_compatibility_modifier` — Compatibility Modifier

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Compatibility_Modifier` | §3.3 | — | — |

## `criterion_compatibility_modifier/criterion_olc_modifier` — Occupant Load Criterion (OLC) Modifier

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_OLC_Modifier` | §3.3 (inherited) | 0 (from limits) | — |

Limits for `M?MBAR0OLC??VEX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| 0 pt. Modifier | 25 | 0 | black | upper | g0 | - |
| -2..0 pt. Modifier | 25 | 0 | black | lower | g0 | - |
| -2 pt. Modifier | 40 | -2 | black | lower | g0 | - |
