# EuroNCAP_Frontal_50kmh

| property | value |
| --- | --- |
| name | Euro NCAP \| Frontal-Impact against Rigid Wall with 100 % Overlap at 50 km/h |
| protocol | 9.3 |
| protocols | 9.3 |
| overall criterion | `Overall` |
| pages | Page_Cover, Page_Rating_Table, Page_Driver_Result_Values_Chart, Page_Driver_Rating_Table, Page_Driver_Values_Table, Page_Driver_Belt, Page_Driver_Head_Acceleration, Page_Driver_Neck_Load, Page_Driver_Neck_NIJ, Page_Driver_Chest_Deflection, Page_Driver_Femur_Axial_Force, Page_Front_Passenger_Result_Values_Chart, Page_Front_Passenger_Rating_Table, Page_Front_Passenger_Values_Table, Page_Front_Passenger_Belt, Page_Front_Passenger_Head_Acceleration, Page_Front_Passenger_Neck_Load, Page_Front_Passenger_Neck_NIJ, Page_Front_Passenger_Chest_Deflection, Page_Front_Passenger_Femur_Axial_Force, Page_Rear_Passenger_Result_Values_Chart, Page_Rear_Passenger_Rating_Table, Page_Rear_Passenger_Values_Table, Page_Rear_Passenger_Belt, Page_Rear_Passenger_Head_Acceleration, Page_Rear_Passenger_Neck_Load, Page_Rear_Passenger_Chest_Deflection, Page_Rear_Passenger_Femur_Axial_Force, Page_OLC |

## `Overall` — Overall

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Overall` | §TODO full-width frontal | 8 | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| p_driver | int | 1 | — | test report | Channel-code position of the driver. Defaults to the 'Driver position object 1' test-info field when the test carries it. |
| p_front_passenger | int | 3 | — | test report | Channel-code position of the front passenger. Derived from p_driver (1 for a right-hand-drive test) unless set explicitly. |
| p_rear_passenger | int | 6 | — | test report | Channel-code position of the rear passenger. Derived from p_driver (4 for a right-hand-drive test) unless set explicitly. |

## `criterion_door_opening_during_impact` — Door Opening During Impact

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_DoorOpeningDuringImpact` | §TODO full-width frontal (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| number_of_door_openings_during_impact | int | 0 | — | test report | How many doors opened during the impact. −1 point each. |

## `criterion_driver` — Driver

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Driver` | §TODO full-width frontal (inherited) | 16 | sum |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| steering_wheel_airbag_exists | bool | True | — | test report | Is a steering-wheel airbag fitted? Without one the head and neck boxes score 0. |

## `criterion_driver/criterion_chest` — Chest

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest` | §TODO full-width frontal (inherited) | 4 | — |

## `criterion_driver/criterion_chest/criterion_SteeringWheelContact` — Modifier Chest Steering Wheel Contact

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_SteeringWheelContact` | §TODO full-width frontal (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| steering_wheel_contact | bool | False | — | video | Chest contact with the steering wheel (driver only). −1 point. |

## `criterion_driver/criterion_chest/criterion_chest_deflection` — Chest Deflection

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Deflection` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?1CHST000[03]??DSX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Capping | -34 | -inf | gray | upper | mm | - |
| Poor | -34 | 0 | red | — | mm | - |
| Weak | -28.667 | 1.329 | brown | upper | mm | - |
| Marginal | -23.333 | 2.669 | orange | upper | mm | - |
| Adequate | -18 | 4 | yellow | upper | mm | - |
| Good | -18 | 4 | green | lower | mm | - |

## `criterion_driver/criterion_chest/criterion_chest_vc` — Chest VC

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_VC` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?1VCCR000[03]??VEX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 0.5 | 4 | green | upper | m/s | - |
| Adequate | 0.5 | 4 | yellow | lower | m/s | - |
| Marginal | 0.667 | 2.669 | orange | lower | m/s | - |
| Weak | 0.833 | 1.329 | brown | lower | m/s | - |
| Poor | 1 | 0 | red | — | m/s | - |
| Capping | 1 | -inf | gray | lower | m/s | - |

## `criterion_driver/criterion_chest/criterion_shoulder_belt_load` — Modifier Shoulder Belt Load

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_ShoulderBeltLoad` | §TODO full-width frontal (inherited) | 0 (from limits) | — |

Limits for `?1SEBE????B3FO[X0]?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| 0 pt. Modifier | 6 | 0 | green | upper | kN | - |
| -2 pt. Modifier | 6 | -2 | red | lower | kN | - |

## `criterion_driver/criterion_femur` — Femur

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur` | §TODO full-width frontal (inherited) | 4 | — |

## `criterion_driver/criterion_femur/criterion_femur_axial_force` — Femur Axial Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Axial_Force` | §TODO full-width frontal (inherited) | — | — |

## `criterion_driver/criterion_femur/criterion_femur_axial_force/criterion_femur_axial_force_left` — Femur Axial Force Left

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Axial_Force_Left` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?1FEMRLE00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -2.6 | 4 | green | lower | kN | - |
| Adequate | -2.6 | 4 | yellow | upper | kN | - |
| Marginal | -3.8 | 2.669 | orange | upper | kN | - |
| Weak | -5 | 1.329 | brown | upper | kN | - |
| Poor | -6.2 | 0 | red | upper | kN | - |

## `criterion_driver/criterion_femur/criterion_femur_axial_force/criterion_femur_axial_force_right` — Femur Axial Force Right

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Axial_Force_Right` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?1FEMRRI00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -2.6 | 4 | green | lower | kN | - |
| Adequate | -2.6 | 4 | yellow | upper | kN | - |
| Marginal | -3.8 | 2.669 | orange | upper | kN | - |
| Weak | -5 | 1.329 | brown | upper | kN | - |
| Poor | -6.2 | 0 | red | upper | kN | - |

## `criterion_driver/criterion_femur/criterion_submarining` — Submarining

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Submarining` | §TODO full-width frontal (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| submarining | bool | False | — | video | Pelvis slid under the lap belt. Caps the femur box at 0 points. |

## `criterion_driver/criterion_head` — Head

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head` | §TODO head | 4 | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| hard_contact | bool | True | — | video | Was hard head contact observed? A head-acceleration peak above 80 g forces this to True regardless (Appendix A2: 'video OR curve'). |

## `criterion_driver/criterion_head/criterion_DisplacementSteeringColumn` — Modifier for Displacement of Steering Column

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_DisplacementSteeringColumn` | §TODO head (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| displacement_steering_column_lateral | float | 0 | mm | measurement | Lateral displacement of the steering column (limit 100 mm). |
| displacement_steering_column_rearwards | float | 0 | mm | measurement | Rearward displacement of the steering column (limit 100 mm). |
| displacement_steering_column_upwards | float | 0 | mm | measurement | Upward displacement of the steering column (limit 80 mm). |

## `criterion_driver/criterion_head/criterion_ExceedingForwardExcursionLine` — Modifier for Exceeding forward excursion line

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_ExceedingForwardExcursionLine` | §TODO head (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| forward_excursion | float | 0 | mm | video | Forward head excursion beyond the excursion line. |
| simulation_contact_seat_H3 | bool | False | — | simulation | Hybrid-III simulation shows head contact with the front seat. |
| simulation_hic_15_H3 | float | 0 | — | simulation | HIC15 from the Hybrid-III simulation. |

## `criterion_driver/criterion_head/criterion_HazardousAirbagDeployment` — Modifier for Hazardous Airbag Deployment

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HazardousAirbagDeployment` | §TODO head (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| hazardous_airbag_deployment | bool | False | — | video | Hazardous airbag deployment observed. −1 point. |

## `criterion_driver/criterion_head/criterion_IncorrectAirbagDeployment` — Modifier for Incorrect Airbag Deployment

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_IncorrectAirbagDeployment` | §TODO head (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| incorrect_airbag_deployment | bool | False | — | video | Incorrect airbag deployment observed. −1 point. |

## `criterion_driver/criterion_head/criterion_UnstableAirbagSteeringWheelContact` — Modifier for Unstable airbag/steering wheel contact

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_UnstableAirbagSteeringWheelContact` | §TODO head (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| unstable_airbag_steering_wheel_contact | bool | False | — | video | Unstable contact between head and airbag/steering wheel. −1 point. |

## `criterion_driver/criterion_head/criterion_head_a3ms` — Head a3ms

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_a3ms` | §TODO head (inherited) | 4 (from limits) | — |

Limits for `?1HEAD003C??ACR?`, `?1HEADCG3C??ACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 72 | 4 | green | upper | g0 | - |
| Adequate | 72 | 4 | yellow | lower | g0 | - |
| Marginal | 74.667 | 2.669 | orange | lower | g0 | - |
| Weak | 77.333 | 1.329 | brown | lower | g0 | - |
| Poor | 80 | 0 | red | — | g0 | - |
| Capping | 80 | -inf | gray | lower | g0 | - |

## `criterion_driver/criterion_head/criterion_hic_15` — HIC 15

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HIC_15` | §TODO head (inherited) | 4 (from limits) | — |

Limits for `?1HICR0015??00RX`, `?1HICRCG15??00RX`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 500 | 4 | green | upper | 1 | - |
| Adequate | 500 | 4 | yellow | lower | 1 | - |
| Marginal | 566.667 | 2.669 | orange | lower | 1 | - |
| Weak | 633.333 | 1.329 | brown | lower | 1 | - |
| Poor | 700 | 0 | red | — | 1 | - |
| Capping | 700 | -inf | gray | lower | 1 | - |

## `criterion_driver/criterion_neck` — Neck

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck` | §TODO full-width frontal (inherited) | 4 | — |

## `criterion_driver/criterion_neck/criterion_fx_shear` — Neck Fx shear

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Fx_shear` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?1NECKUP00??FOX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 1.2 | 4 | green | upper | kN | - |
| Adequate | 1.2 | 4 | yellow | lower | kN | - |
| Marginal | 1.45 | 2.669 | orange | lower | kN | - |
| Weak | 1.7 | 1.329 | brown | lower | kN | - |
| Poor | 1.95 | 0 | red | lower | kN | - |
| Good | -1.2 | 4 | green | lower | kN | - |
| Adequate | -1.2 | 4 | yellow | upper | kN | - |
| Marginal | -1.45 | 2.669 | orange | upper | kN | - |
| Weak | -1.7 | 1.329 | brown | upper | kN | - |
| Poor | -1.95 | 0 | red | upper | kN | - |
| Capping | 2.7 | -inf | gray | lower | kN | - |
| Capping | -2.7 | -inf | gray | upper | kN | - |

## `criterion_driver/criterion_neck/criterion_fz_tension` — Neck Fz tension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Fz_tension` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?1NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 1.7 | 4 | green | upper | kN | - |
| Adequate | 1.7 | 4 | yellow | lower | kN | - |
| Marginal | 2.007 | 2.669 | orange | lower | kN | - |
| Weak | 2.313 | 1.329 | brown | lower | kN | - |
| Poor | 2.62 | 0 | red | lower | kN | - |
| Capping | 2.9 | -inf | gray | lower | kN | - |

## `criterion_driver/criterion_neck/criterion_my_extension` — Neck My extension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_My_extension` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?1NECKUP00??MOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -36 | 4 | green | lower | Nm | - |
| Adequate | -36 | 4 | yellow | upper | Nm | - |
| Marginal | -40.333 | 2.669 | orange | upper | Nm | - |
| Weak | -44.667 | 1.329 | brown | upper | Nm | - |
| Poor | -49 | 0 | red | upper | Nm | - |
| Capping | -57 | -inf | gray | upper | Nm | - |

## `criterion_front_passenger` — Front Passenger

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Front_Passenger` | §TODO full-width frontal (inherited) | — | — |

## `criterion_front_passenger/criterion_chest` — Chest

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest` | §TODO full-width frontal (inherited) | — | — |

## `criterion_front_passenger/criterion_chest/criterion_chest_deflection` — Chest Deflection

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Deflection` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?3CHST000[03]??DSX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Capping | -34 | -inf | gray | upper | mm | - |
| Poor | -34 | 0 | red | — | mm | - |
| Weak | -28.667 | 1.329 | brown | upper | mm | - |
| Marginal | -23.333 | 2.669 | orange | upper | mm | - |
| Adequate | -18 | 4 | yellow | upper | mm | - |
| Good | -18 | 4 | green | lower | mm | - |

## `criterion_front_passenger/criterion_chest/criterion_chest_vc` — Chest VC

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_VC` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?3VCCR000[03]??VEX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 0.5 | 4 | green | upper | m/s | - |
| Adequate | 0.5 | 4 | yellow | lower | m/s | - |
| Marginal | 0.667 | 2.669 | orange | lower | m/s | - |
| Weak | 0.833 | 1.329 | brown | lower | m/s | - |
| Poor | 1 | 0 | red | — | m/s | - |
| Capping | 1 | -inf | gray | lower | m/s | - |

## `criterion_front_passenger/criterion_chest/criterion_shoulder_belt_load` — Modifier Shoulder Belt Load

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_ShoulderBeltLoad` | §TODO full-width frontal (inherited) | 0 (from limits) | — |

Limits for `?3SEBE????B3FO[X0]?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| 0 pt. Modifier | 6 | 0 | green | upper | kN | - |
| -2 pt. Modifier | 6 | -2 | red | lower | kN | - |

## `criterion_front_passenger/criterion_femur` — Femur

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur` | §TODO full-width frontal (inherited) | — | — |

## `criterion_front_passenger/criterion_femur/criterion_femur_axial_force` — Femur Axial Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Axial_Force` | §TODO full-width frontal (inherited) | — | — |

## `criterion_front_passenger/criterion_femur/criterion_femur_axial_force/criterion_femur_axial_force_left` — Femur Axial Force Left

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Axial_Force_Left` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?3FEMRLE00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -2.6 | 4 | green | lower | kN | - |
| Adequate | -2.6 | 4 | yellow | upper | kN | - |
| Marginal | -3.8 | 2.669 | orange | upper | kN | - |
| Weak | -5 | 1.329 | brown | upper | kN | - |
| Poor | -6.2 | 0 | red | upper | kN | - |

## `criterion_front_passenger/criterion_femur/criterion_femur_axial_force/criterion_femur_axial_force_right` — Femur Axial Force Right

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Axial_Force_Right` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?3FEMRRI00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -2.6 | 4 | green | lower | kN | - |
| Adequate | -2.6 | 4 | yellow | upper | kN | - |
| Marginal | -3.8 | 2.669 | orange | upper | kN | - |
| Weak | -5 | 1.329 | brown | upper | kN | - |
| Poor | -6.2 | 0 | red | upper | kN | - |

## `criterion_front_passenger/criterion_head` — Head

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head` | §TODO full-width frontal (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| hard_contact | bool | True | — | video | Was hard head contact observed? A head-acceleration peak above 80 g forces this to True regardless (Appendix A2: 'video OR curve'). |

## `criterion_front_passenger/criterion_head/criterion_ExceedingForwardExcursionLine` — Modifier for Exceeding forward excursion line

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_ExceedingForwardExcursionLine` | §TODO full-width frontal (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| forward_excursion | float | 0 | mm | video | Forward head excursion beyond the excursion line. |
| simulation_contact_seat_H3 | bool | False | — | simulation | Hybrid-III simulation shows head contact with the front seat. |
| simulation_hic_15_H3 | float | 0 | — | simulation | HIC15 from the Hybrid-III simulation. |

## `criterion_front_passenger/criterion_head/criterion_HazardousAirbagDeployment` — Modifier for Hazardous Airbag Deployment

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HazardousAirbagDeployment` | §TODO full-width frontal (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| hazardous_airbag_deployment | bool | False | — | video | Hazardous airbag deployment observed. −1 point. |

## `criterion_front_passenger/criterion_head/criterion_IncorrectAirbagDeployment` — Modifier for Incorrect Airbag Deployment

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_IncorrectAirbagDeployment` | §TODO full-width frontal (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| incorrect_airbag_deployment | bool | False | — | video | Incorrect airbag deployment observed. −1 point. |

## `criterion_front_passenger/criterion_head/criterion_head_a3ms` — Head a3ms

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_a3ms` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?3HEAD003C??ACR?`, `?3HEADCG3C??ACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 72 | 4 | green | upper | g0 | - |
| Adequate | 72 | 4 | yellow | lower | g0 | - |
| Marginal | 74.667 | 2.669 | orange | lower | g0 | - |
| Weak | 77.333 | 1.329 | brown | lower | g0 | - |
| Poor | 80 | 0 | red | — | g0 | - |
| Capping | 80 | -inf | gray | lower | g0 | - |

## `criterion_front_passenger/criterion_head/criterion_hic_15` — HIC 15

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HIC_15` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?3HICR0015??00RX`, `?3HICRCG15??00RX`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 500 | 4 | green | upper | 1 | - |
| Adequate | 500 | 4 | yellow | lower | 1 | - |
| Marginal | 566.667 | 2.669 | orange | lower | 1 | - |
| Weak | 633.333 | 1.329 | brown | lower | 1 | - |
| Poor | 700 | 0 | red | — | 1 | - |
| Capping | 700 | -inf | gray | lower | 1 | - |

## `criterion_front_passenger/criterion_neck` — Neck

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck` | §TODO full-width frontal (inherited) | — | — |

## `criterion_front_passenger/criterion_neck/criterion_fx_shear` — Neck Fx shear

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Fx_shear` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?3NECKUP00??FOX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 1.2 | 4 | green | upper | kN | - |
| Adequate | 1.2 | 4 | yellow | lower | kN | - |
| Marginal | 1.45 | 2.669 | orange | lower | kN | - |
| Weak | 1.7 | 1.329 | brown | lower | kN | - |
| Poor | 1.95 | 0 | red | lower | kN | - |
| Good | -1.2 | 4 | green | lower | kN | - |
| Adequate | -1.2 | 4 | yellow | upper | kN | - |
| Marginal | -1.45 | 2.669 | orange | upper | kN | - |
| Weak | -1.7 | 1.329 | brown | upper | kN | - |
| Poor | -1.95 | 0 | red | upper | kN | - |

## `criterion_front_passenger/criterion_neck/criterion_fz_tension` — Neck Fz tension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Fz_tension` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?3NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 1.7 | 4 | green | upper | kN | - |
| Adequate | 1.7 | 4 | yellow | lower | kN | - |
| Marginal | 2.007 | 2.669 | orange | lower | kN | - |
| Weak | 2.313 | 1.329 | brown | lower | kN | - |
| Poor | 2.62 | 0 | red | lower | kN | - |

## `criterion_front_passenger/criterion_neck/criterion_my_extension` — Neck My extension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_My_extension` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?3NECKUP00??MOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -36 | 4 | green | lower | Nm | - |
| Adequate | -36 | 4 | yellow | upper | Nm | - |
| Marginal | -40.333 | 2.669 | orange | upper | Nm | - |
| Weak | -44.667 | 1.329 | brown | upper | Nm | - |
| Poor | -49 | 0 | red | upper | Nm | - |

## `criterion_rear_passenger` — Rear Passenger

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Rear_Passenger` | §TODO full-width frontal (inherited) | — | — |

## `criterion_rear_passenger/criterion_chest` — Chest

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest` | §TODO full-width frontal (inherited) | — | — |

## `criterion_rear_passenger/criterion_chest/criterion_chest_deflection` — Chest Deflection

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Deflection` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?6CHST000[03]??DSX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Capping | -34 | -inf | gray | upper | mm | - |
| Poor | -34 | 0 | red | — | mm | - |
| Weak | -28.667 | 1.329 | brown | upper | mm | - |
| Marginal | -23.333 | 2.669 | orange | upper | mm | - |
| Adequate | -18 | 4 | yellow | upper | mm | - |
| Good | -18 | 4 | green | lower | mm | - |

## `criterion_rear_passenger/criterion_chest/criterion_chest_vc` — Chest VC

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_VC` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?6VCCR000[03]??VEX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 0.5 | 4 | green | upper | m/s | - |
| Adequate | 0.5 | 4 | yellow | lower | m/s | - |
| Marginal | 0.667 | 2.669 | orange | lower | m/s | - |
| Weak | 0.833 | 1.329 | brown | lower | m/s | - |
| Poor | 1 | 0 | red | — | m/s | - |
| Capping | 1 | -inf | gray | lower | m/s | - |

## `criterion_rear_passenger/criterion_chest/criterion_shoulder_belt_load` — Modifier Shoulder Belt Load

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_ShoulderBeltLoad` | §TODO full-width frontal (inherited) | 0 (from limits) | — |

Limits for `?6SEBE????B3FO[X0]?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| 0 pt. Modifier | 6 | 0 | green | upper | kN | - |
| -2 pt. Modifier | 6 | -2 | red | lower | kN | - |

## `criterion_rear_passenger/criterion_femur` — Femur

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur` | §TODO full-width frontal (inherited) | — | — |

## `criterion_rear_passenger/criterion_femur/criterion_femur_axial_force` — Femur Axial Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Axial_Force` | §TODO full-width frontal (inherited) | — | — |

## `criterion_rear_passenger/criterion_femur/criterion_femur_axial_force/criterion_femur_axial_force_left` — Femur Axial Force Left

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Axial_Force_Left` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?6FEMRLE00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -2.6 | 4 | green | lower | kN | - |
| Adequate | -2.6 | 4 | yellow | upper | kN | - |
| Marginal | -3.8 | 2.669 | orange | upper | kN | - |
| Weak | -5 | 1.329 | brown | upper | kN | - |
| Poor | -6.2 | 0 | red | upper | kN | - |

## `criterion_rear_passenger/criterion_femur/criterion_femur_axial_force/criterion_femur_axial_force_right` — Femur Axial Force Right

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Axial_Force_Right` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?6FEMRRI00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -2.6 | 4 | green | lower | kN | - |
| Adequate | -2.6 | 4 | yellow | upper | kN | - |
| Marginal | -3.8 | 2.669 | orange | upper | kN | - |
| Weak | -5 | 1.329 | brown | upper | kN | - |
| Poor | -6.2 | 0 | red | upper | kN | - |

## `criterion_rear_passenger/criterion_femur/criterion_submarining` — Submarining

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Submarining` | §TODO full-width frontal (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| submarining | bool | False | — | video | Pelvis slid under the lap belt. Caps the femur box at 0 points. |

## `criterion_rear_passenger/criterion_head` — Head

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head` | §TODO full-width frontal (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| hard_contact | bool | True | — | video | Was hard head contact observed? A head-acceleration peak above 80 g forces this to True regardless (Appendix A2: 'video OR curve'). |

## `criterion_rear_passenger/criterion_head/criterion_ExceedingForwardExcursionLine` — Modifier for Exceeding forward excursion line

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_ExceedingForwardExcursionLine` | §TODO full-width frontal (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| forward_excursion | float | 0 | mm | video | Forward head excursion beyond the excursion line. |
| simulation_contact_seat_H3 | bool | False | — | simulation | Hybrid-III simulation shows head contact with the front seat. |
| simulation_hic_15_H3 | float | 0 | — | simulation | HIC15 from the Hybrid-III simulation. |

## `criterion_rear_passenger/criterion_head/criterion_HazardousAirbagDeployment` — Modifier for Hazardous Airbag Deployment

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HazardousAirbagDeployment` | §TODO full-width frontal (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| hazardous_airbag_deployment | bool | False | — | video | Hazardous airbag deployment observed. −1 point. |

## `criterion_rear_passenger/criterion_head/criterion_IncorrectAirbagDeployment` — Modifier for Incorrect Airbag Deployment

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_IncorrectAirbagDeployment` | §TODO full-width frontal (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| incorrect_airbag_deployment | bool | False | — | video | Incorrect airbag deployment observed. −1 point. |

## `criterion_rear_passenger/criterion_head/criterion_head_a3ms` — Head a3ms

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_a3ms` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?6HEAD003C??ACR?`, `?6HEADCG3C??ACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 72 | 4 | green | upper | g0 | - |
| Adequate | 72 | 4 | yellow | lower | g0 | - |
| Marginal | 74.667 | 2.669 | orange | lower | g0 | - |
| Weak | 77.333 | 1.329 | brown | lower | g0 | - |
| Poor | 80 | 0 | red | — | g0 | - |
| Capping | 80 | -inf | gray | lower | g0 | - |

## `criterion_rear_passenger/criterion_head/criterion_hic_15` — HIC 15

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HIC_15` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?6HICR0015??00RX`, `?6HICRCG15??00RX`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 500 | 4 | green | upper | 1 | - |
| Adequate | 500 | 4 | yellow | lower | 1 | - |
| Marginal | 566.667 | 2.669 | orange | lower | 1 | - |
| Weak | 633.333 | 1.329 | brown | lower | 1 | - |
| Poor | 700 | 0 | red | — | 1 | - |
| Capping | 700 | -inf | gray | lower | 1 | - |

## `criterion_rear_passenger/criterion_neck` — Neck

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck` | §TODO full-width frontal (inherited) | — | — |

## `criterion_rear_passenger/criterion_neck/criterion_fx_shear` — Neck Fx shear

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Fx_shear` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?6NECKUP00??FOX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 1.2 | 4 | green | upper | kN | - |
| Adequate | 1.2 | 4 | yellow | lower | kN | - |
| Marginal | 1.45 | 2.669 | orange | lower | kN | - |
| Weak | 1.7 | 1.329 | brown | lower | kN | - |
| Poor | 1.95 | 0 | red | lower | kN | - |
| Good | -1.2 | 4 | green | lower | kN | - |
| Adequate | -1.2 | 4 | yellow | upper | kN | - |
| Marginal | -1.45 | 2.669 | orange | upper | kN | - |
| Weak | -1.7 | 1.329 | brown | upper | kN | - |
| Poor | -1.95 | 0 | red | upper | kN | - |

## `criterion_rear_passenger/criterion_neck/criterion_fz_tension` — Neck Fz tension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Fz_tension` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?6NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 1.7 | 4 | green | upper | kN | - |
| Adequate | 1.7 | 4 | yellow | lower | kN | - |
| Marginal | 2.007 | 2.669 | orange | lower | kN | - |
| Weak | 2.313 | 1.329 | brown | lower | kN | - |
| Poor | 2.62 | 0 | red | lower | kN | - |

## `criterion_rear_passenger/criterion_neck/criterion_my_extension` — Neck My extension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_My_extension` | §TODO full-width frontal (inherited) | 4 (from limits) | — |

Limits for `?6NECKUP00??MOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -36 | 4 | green | lower | Nm | - |
| Adequate | -36 | 4 | yellow | upper | Nm | - |
| Marginal | -40.333 | 2.669 | orange | upper | Nm | - |
| Weak | -44.667 | 1.329 | brown | upper | Nm | - |
| Poor | -49 | 0 | red | upper | Nm | - |
