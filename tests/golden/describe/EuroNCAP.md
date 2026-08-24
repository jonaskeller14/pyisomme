# EuroNCAP

## `frontal_50kmh` — Euro NCAP | Frontal-Impact against Rigid Wall with 100 % Overlap at 50 km/h

# EuroNCAP_Frontal_50kmh

| property | value |
| --- | --- |
| name | Euro NCAP \| Frontal-Impact against Rigid Wall with 100 % Overlap at 50 km/h |
| protocol | 9.3 |
| protocols | 9.3 |
| overall criterion | `Overall` |
| available_pages | Page_Cover, Page_Rating_Table, Page_Driver_Result_Values_Chart, Page_Driver_Rating_Table, Page_Driver_Values_Table, Page_Driver_Belt, Page_Driver_Head_Acceleration, Page_Driver_HIC15, Page_Driver_Neck_Load, Page_Driver_Neck_NIJ, Page_Driver_Chest_Deflection, Page_Driver_Femur_Axial_Force, Page_Front_Passenger_Result_Values_Chart, Page_Front_Passenger_Rating_Table, Page_Front_Passenger_Values_Table, Page_Front_Passenger_Belt, Page_Front_Passenger_Head_Acceleration, Page_Front_Passenger_HIC15, Page_Front_Passenger_Neck_Load, Page_Front_Passenger_Neck_NIJ, Page_Front_Passenger_Chest_Deflection, Page_Front_Passenger_Femur_Axial_Force, Page_Rear_Passenger_Result_Values_Chart, Page_Rear_Passenger_Rating_Table, Page_Rear_Passenger_Values_Table, Page_Rear_Passenger_Belt, Page_Rear_Passenger_Head_Acceleration, Page_Rear_Passenger_HIC15, Page_Rear_Passenger_Neck_Load, Page_Rear_Passenger_Chest_Deflection, Page_Rear_Passenger_Femur_Axial_Force, Page_OLC |
| selected_pages | Page_Cover, Page_Rating_Table, Page_Driver_Result_Values_Chart, Page_Driver_Rating_Table, Page_Driver_Values_Table, Page_Driver_Belt, Page_Driver_Head_Acceleration, Page_Driver_HIC15, Page_Driver_Neck_Load, Page_Driver_Neck_NIJ, Page_Driver_Chest_Deflection, Page_Driver_Femur_Axial_Force, Page_Front_Passenger_Result_Values_Chart, Page_Front_Passenger_Rating_Table, Page_Front_Passenger_Values_Table, Page_Front_Passenger_Belt, Page_Front_Passenger_Head_Acceleration, Page_Front_Passenger_HIC15, Page_Front_Passenger_Neck_Load, Page_Front_Passenger_Neck_NIJ, Page_Front_Passenger_Chest_Deflection, Page_Front_Passenger_Femur_Axial_Force, Page_Rear_Passenger_Result_Values_Chart, Page_Rear_Passenger_Rating_Table, Page_Rear_Passenger_Values_Table, Page_Rear_Passenger_Belt, Page_Rear_Passenger_Head_Acceleration, Page_Rear_Passenger_HIC15, Page_Rear_Passenger_Neck_Load, Page_Rear_Passenger_Chest_Deflection, Page_Rear_Passenger_Femur_Axial_Force, Page_OLC |

## `Overall` — Overall

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Overall` | §4 | 8 | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| front_passenger_meets_90_percent | bool | True | — | test report | Does the manufacturer-provided front-passenger dummy score reach 90 % of the driver's total (§4.3)? When it does not, every front-row body region is assessed on the worse of driver and front passenger. |
| p_driver | str | '1' | — | test report | Channel-code position of the driver. Defaults to the 'Driver position object 1' test-info field when the test carries it. |
| p_front_passenger | str | '3' | — | test report | Channel-code position of the front passenger. Derived from p_driver ('1' for a right-hand-drive test) unless set explicitly. |
| p_rear_passenger | str | '6' | — | test report | Channel-code position of the rear passenger. Derived from p_driver ('4' for a right-hand-drive test) unless set explicitly. |

## `criterion_driver` — Driver

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Driver` | §4 (inherited) | 16 | sum |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| steering_wheel_airbag_exists | bool | True | — | test report | Is a steering-wheel airbag fitted? Without one the head and neck boxes score 0. |

## `criterion_driver/criterion_head` — Head

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head` | §4.1.1 | 4 | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| hard_contact | bool | True | — | video | Was hard head contact observed? A head-acceleration peak above 80 g forces this to True regardless (Appendix A2: 'video OR curve'). |

## `criterion_driver/criterion_head/criterion_hic_15` — HIC 15

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HIC_15` | §4.1.1 (inherited) | 4 (from limits) | — |

Limits for `?1HICR0015??00RX`, `?1HICRCG15??00RX`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 500 | 4 | green | upper | 1 | - |
| Adequate | 500 | 4 | yellow | lower | 1 | - |
| Marginal | 566.667 | 2.669 | orange | lower | 1 | - |
| Weak | 633.333 | 1.329 | brown | lower | 1 | - |
| Poor | 700 | 0 | red | — | 1 | - |
| Capping | 700 | -inf | gray | lower | 1 | - |

## `criterion_driver/criterion_head/criterion_head_a3ms` — Head a3ms

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_a3ms` | §4.1.1 (inherited) | 4 (from limits) | — |

Limits for `?1HEAD003C??ACR?`, `?1HEADCG3C??ACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 72 | 4 | green | upper | g0 | - |
| Adequate | 72 | 4 | yellow | lower | g0 | - |
| Marginal | 74.667 | 2.669 | orange | lower | g0 | - |
| Weak | 77.333 | 1.329 | brown | lower | g0 | - |
| Poor | 80 | 0 | red | — | g0 | - |
| Capping | 80 | -inf | gray | lower | g0 | - |

## `criterion_driver/criterion_head/criterion_UnstableAirbagContact` — Modifier for Unstable Airbag Contact

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_UnstableAirbagContact` | §4.2.1 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| unstable_airbag_contact | bool | False | — | video | During the head's forward movement its centre of gravity moved further than the outside edge of the airbag, or head protection by the airbag was otherwise compromised — steering wheel detached from the column, airbag bottomed out by the head. −1 point. |

## `criterion_driver/criterion_head/criterion_HazardousAirbagDeployment` — Modifier for Hazardous Airbag Deployment

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HazardousAirbagDeployment` | §4.2.1 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| hazardous_airbag_deployment | bool | False | — | video | Hazardous airbag deployment observed. −1 point. |

## `criterion_driver/criterion_head/criterion_IncorrectAirbagDeployment` — Modifier for Incorrect Airbag Deployment

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_IncorrectAirbagDeployment` | §4.2.1 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| incorrect_airbag_deployment | bool | False | — | video | Incorrect airbag deployment observed. −1 point. |

## `criterion_driver/criterion_head/criterion_DisplacementSteeringColumn` — Modifier for Displacement of Steering Column

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_DisplacementSteeringColumn` | §4.2.1 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| displacement_steering_column_lateral | float | 0 | mm | measurement | Lateral displacement of the steering column (limit 100 mm). |
| displacement_steering_column_rearwards | float | 0 | mm | measurement | Rearward displacement of the steering column (limit 100 mm). |
| displacement_steering_column_upwards | float | 0 | mm | measurement | Upward displacement of the steering column (limit 80 mm). |

## `criterion_driver/criterion_neck` — Neck

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck` | §4.1.2 | 4 | — |

## `criterion_driver/criterion_neck/criterion_my_extension` — Neck My extension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_My_extension` | §4.1.2 (inherited) | 4 (from limits) | — |

Limits for `?1NECKUP00??MOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -36 | 4 | green | lower | Nm | - |
| Adequate | -36 | 4 | yellow | upper | Nm | - |
| Marginal | -40.333 | 2.669 | orange | upper | Nm | - |
| Weak | -44.667 | 1.329 | brown | upper | Nm | - |
| Poor | -49 | 0 | red | upper | Nm | - |
| Capping | -57 | -inf | gray | upper | Nm | - |

## `criterion_driver/criterion_neck/criterion_fz_tension` — Neck Fz tension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Fz_tension` | §4.1.2 (inherited) | 4 (from limits) | — |

Limits for `?1NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 1.7 | 4 | green | upper | kN | - |
| Adequate | 1.7 | 4 | yellow | lower | kN | - |
| Marginal | 2.007 | 2.669 | orange | lower | kN | - |
| Weak | 2.313 | 1.329 | brown | lower | kN | - |
| Poor | 2.62 | 0 | red | lower | kN | - |
| Capping | 2.9 | -inf | gray | lower | kN | - |

## `criterion_driver/criterion_neck/criterion_fx_shear` — Neck Fx shear

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Fx_shear` | §4.1.2 (inherited) | 4 (from limits) | — |

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

## `criterion_driver/criterion_chest` — Chest

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest` | §4.1.3 | 4 | — |

## `criterion_driver/criterion_chest/criterion_chest_deflection` — Chest Deflection

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Deflection` | §4.1.3 (inherited) | 4 (from limits) | — |

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
| `Criterion_Chest_VC` | §4.1.3 (inherited) | 4 (from limits) | — |

Limits for `?1VCCR000[03]??VEX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 0.5 | 4 | green | upper | m/s | - |
| Adequate | 0.5 | 4 | yellow | lower | m/s | - |
| Marginal | 0.667 | 2.669 | orange | lower | m/s | - |
| Weak | 0.833 | 1.329 | brown | lower | m/s | - |
| Poor | 1 | 0 | red | — | m/s | - |
| Capping | 1 | -inf | gray | lower | m/s | - |

## `criterion_driver/criterion_chest/criterion_SteeringWheelContact` — Modifier Chest Steering Wheel Contact

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_SteeringWheelContact` | §4.2.2 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| steering_wheel_contact | bool | False | — | video | Chest contact with the steering wheel (driver only). −1 point. |

## `criterion_driver/criterion_chest/criterion_shoulder_belt_load` — Modifier Shoulder Belt Load

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_ShoulderBeltLoad` | §4.1.3 (inherited) | 0 (from limits) | — |

Limits for `?1SEBE????B3FO[X0]?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| 0 pt. Modifier | 6 | 0 | green | upper | kN | - |
| -2 pt. Modifier | 6 | -2 | red | lower | kN | - |

## `criterion_driver/criterion_femur` — Femur

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur` | §4.1.4 | 4 | — |

## `criterion_driver/criterion_femur/criterion_femur_axial_force` — Femur Axial Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Axial_Force` | §4.1.4 (inherited) | — | — |

## `criterion_driver/criterion_femur/criterion_femur_axial_force/criterion_femur_axial_force_left` — Femur Axial Force Left

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Axial_Force_Left` | §4.1.4 (inherited) | 4 (from limits) | — |

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
| `Criterion_Femur_Axial_Force_Right` | §4.1.4 (inherited) | 4 (from limits) | — |

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
| `Criterion_Submarining` | §4.1.4 (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| submarining | bool | False | — | video | Pelvis slid under the lap belt. Caps the femur box at 0 points. |

## `criterion_front_passenger` — Front Passenger

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Front_Passenger` | §4 (inherited) | 16 | sum |

## `criterion_front_passenger/criterion_head` — Head

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head` | §4.1.1 | 4 | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| hard_contact | bool | True | — | video | Was hard head contact observed? A head-acceleration peak above 80 g forces this to True regardless (Appendix A2: 'video OR curve'). |

## `criterion_front_passenger/criterion_head/criterion_hic_15` — HIC 15

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HIC_15` | §4.1.1 (inherited) | 4 (from limits) | — |

Limits for `?3HICR0015??00RX`, `?3HICRCG15??00RX`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 500 | 4 | green | upper | 1 | - |
| Adequate | 500 | 4 | yellow | lower | 1 | - |
| Marginal | 566.667 | 2.669 | orange | lower | 1 | - |
| Weak | 633.333 | 1.329 | brown | lower | 1 | - |
| Poor | 700 | 0 | red | — | 1 | - |
| Capping | 700 | -inf | gray | lower | 1 | - |

## `criterion_front_passenger/criterion_head/criterion_head_a3ms` — Head a3ms

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_a3ms` | §4.1.1 (inherited) | 4 (from limits) | — |

Limits for `?3HEAD003C??ACR?`, `?3HEADCG3C??ACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 72 | 4 | green | upper | g0 | - |
| Adequate | 72 | 4 | yellow | lower | g0 | - |
| Marginal | 74.667 | 2.669 | orange | lower | g0 | - |
| Weak | 77.333 | 1.329 | brown | lower | g0 | - |
| Poor | 80 | 0 | red | — | g0 | - |
| Capping | 80 | -inf | gray | lower | g0 | - |

## `criterion_front_passenger/criterion_head/criterion_HazardousAirbagDeployment` — Modifier for Hazardous Airbag Deployment

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HazardousAirbagDeployment` | §4.2.1 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| hazardous_airbag_deployment | bool | False | — | video | Hazardous airbag deployment observed. −1 point. |

## `criterion_front_passenger/criterion_head/criterion_IncorrectAirbagDeployment` — Modifier for Incorrect Airbag Deployment

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_IncorrectAirbagDeployment` | §4.2.1 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| incorrect_airbag_deployment | bool | False | — | video | Incorrect airbag deployment observed. −1 point. |

## `criterion_front_passenger/criterion_neck` — Neck

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck` | §4.1.2 | 4 | — |

## `criterion_front_passenger/criterion_neck/criterion_my_extension` — Neck My extension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_My_extension` | §4.1.2 (inherited) | 4 (from limits) | — |

Limits for `?3NECKUP00??MOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -36 | 4 | green | lower | Nm | - |
| Adequate | -36 | 4 | yellow | upper | Nm | - |
| Marginal | -40.333 | 2.669 | orange | upper | Nm | - |
| Weak | -44.667 | 1.329 | brown | upper | Nm | - |
| Poor | -49 | 0 | red | upper | Nm | - |

## `criterion_front_passenger/criterion_neck/criterion_fz_tension` — Neck Fz tension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Fz_tension` | §4.1.2 (inherited) | 4 (from limits) | — |

Limits for `?3NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 1.7 | 4 | green | upper | kN | - |
| Adequate | 1.7 | 4 | yellow | lower | kN | - |
| Marginal | 2.007 | 2.669 | orange | lower | kN | - |
| Weak | 2.313 | 1.329 | brown | lower | kN | - |
| Poor | 2.62 | 0 | red | lower | kN | - |

## `criterion_front_passenger/criterion_neck/criterion_fx_shear` — Neck Fx shear

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Fx_shear` | §4.1.2 (inherited) | 4 (from limits) | — |

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

## `criterion_front_passenger/criterion_chest` — Chest

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest` | §4.1.3 | 4 | — |

## `criterion_front_passenger/criterion_chest/criterion_chest_deflection` — Chest Deflection

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Deflection` | §4.1.3 (inherited) | 4 (from limits) | — |

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
| `Criterion_Chest_VC` | §4.1.3 (inherited) | 4 (from limits) | — |

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
| `Criterion_ShoulderBeltLoad` | §4.1.3 (inherited) | 0 (from limits) | — |

Limits for `?3SEBE????B3FO[X0]?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| 0 pt. Modifier | 6 | 0 | green | upper | kN | - |
| -2 pt. Modifier | 6 | -2 | red | lower | kN | - |

## `criterion_front_passenger/criterion_femur` — Femur

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur` | §4.1.4 | 4 | — |

## `criterion_front_passenger/criterion_femur/criterion_femur_axial_force` — Femur Axial Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Axial_Force` | §4.1.4 (inherited) | — | — |

## `criterion_front_passenger/criterion_femur/criterion_femur_axial_force/criterion_femur_axial_force_left` — Femur Axial Force Left

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Axial_Force_Left` | §4.1.4 (inherited) | 4 (from limits) | — |

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
| `Criterion_Femur_Axial_Force_Right` | §4.1.4 (inherited) | 4 (from limits) | — |

Limits for `?3FEMRRI00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -2.6 | 4 | green | lower | kN | - |
| Adequate | -2.6 | 4 | yellow | upper | kN | - |
| Marginal | -3.8 | 2.669 | orange | upper | kN | - |
| Weak | -5 | 1.329 | brown | upper | kN | - |
| Poor | -6.2 | 0 | red | upper | kN | - |

## `criterion_rear_passenger` — Rear Passenger

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Rear_Passenger` | §4 (inherited) | 16 | sum |

## `criterion_rear_passenger/criterion_head` — Head

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head` | §4.1.1.3 | 4 | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| hard_contact | bool | True | — | video | Was hard head contact seen on the high speed film? §4.1.1.3 has no 80 g rule for the rear passenger, so this input alone decides. Without contact only the 3 ms resultant is scored. |

## `criterion_rear_passenger/criterion_head/criterion_hic_15` — HIC 15

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HIC_15` | §4.1.1.3 (inherited) | 4 (from limits) | — |

Limits for `?6HICR0015??00RX`, `?6HICRCG15??00RX`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 500 | 4 | green | upper | 1 | - |
| Adequate | 500 | 4 | yellow | lower | 1 | - |
| Marginal | 566.667 | 2.669 | orange | lower | 1 | - |
| Weak | 633.333 | 1.329 | brown | lower | 1 | - |
| Poor | 700 | 0 | red | — | 1 | - |
| Capping | 700 | -inf | gray | lower | 1 | - |

## `criterion_rear_passenger/criterion_head/criterion_head_a3ms` — Head a3ms

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_a3ms` | §4.1.1.3 (inherited) | 4 (from limits) | — |

Limits for `?6HEAD003C??ACR?`, `?6HEADCG3C??ACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 72 | 4 | green | upper | g0 | - |
| Adequate | 72 | 4 | yellow | lower | g0 | - |
| Marginal | 74.667 | 2.669 | orange | lower | g0 | - |
| Weak | 77.333 | 1.329 | brown | lower | g0 | - |
| Poor | 80 | 0 | red | — | g0 | - |
| Capping | 80 | -inf | gray | lower | g0 | - |

## `criterion_rear_passenger/criterion_head/criterion_UnstableAirbagContact` — Modifier for Unstable Airbag Contact

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_UnstableAirbagContact` | §4.2.1 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| unstable_airbag_contact | bool | False | — | video | During the head's forward movement its centre of gravity moved further than the outside edge of the airbag, or head protection by the airbag was otherwise compromised — steering wheel detached from the column, airbag bottomed out by the head. −1 point. |

## `criterion_rear_passenger/criterion_head/criterion_HazardousAirbagDeployment` — Modifier for Hazardous Airbag Deployment

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HazardousAirbagDeployment` | §4.2.1 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| hazardous_airbag_deployment | bool | False | — | video | Hazardous airbag deployment observed. −1 point. |

## `criterion_rear_passenger/criterion_head/criterion_IncorrectAirbagDeployment` — Modifier for Incorrect Airbag Deployment

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_IncorrectAirbagDeployment` | §4.2.1 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| incorrect_airbag_deployment | bool | False | — | video | Incorrect airbag deployment observed. −1 point. |

## `criterion_rear_passenger/criterion_head/criterion_ExceedingForwardExcursionLine` — Modifier for Exceeding forward excursion line

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_ExceedingForwardExcursionLine` | §4.2.1 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| forward_excursion | float | 0 | mm | video | Forward head excursion beyond the excursion line. |
| simulation_contact_seat_H3 | bool | False | — | simulation | Hybrid-III simulation shows head contact with the front seat. |
| simulation_hic_15_H3 | float | 0 | — | simulation | HIC15 from the Hybrid-III simulation. |

## `criterion_rear_passenger/criterion_neck` — Neck

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck` | §4.1.2 | 4 | sum |

## `criterion_rear_passenger/criterion_neck/criterion_my_extension` — Neck My extension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_My_extension` | §4.1.2 (inherited) | 2 | — |

Limits for `?6NECKUP00??MOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | -36 | 4 | green | lower | Nm | - |
| Adequate | -36 | 4 | yellow | upper | Nm | - |
| Marginal | -40.333 | 2.669 | orange | upper | Nm | - |
| Weak | -44.667 | 1.329 | brown | upper | Nm | - |
| Poor | -49 | 0 | red | upper | Nm | - |

## `criterion_rear_passenger/criterion_neck/criterion_fz_tension` — Neck Fz tension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Fz_tension` | §4.1.2 (inherited) | 1 | — |

Limits for `?6NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 1.7 | 4 | green | upper | kN | - |
| Adequate | 1.7 | 4 | yellow | lower | kN | - |
| Marginal | 2.007 | 2.669 | orange | lower | kN | - |
| Weak | 2.313 | 1.329 | brown | lower | kN | - |
| Poor | 2.62 | 0 | red | lower | kN | - |

## `criterion_rear_passenger/criterion_neck/criterion_fx_shear` — Neck Fx shear

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Fx_shear` | §4.1.2 (inherited) | 1 | — |

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

## `criterion_rear_passenger/criterion_chest` — Chest

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest` | §4.1.3 | 4 | — |

## `criterion_rear_passenger/criterion_chest/criterion_chest_deflection` — Chest Deflection

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Deflection` | §4.1.3 (inherited) | 4 (from limits) | — |

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
| `Criterion_Chest_VC` | §4.1.3 (inherited) | 4 (from limits) | — |

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
| `Criterion_ShoulderBeltLoad` | §4.1.3 (inherited) | 0 (from limits) | — |

Limits for `?6SEBE????B3FO[X0]?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| 0 pt. Modifier | 6 | 0 | green | upper | kN | - |
| -2 pt. Modifier | 6 | -2 | red | lower | kN | - |

## `criterion_rear_passenger/criterion_femur` — Femur

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur` | §4.1.4 | 4 | — |

## `criterion_rear_passenger/criterion_femur/criterion_femur_axial_force` — Femur Axial Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Axial_Force` | §4.1.4 (inherited) | — | — |

## `criterion_rear_passenger/criterion_femur/criterion_femur_axial_force/criterion_femur_axial_force_left` — Femur Axial Force Left

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Femur_Axial_Force_Left` | §4.1.4 (inherited) | 4 (from limits) | — |

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
| `Criterion_Femur_Axial_Force_Right` | §4.1.4 (inherited) | 4 (from limits) | — |

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
| `Criterion_Submarining` | §4.1.4 (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| submarining | bool | False | — | video | Pelvis slid under the lap belt. Caps the femur box at 0 points. |

## `criterion_door_opening_during_impact` — Door Opening During Impact

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_DoorOpeningDuringImpact` | §4 (inherited) | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| number_of_door_openings_during_impact | int | 0 | — | test report | How many doors opened during the impact. −1 point each. |

## `frontal_mpdb` — Euro NCAP | Frontal-Impact against MPDB with 50 % Overlap at 50/50 km/h

# EuroNCAP_Frontal_MPDB

| property | value |
| --- | --- |
| name | Euro NCAP \| Frontal-Impact against MPDB with 50 % Overlap at 50/50 km/h |
| protocol | 9.3 |
| protocols | 9.3 |
| overall criterion | `Overall` |
| available_pages | Page_Cover, Page_Rating_Table, Page_Driver_Result_Values_Chart, Page_Driver_Rating_Table, Page_Driver_Values_Table, Page_Driver_Belt, Page_Driver_Head_Acceleration, Page_Driver_Head_Damage, Page_Driver_Neck_Load, Page_Driver_Chest_Compression, Page_Driver_Abdomen_Compression, Page_Driver_Femur_Axial_Force, Page_Driver_Knee_Slider_Compression, Page_Driver_Tibia_Compression, Page_Driver_Tibia_Index, Page_Passenger_Result_Values_Chart, Page_Passenger_Rating_Table, Page_Passenger_Values_Table, Page_Passenger_Belt, Page_Passenger_Head_Acceleration, Page_Passenger_Neck_Load, Page_Passenger_Chest_Deflection, Page_Passenger_Femur_Axial_Force, Page_Passenger_Knee_Slider_Compression, Page_Passenger_Tibia_Compression, Page_Passenger_Tibia_Index, Page_OLC, Page_OLC_Trolley |
| selected_pages | Page_Cover, Page_Rating_Table, Page_Driver_Result_Values_Chart, Page_Driver_Rating_Table, Page_Driver_Values_Table, Page_Driver_Belt, Page_Driver_Head_Acceleration, Page_Driver_Head_Damage, Page_Driver_Neck_Load, Page_Driver_Chest_Compression, Page_Driver_Abdomen_Compression, Page_Driver_Femur_Axial_Force, Page_Driver_Knee_Slider_Compression, Page_Driver_Tibia_Compression, Page_Driver_Tibia_Index, Page_Passenger_Result_Values_Chart, Page_Passenger_Rating_Table, Page_Passenger_Values_Table, Page_Passenger_Belt, Page_Passenger_Head_Acceleration, Page_Passenger_Neck_Load, Page_Passenger_Chest_Deflection, Page_Passenger_Femur_Axial_Force, Page_Passenger_Knee_Slider_Compression, Page_Passenger_Tibia_Compression, Page_Passenger_Tibia_Index, Page_OLC, Page_OLC_Trolley |

## `Overall` — Overall

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Overall` | §3 | 8 | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| p_driver | str | '1' | — | test report | Channel-code position of the driver. Defaults to the 'Driver position object 1' test-info field when the test carries it. |
| p_passenger | str | '3' | — | test report | Channel-code position of the front passenger. Derived from p_driver ('1' for a right-hand-drive test) unless set explicitly. |

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
| 0 pt. Modifier | 25 | 0 | green | upper | g0 | - |
| -2..0 pt. Modifier | 25 | 0 | red | lower | g0 | - |
| -2 pt. Modifier | 40 | -2 | red | lower | g0 | - |

## `side_pole` — Euro NCAP | Pole Side Impact at 32 km/h

# EuroNCAP_Side_Pole

| property | value |
| --- | --- |
| name | Euro NCAP \| Pole Side Impact at 32 km/h |
| protocol | 9.3 |
| protocols | 9.3 |
| overall criterion | `Overall` |
| available_pages | Page_Cover, Page_Values_Chart, Page_Rating_Table, Page_Values_Table, Page_Head_Acceleration, Page_Shoulder_Lateral_Force, Page_Chest_Lateral_Compression, Page_Chest_Lateral_VC, Page_Abdomen_Lateral_Compression, Page_Abdomen_Lateral_VC, Page_Pubic_Symphysis_Force |
| selected_pages | Page_Cover, Page_Values_Chart, Page_Rating_Table, Page_Values_Table, Page_Head_Acceleration, Page_Shoulder_Lateral_Force, Page_Chest_Lateral_Compression, Page_Chest_Lateral_VC, Page_Abdomen_Lateral_Compression, Page_Abdomen_Lateral_VC, Page_Pubic_Symphysis_Force |

## `Overall` — Overall

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Overall` | §5 | 16 | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| p | str | '1' | — | test report | Channel-code position of the struck-side occupant — the only occupant §5 assesses. Defaults to the 'Driver position object 1' test-info field when the test carries it. |

## `criterion_head` — Head

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head` | §5.1.1.2 | 4 | — |

## `criterion_head/criterion_hic_15` — HIC 15

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HIC_15` | §5.1.1.2 (inherited) | 4 (from limits) | — |

Limits for `?1HICR0015??00RX`, `?1HICRCG15??00RX`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 700 | 4 | green | upper | 1 | - |
| Capping | 700 | -inf | gray | lower | 1 | - |

## `criterion_head/criterion_head_acceleration` — Head Peak Acceleration

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_Peak_Acceleration` | §5.1.1.2 (inherited) | 4 (from limits) | — |

Limits for `?1HEAD??00??ACR?`, `?1HEADCG00??ACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 80 | 4 | green | upper | g0 | - |
| Capping | 80 | -inf | gray | lower | g0 | - |

## `criterion_head/criterion_direct_head_contact_with_the_pole` — Direct head contact with the pole

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_DirectHeadContactWithThePole` | §5.1.1.2 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| direct_head_contact_with_the_pole | bool | False | — | video | Direct head contact with the pole. Caps the head box (−inf → 0 points). |

## `criterion_chest` — Chest

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest` | §5.1.2 | 4 | — |

## `criterion_chest/criterion_chest_lateral_compression` — Chest Lateral Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Lateral_Compression` | §5.1.2 (inherited) | 4 (from limits) | — |

Limits for `?1TRRI??0[0123]??DSY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Capping | -55 | -inf | gray | upper | mm | - |
| Poor | -50 | 0 | red | upper | mm | - |
| Weak | -42.667 | 1.329 | brown | upper | mm | - |
| Marginal | -35.333 | 2.669 | orange | upper | mm | - |
| Adequate | -28 | 4 | yellow | upper | mm | - |
| Good | -28 | 4 | green | lower | mm | - |

## `criterion_chest/criterion_chest_lateral_vc` — Modifier Chest Lateral Viscous Criterion

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Lateral_VC` | §5.2.2 | 4 (from limits) | — |

Limits for `?1VCCR??????VEYC`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Poor | -1 | 0 | red | upper | m/s | - |
| Good | -1 | 4 | green | lower | m/s | - |
| Good | 1 | 4 | green | upper | m/s | - |
| Poor | 1 | 0 | red | lower | m/s | - |

## `criterion_chest/criterion_shoulder_lateral_force` — Modifier Shoulder Lateral Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Shoulder_Lateral_Force` | §5.2.1 | 4 (from limits) | — |

Limits for `?1SHLD0000??FOY?`, `?1SHLDLE00??FOY?`, `?1SHLDRI00??FOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Poor | -3 | 0 | red | upper | kN | - |
| Good | -3 | 4 | green | lower | kN | - |
| Good | 3 | 4 | green | upper | kN | - |
| Poor | 3 | 0 | red | lower | kN | - |

## `criterion_abdomen` — Abdomen

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Abdomen` | §5.1.3 | 4 | — |

## `criterion_abdomen/criterion_abdomen_lateral_compression` — Abdomen Lateral Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Abdomen_Lateral_Compression` | §5.1.3 (inherited) | 4 (from limits) | — |

Limits for `?1ABRI??0[012]??DSY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Capping | -65 | -inf | gray | upper | mm | - |
| Poor | -65 | 0 | red | — | mm | - |
| Weak | -59 | 1.329 | brown | upper | mm | - |
| Marginal | -53 | 2.669 | orange | upper | mm | - |
| Adequate | -47 | 4 | yellow | upper | mm | - |
| Good | -47 | 4 | green | lower | mm | - |

## `criterion_abdomen/criterion_abdomen_lateral_vc` — Modifier Abdomen Lateral Viscous Criterion

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Abdomen_Lateral_VC` | §5.2.2 | 4 (from limits) | — |

Limits for `?1VCAR??????VEYC`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Poor | -1 | 0 | red | upper | m/s | - |
| Good | -1 | 4 | green | lower | m/s | - |
| Good | 1 | 4 | green | upper | m/s | - |
| Poor | 1 | 0 | red | lower | m/s | - |

## `criterion_pelvis` — Pelvis

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Pelvis` | §5.1.4 | 4 | — |

## `criterion_pelvis/criterion_pubic_symphysis_force` — Pubic Symphysis Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Pubic_Symphysis_Force` | §5.1.4 (inherited) | 4 (from limits) | — |

Limits for `?1PUBC0000??FOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Capping | -2.8 | -inf | gray | upper | kN | - |
| Poor | -2.8 | 0 | red | — | kN | - |
| Weak | -2.433 | 1.329 | brown | upper | kN | - |
| Marginal | -2.067 | 2.669 | orange | upper | kN | - |
| Adequate | -1.7 | 4 | yellow | upper | kN | - |
| Good | -1.7 | 4 | green | lower | kN | - |
| Good | 1.7 | 4 | green | upper | kN | - |
| Adequate | 1.7 | 4 | yellow | lower | kN | - |
| Marginal | 2.067 | 2.669 | orange | lower | kN | - |
| Weak | 2.433 | 1.329 | brown | lower | kN | - |
| Poor | 2.8 | 0 | red | — | kN | - |
| Capping | 2.8 | -inf | gray | lower | kN | - |

## `criterion_side_head_protection_device` — Modifier for Side Head Protection Device

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_SideHeadProtectionDevice` | §5.2.3 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| head_protection_device_insufficient_front | bool | False | — | geometric assessment | The head protection device does not cover the front seat positions sufficiently, on the worst performing side. −2 points. |
| head_protection_device_insufficient_rear | bool | False | — | geometric assessment | The head protection device does not cover the rear seat positions sufficiently, on the worst performing side. −2 points. |

## `criterion_incorrect_airbag_deployment` — Modifier for Incorrect Airbag Deployment

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_IncorrectAirbagDeployment` | §5.2.4 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| number_of_body_regions_with_incorrect_airbag_deployment | int | 0 | — | test report | How many body regions (head, chest, abdomen, pelvis) an incorrectly deployed airbag was intended to protect. −1 point each. |

## `criterion_door_opening_during_impact` — Door Opening During Impact

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_DoorOpeningDuringImpact` | §5.2.5 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| number_of_door_openings_during_impact | int | 0 | — | test report | How many doors, tailgates or moveable roofs opened during the impact. −1 point each. |

## `side_barrier` — Euro NCAP | Barrier Side Impact (AE-MDB) at 60 km/h

# EuroNCAP_Side_Barrier

| property | value |
| --- | --- |
| name | Euro NCAP \| Barrier Side Impact (AE-MDB) at 60 km/h |
| protocol | 9.3 |
| protocols | 9.3 |
| overall criterion | `Overall` |
| available_pages | Page_Cover, Page_Values_Chart, Page_Rating_Table, Page_Values_Table, Page_Head_Acceleration, Page_Shoulder_Lateral_Force, Page_Chest_Lateral_Compression, Page_Chest_Lateral_VC, Page_Abdomen_Lateral_Compression, Page_Abdomen_Lateral_VC, Page_Pubic_Symphysis_Force |
| selected_pages | Page_Cover, Page_Values_Chart, Page_Rating_Table, Page_Values_Table, Page_Head_Acceleration, Page_Shoulder_Lateral_Force, Page_Chest_Lateral_Compression, Page_Chest_Lateral_VC, Page_Abdomen_Lateral_Compression, Page_Abdomen_Lateral_VC, Page_Pubic_Symphysis_Force |

## `Overall` — Overall

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Overall` | §5 | 16 | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| p | str | '1' | — | test report | Channel-code position of the struck-side occupant — the only occupant §5 assesses. Defaults to the 'Driver position object 1' test-info field when the test carries it. |

## `criterion_head` — Head

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head` | §5.1.1.1 | 4 | — |

## `criterion_head/criterion_hic_15` — HIC 15

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HIC_15` | §5.1.1.1 (inherited) | 4 (from limits) | — |

Limits for `?1HICR0015??00RX`, `?1HICRCG15??00RX`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 500 | 4 | green | upper | 1 | - |
| Adequate | 500 | 4 | yellow | lower | 1 | - |
| Marginal | 566.667 | 2.669 | orange | lower | 1 | - |
| Weak | 633.333 | 1.329 | brown | lower | 1 | - |
| Poor | 700 | 0 | red | — | 1 | - |
| Capping | 700 | -inf | gray | lower | 1 | - |

## `criterion_head/criterion_head_acceleration` — Head a3ms

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_a3ms` | §5.1.1.1 (inherited) | 4 (from limits) | — |

Limits for `?1HEAD003C??ACR?`, `?1HEADCG3C??ACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 72 | 4 | green | upper | g0 | - |
| Adequate | 72 | 4 | yellow | lower | g0 | - |
| Marginal | 74.667 | 2.669 | orange | lower | g0 | - |
| Weak | 77.333 | 1.329 | brown | lower | g0 | - |
| Poor | 80 | 0 | red | — | g0 | - |
| Capping | 80 | -inf | gray | lower | g0 | - |

## `criterion_chest` — Chest

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest` | §5.1.2 | 4 | — |

## `criterion_chest/criterion_chest_lateral_compression` — Chest Lateral Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Lateral_Compression` | §5.1.2 (inherited) | 4 (from limits) | — |

Limits for `?1TRRI??0[0123]??DSY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Capping | -50 | -inf | gray | upper | mm | - |
| Poor | -50 | 0 | red | — | mm | - |
| Weak | -42.667 | 1.329 | brown | upper | mm | - |
| Marginal | -35.333 | 2.669 | orange | upper | mm | - |
| Adequate | -28 | 4 | yellow | upper | mm | - |
| Good | -28 | 4 | green | lower | mm | - |

## `criterion_chest/criterion_chest_lateral_vc` — Modifier Chest Lateral Viscous Criterion

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Lateral_VC` | §5.2.2 | 4 (from limits) | — |

Limits for `?1VCCR??????VEYC`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Poor | -1 | 0 | red | upper | m/s | - |
| Good | -1 | 4 | green | lower | m/s | - |
| Good | 1 | 4 | green | upper | m/s | - |
| Poor | 1 | 0 | red | lower | m/s | - |

## `criterion_chest/criterion_shoulder_lateral_force` — Modifier Shoulder Lateral Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Shoulder_Lateral_Force` | §5.2.1 | 4 (from limits) | — |

Limits for `?1SHLD0000??FOY?`, `?1SHLDLE00??FOY?`, `?1SHLDRI00??FOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Poor | -3 | 0 | red | upper | kN | - |
| Good | -3 | 4 | green | lower | kN | - |
| Good | 3 | 4 | green | upper | kN | - |
| Poor | 3 | 0 | red | lower | kN | - |

## `criterion_abdomen` — Abdomen

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Abdomen` | §5.1.3 | 4 | — |

## `criterion_abdomen/criterion_abdomen_lateral_compression` — Abdomen Lateral Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Abdomen_Lateral_Compression` | §5.1.3 (inherited) | 4 (from limits) | — |

Limits for `?1ABRI??0[012]??DSY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Capping | -65 | -inf | gray | upper | mm | - |
| Poor | -65 | 0 | red | — | mm | - |
| Weak | -59 | 1.329 | brown | upper | mm | - |
| Marginal | -53 | 2.669 | orange | upper | mm | - |
| Adequate | -47 | 4 | yellow | upper | mm | - |
| Good | -47 | 4 | green | lower | mm | - |

## `criterion_abdomen/criterion_abdomen_lateral_vc` — Modifier Abdomen Lateral Viscous Criterion

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Abdomen_Lateral_VC` | §5.2.2 | 4 (from limits) | — |

Limits for `?1VCAR??????VEYC`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Poor | -1 | 0 | red | upper | m/s | - |
| Good | -1 | 4 | green | lower | m/s | - |
| Good | 1 | 4 | green | upper | m/s | - |
| Poor | 1 | 0 | red | lower | m/s | - |

## `criterion_pelvis` — Pelvis

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Pelvis` | §5.1.4 | 4 | — |

## `criterion_pelvis/criterion_pubic_symphysis_force` — Pubic Symphysis Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Pubic_Symphysis_Force` | §5.1.4 (inherited) | 4 (from limits) | — |

Limits for `?1PUBC0000??FOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Capping | -2.8 | -inf | gray | upper | kN | - |
| Poor | -2.8 | 0 | red | — | kN | - |
| Weak | -2.433 | 1.329 | brown | upper | kN | - |
| Marginal | -2.067 | 2.669 | orange | upper | kN | - |
| Adequate | -1.7 | 4 | yellow | upper | kN | - |
| Good | -1.7 | 4 | green | lower | kN | - |
| Good | 1.7 | 4 | green | upper | kN | - |
| Adequate | 1.7 | 4 | yellow | lower | kN | - |
| Marginal | 2.067 | 2.669 | orange | lower | kN | - |
| Weak | 2.433 | 1.329 | brown | lower | kN | - |
| Poor | 2.8 | 0 | red | — | kN | - |
| Capping | 2.8 | -inf | gray | lower | kN | - |

## `criterion_incorrect_airbag_deployment` — Modifier for Incorrect Airbag Deployment

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_IncorrectAirbagDeployment` | §5.2.4 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| number_of_body_regions_with_incorrect_airbag_deployment | int | 0 | — | test report | How many body regions (head, chest, abdomen, pelvis) an incorrectly deployed airbag was intended to protect. −1 point each. |

## `criterion_door_opening_during_impact` — Door Opening During Impact

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_DoorOpeningDuringImpact` | §5.2.5 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| number_of_door_openings_during_impact | int | 0 | — | test report | How many doors, tailgates or moveable roofs opened during the impact. −1 point each. |

## `side_farside` — Euro NCAP | Far Side Occupant Protection Sled Test

# EuroNCAP_Side_FarSide

| property | value |
| --- | --- |
| name | Euro NCAP \| Far Side Occupant Protection Sled Test |
| protocol | 2.4 |
| protocols | 2.4 |
| overall criterion | `Overall` |
| available_pages | Page_Cover, Page_Values_Chart, Page_Rating_Table, Page_Values_Table, Page_Head_Acceleration, Page_Upper_Neck, Page_Lower_Neck, Page_Chest_Lateral_Compression, Page_Abdomen_Lateral_Compression, Page_Lumbar_Force, Page_Pubic_Symphysis_Force |
| selected_pages | Page_Cover, Page_Values_Chart, Page_Rating_Table, Page_Values_Table, Page_Head_Acceleration, Page_Upper_Neck, Page_Lower_Neck, Page_Chest_Lateral_Compression, Page_Abdomen_Lateral_Compression, Page_Lumbar_Force, Page_Pubic_Symphysis_Force |

## `Overall` — Overall

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Overall` | — | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| p | str | '1' | — | test report | Channel-code position of the far-side occupant — the only occupant §6 assesses. Defaults to the 'Driver position object 1' test-info field when the test carries it. |

## `criterion_head_excursion` — Head Excursion

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_Excursion` | — | — | — |

## `criterion_head` — Head

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head` | — | — | — |

## `criterion_head/criterion_hic_15` — HIC 15

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HIC_15` | — | 4 (from limits) | — |

Limits for `?1HICR0015??00RX`, `?1HICRCG15??00RX`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 500 | 4 | green | upper | 1 | - |
| Adequate | 500 | 4 | yellow | lower | 1 | - |
| Marginal | 566.667 | 2.669 | orange | lower | 1 | - |
| Weak | 633.333 | 1.329 | brown | lower | 1 | - |
| Poor | 700 | 0 | red | — | 1 | - |
| Capping | 700 | -inf | gray | lower | 1 | - |

## `criterion_head/criterion_head_a3ms` — Head a3ms

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_a3ms` | — | 4 (from limits) | — |

Limits for `?1HEAD003C??ACR?`, `?1HEADCG3C??ACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 72 | 4 | green | upper | g0 | - |
| Adequate | 72 | 4 | yellow | lower | g0 | - |
| Marginal | 74.667 | 2.669 | orange | lower | g0 | - |
| Weak | 77.333 | 1.329 | brown | lower | g0 | - |
| Poor | 80 | 0 | red | — | g0 | - |
| Capping | 80 | -inf | gray | lower | g0 | - |

## `criterion_neck` — Neck

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Neck` | — | — | — |

## `criterion_neck/criterion_upper_neck` — Upper_Neck

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Upper_Neck` | — | — | — |

## `criterion_neck/criterion_upper_neck/criterion_tension_fz` — Upper Neck Fz tension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Tension_Fz` | — | 4 (from limits) | — |

Limits for `?1NECKUP00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 3.74 | 4 | green | upper | kN | - |
| Poor | 3.74 | 0 | red | lower | kN | - |

## `criterion_neck/criterion_upper_neck/criterion_lateral_flexion_mxoc` — Lateral flexion MxOC

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Lateral_Flexion_MxOC` | — | 4 (from limits) | — |

Limits for `?1TMONUP00??MOX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Poor | -248 | 0 | red | upper | Nm | - |
| Weak | -219.333 | 1.329 | brown | upper | Nm | - |
| Marginal | -190.667 | 2.669 | orange | upper | Nm | - |
| Adequate | -162 | 4 | yellow | upper | Nm | - |
| Good | -162 | 4 | green | lower | Nm | - |
| Good | 162 | 4 | green | upper | Nm | - |
| Adequate | 162 | 4 | yellow | lower | Nm | - |
| Marginal | 190.667 | 2.669 | orange | lower | Nm | - |
| Weak | 219.333 | 1.329 | brown | lower | Nm | - |
| Poor | 248 | 0 | red | lower | Nm | - |

## `criterion_neck/criterion_upper_neck/criterion_extension_myoc` — Upper Neck Extension MyOC

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Extension_MyOC` | — | 4 (from limits) | — |

Limits for `?1TMONUP00??MOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Poor | -50 | 0 | red | upper | Nm | - |
| Good | -50 | 4 | green | lower | Nm | - |

## `criterion_neck/criterion_lower_neck` — Lower_Neck

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Lower_Neck` | — | — | — |

## `criterion_neck/criterion_lower_neck/criterion_tension_fz` — Lower Neck Fz tension

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Tension_Fz` | — | 4 (from limits) | — |

Limits for `?1NECKLO00??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 3.74 | 4 | green | upper | kN | - |
| Poor | 3.74 | 0 | red | lower | kN | - |

## `criterion_neck/criterion_lower_neck/criterion_lateral_flexion_mx` — Lateral flexion Mx (base of neck)

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Lateral_Flexion_Mx` | — | 4 (from limits) | — |

Limits for `?1TMONLO00??MOX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Poor | -248 | 0 | red | upper | Nm | - |
| Weak | -219.333 | 1.329 | brown | upper | Nm | - |
| Marginal | -190.667 | 2.669 | orange | upper | Nm | - |
| Adequate | -162 | 4 | yellow | upper | Nm | - |
| Good | -162 | 4 | green | lower | Nm | - |
| Good | 162 | 4 | green | upper | Nm | - |
| Adequate | 162 | 4 | yellow | lower | Nm | - |
| Marginal | 190.667 | 2.669 | orange | lower | Nm | - |
| Weak | 219.333 | 1.329 | brown | lower | Nm | - |
| Poor | 248 | 0 | red | lower | Nm | - |

## `criterion_neck/criterion_lower_neck/criterion_extension_my_base` — Lower Neck Extension My Base

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Extension_My_Base` | — | 4 (from limits) | — |

Limits for `?1TMONLO00??MOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Poor | -100 | 0 | red | upper | Nm | - |
| Good | -100 | 4 | green | lower | Nm | - |

## `criterion_chest_abdomen` — Chest & Abdomen

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Abdomen` | — | — | — |

## `criterion_chest_abdomen/criterion_chest_lateral_compression` — Chest Lateral Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Chest_Lateral_Compression` | — | 4 (from limits) | — |

Limits for `?1TRRI??0[0123]??DSY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Capping | -50 | -inf | gray | upper | mm | - |
| Poor | -50 | 0 | red | — | mm | - |
| Weak | -42.667 | 1.329 | brown | upper | mm | - |
| Marginal | -35.333 | 2.669 | orange | upper | mm | - |
| Adequate | -28 | 4 | yellow | upper | mm | - |
| Good | -28 | 4 | green | lower | mm | - |

## `criterion_chest_abdomen/criterion_abdomen_lateral_compression` — Abdomen Lateral Compression

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Abdomen_Lateral_Compression` | — | 4 (from limits) | — |

Limits for `?1ABRI??0[012]??DSY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Capping | -65 | -inf | gray | upper | mm | - |
| Poor | -65 | 0 | red | — | mm | - |
| Weak | -59 | 1.329 | brown | upper | mm | - |
| Marginal | -53 | 2.669 | orange | upper | mm | - |
| Adequate | -47 | 4 | yellow | upper | mm | - |
| Good | -47 | 4 | green | lower | mm | - |

## `criterion_pelvis_lumbar_modifier` — Pelvis and Lumbar Modifier

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Pelvis_Lumbar_Modifier` | — | — | — |

## `criterion_pelvis_lumbar_modifier/criterion_pubic_symphysis` — Modifier Pubic Symphysis

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Pubic_Symphysis` | — | 0 (from limits) | — |

Limits for `?1PUBC0000??FOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| -4 pt. Modifier | -2.8 | -4 | red | upper | kN | - |
| 0 pt. Modifier | 2.8 | 0 | green | upper | kN | - |
| -4 pt. Modifier | 2.8 | -4 | red | lower | kN | - |

## `criterion_pelvis_lumbar_modifier/criterion_lumbar_fy` — Modifier Lumbar Fy

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Lumbar_Fy` | — | 0 (from limits) | — |

Limits for `?1LUSP0000??FOY?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| -4 pt. Modifier | -2 | -4 | red | upper | kN | - |
| 0 pt. Modifier | 2 | 0 | green | upper | kN | - |
| -4 pt. Modifier | 2 | -4 | red | lower | kN | - |

## `criterion_pelvis_lumbar_modifier/criterion_lumbar_fz` — Modifier Lumbar Fz

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Lumbar_Fz` | — | 0 (from limits) | — |

Limits for `?1LUSP0000??FOZ?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| -4 pt. Modifier | -3.5 | -4 | red | upper | kN | - |
| 0 pt. Modifier | 3.5 | 0 | green | upper | kN | - |
| -4 pt. Modifier | 3.5 | -4 | red | lower | kN | - |

## `criterion_pelvis_lumbar_modifier/criterion_lumbar_mx` — Modifier Lumbar Mx

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Lumbar_Mx` | — | 0 (from limits) | — |

Limits for `?1LUSP0000??MOX?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| -4 pt. Modifier | -120 | -4 | red | upper | Nm | - |
| 0 pt. Modifier | 120 | 0 | green | upper | Nm | - |
| -4 pt. Modifier | 120 | -4 | red | lower | Nm | - |
