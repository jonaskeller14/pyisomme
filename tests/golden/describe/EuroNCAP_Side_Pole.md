# EuroNCAP_Side_Pole

| property | value |
| --- | --- |
| name | Euro NCAP \| Pole Side Impact at 32 km/h |
| protocol | 9.3 |
| protocols | 9.3 |
| overall criterion | `Overall` |
| pages | Page_Cover, Page_Values_Chart, Page_Rating_Table, Page_Values_Table, Page_Head_Acceleration, Page_Shoulder_Lateral_Force, Page_Chest_Lateral_Compression, Page_Chest_Lateral_VC, Page_Abdomen_Lateral_Compression, Page_Abdomen_Lateral_VC, Page_Pubic_Symphysis_Force |

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
