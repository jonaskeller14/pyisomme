# EuroNCAP_Side_FarSide

| property | value |
| --- | --- |
| name | Euro NCAP \| Far Side Occupant Protection Sled Test |
| protocol | 2.5 |
| protocols | 2.4, 2.5 |
| overall criterion | `Overall` |
| available_pages | Page_Cover, Page_Values_Chart, Page_Rating_Table, Page_Values_Table, Page_Head_Acceleration, Page_Head_DAMAGE, Page_Upper_Neck, Page_Lower_Neck, Page_Chest_Lateral_Compression, Page_Abdomen_Lateral_Compression, Page_Lumbar_Force, Page_Pubic_Symphysis_Force |
| selected_pages | Page_Cover, Page_Values_Chart, Page_Rating_Table, Page_Values_Table, Page_Head_Acceleration, Page_Head_DAMAGE, Page_Upper_Neck, Page_Lower_Neck, Page_Chest_Lateral_Compression, Page_Abdomen_Lateral_Compression, Page_Lumbar_Force, Page_Pubic_Symphysis_Force |

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
| `Criterion_Head_Excursion` | §7.2 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| excursion_zone | str | 'green' | — | high-speed video | Peak head-excursion zone: capping, red, orange, yellow, or green. |
| far_side_countermeasure | bool | False | — | test report | Is a far-side countermeasure fitted? This selects the applicable §7.2 head-excursion score-cap table. |
| red_line_more_than_125_mm_outboard | bool | False | — | test set-up measurement | For a red-zone excursion with a countermeasure, is the red line more than 125 mm outboard of the orange line? |

## `criterion_head` — Head

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head` | §7.3.1 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| hard_contact | bool | True | — | high-speed video | Was hard head contact observed? A resultant 3 ms acceleration above 80 g forces this to True regardless. |

## `criterion_head/criterion_hic_15` — HIC 15

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HIC_15` | §7.3.1 (inherited) | 4 (from limits) | — |

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
| `Criterion_Head_a3ms` | §7.3.1 (inherited) | 4 (from limits) | — |

Limits for `?1HEAD003C??ACR?`, `?1HEADCG3C??ACR?`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Good | 72 | 4 | green | upper | g0 | - |
| Adequate | 72 | 4 | yellow | lower | g0 | - |
| Marginal | 74.667 | 2.669 | orange | lower | g0 | - |
| Weak | 77.333 | 1.329 | brown | lower | g0 | - |
| Poor | 80 | 0 | red | — | g0 | - |
| Capping | 80 | -inf | gray | lower | g0 | - |

## `criterion_head/criterion_damage` — Head DAMAGE (monitoring)

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_DAMAGE` | §7.3.1.1 | — | — |

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

## `criterion_occupant_to_occupant_protection` — Modifier for Occupant-to-Occupant Protection

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Occupant_to_Occupant_Protection` | §7.4.2 | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| countermeasure_asymmetric | bool | False | — | dual-occupancy assessment | The occupant-interaction countermeasure lacks equivalent protection for impacts on both sides. −1 final point. |
| dual_occupancy_head_interaction | bool | False | — | dual-occupancy high-speed video | Either dummy head contacted the adjacent occupant, or the head lower performance limits were exceeded. −1 final point. |
| excursion_countermeasure_lacks_interaction_protection | bool | False | — | dual-occupancy assessment | A far-side countermeasure limits excursion but does not provide meaningful occupant-to-occupant head protection. −1 final point. |
| protection_zone_not_met | bool | False | — | dual-occupancy assessment | The required occupant-interaction protection zone was not demonstrated. −1 final point. |
