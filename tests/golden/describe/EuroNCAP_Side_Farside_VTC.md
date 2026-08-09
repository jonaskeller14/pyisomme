# EuroNCAP_Side_Farside_VTC

| property | value |
| --- | --- |
| name | Euro NCAP \| Virtual Far Side Simulations |
| protocol | 1.0 |
| protocols | 1.0 |
| overall criterion | `Overall` |
| available_pages | Page_Cover, Page_Validation_ISO_Score_Table, Page_Validation_Injury_Criteria_Percentage_Table, Page_Head_Acceleration, Page_Chest_Lateral_Compression, Page_Abdomen_Lateral_Compression, Page_Pubic_Symphysis_Force |
| selected_pages | Page_Cover, Page_Validation_ISO_Score_Table, Page_Validation_Injury_Criteria_Percentage_Table, Page_Head_Acceleration, Page_Chest_Lateral_Compression, Page_Abdomen_Lateral_Compression, Page_Pubic_Symphysis_Force |

## `Overall` — Overall

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Overall` | — | — | — |

Manual inputs:

| input | type | default | unit | source | doc |
| --- | --- | --- | --- | --- | --- |
| p | str | '1' | — | test report | Channel-code position of the assessed occupant. Defaults to the 'Driver position object 1' test-info field when the test carries it. |

## `validation_iso_scores` — Validation ISO Scores

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Validation_ISO_Scores` | — | — | — |

## `validation_iso_scores/head_avx` — Head COG Angular Velocity X

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_COG_Angular_Velocity_X` | — | 1 (from limits) | — |

Limits for `—`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Limit | 0.5 | True | green | lower | 1 | - |
| Limit | 0.5 | False | red | upper | 1 | - |

## `validation_iso_scores/head_avy` — Head COG Angular Velocity Y

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_COG_Angular_Velocity_Y` | — | 1 (from limits) | — |

Limits for `—`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Limit | 0.5 | True | green | lower | 1 | - |
| Limit | 0.5 | False | red | upper | 1 | - |

## `validation_iso_scores/head_avz` — Head COG Angular Velocity Z

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_COG_Angular_Velocity_Z` | — | 1 (from limits) | — |

Limits for `—`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Limit | 0.5 | True | green | lower | 1 | - |
| Limit | 0.5 | False | red | upper | 1 | - |

## `validation_iso_scores/head_avr` — Head COG Angular Velocity

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_COG_Angular_Velocity` | — | 1 (from limits) | — |

Limits for `—`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Limit | 0.5 | True | green | lower | 1 | - |
| Limit | 0.5 | False | red | upper | 1 | - |

## `validation_iso_scores/thsp_04_acx` — T4 Acceleration X

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Spine_T4_Acceleration_X` | — | 1 (from limits) | — |

Limits for `—`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Limit | 0.5 | True | green | lower | 1 | - |
| Limit | 0.5 | False | red | upper | 1 | - |

## `validation_iso_scores/thsp_04_acy` — T4 Acceleration Y

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Spine_T4_Acceleration_Y` | — | 1 (from limits) | — |

Limits for `—`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Limit | 0.5 | True | green | lower | 1 | - |
| Limit | 0.5 | False | red | upper | 1 | - |

## `validation_iso_scores/thsp_04_acz` — T4 Acceleration Z

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Spine_T4_Acceleration_Z` | — | 1 (from limits) | — |

Limits for `—`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Limit | 0.5 | True | green | lower | 1 | - |
| Limit | 0.5 | False | red | upper | 1 | - |

## `validation_iso_scores/thsp_04_acr` — T4 Acceleration

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Spine_T4_Acceleration` | — | 1 (from limits) | — |

Limits for `—`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Limit | 0.5 | True | green | lower | 1 | - |
| Limit | 0.5 | False | red | upper | 1 | - |

## `validation_iso_scores/thsp_12_acx` — T12 Acceleration X

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Spine_T12_Acceleration_X` | — | 1 (from limits) | — |

Limits for `—`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Limit | 0.5 | True | green | lower | 1 | - |
| Limit | 0.5 | False | red | upper | 1 | - |

## `validation_iso_scores/thsp_12_acy` — T12 Acceleration Y

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Spine_T12_Acceleration_Y` | — | 1 (from limits) | — |

Limits for `—`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Limit | 0.5 | True | green | lower | 1 | - |
| Limit | 0.5 | False | red | upper | 1 | - |

## `validation_iso_scores/thsp_12_acz` — T12 Acceleration Z

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Spine_T12_Acceleration_Z` | — | 1 (from limits) | — |

Limits for `—`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Limit | 0.5 | True | green | lower | 1 | - |
| Limit | 0.5 | False | red | upper | 1 | - |

## `validation_iso_scores/thsp_12_acr` — T12 Acceleration

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Spine_T12_Acceleration` | — | 1 (from limits) | — |

Limits for `—`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Limit | 0.5 | True | green | lower | 1 | - |
| Limit | 0.5 | False | red | upper | 1 | - |

## `validation_iso_scores/pelv_acx` — Pelvis Acceleration X

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Pelvis_Acceleration_X` | — | 1 (from limits) | — |

Limits for `—`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Limit | 0.5 | True | green | lower | 1 | - |
| Limit | 0.5 | False | red | upper | 1 | - |

## `validation_iso_scores/pelv_acy` — Pelvis Acceleration Y

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Pelvis_Acceleration_Y` | — | 1 (from limits) | — |

Limits for `—`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Limit | 0.5 | True | green | lower | 1 | - |
| Limit | 0.5 | False | red | upper | 1 | - |

## `validation_iso_scores/pelv_acz` — Pelvis Acceleration Z

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Pelvis_Acceleration_Z` | — | 1 (from limits) | — |

Limits for `—`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Limit | 0.5 | True | green | lower | 1 | - |
| Limit | 0.5 | False | red | upper | 1 | - |

## `validation_iso_scores/pelv_acr` — Pelvis Acceleration

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Pelvis_Acceleration` | — | 1 (from limits) | — |

Limits for `—`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Limit | 0.5 | True | green | lower | 1 | - |
| Limit | 0.5 | False | red | upper | 1 | - |

## `validation_iso_scores/b_pillar_acx` — B-Pillar Acceleration X

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_B_Pillar_Acceleration_X` | — | 1 (from limits) | — |

Limits for `—`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Limit | 0.5 | True | green | lower | 1 | - |
| Limit | 0.5 | False | red | upper | 1 | - |

## `validation_iso_scores/b_pillar_acy` — B-Pillar Acceleration Y

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_B_Pillar_Acceleration_Y` | — | 1 (from limits) | — |

Limits for `—`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Limit | 0.5 | True | green | lower | 1 | - |
| Limit | 0.5 | False | red | upper | 1 | - |

## `validation_iso_scores/b_pillar_acz` — B-Pillar Acceleration Z

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_B_Pillar_Acceleration_Z` | — | 1 (from limits) | — |

Limits for `—`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Limit | 0.5 | True | green | lower | 1 | - |
| Limit | 0.5 | False | red | upper | 1 | - |

## `validation_iso_scores/b_pillar_acr` — B-Pillar Acceleration

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_B_Pillar_Acceleration` | — | 1 (from limits) | — |

Limits for `—`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Limit | 0.5 | True | green | lower | 1 | - |
| Limit | 0.5 | False | red | upper | 1 | - |

## `validation_iso_scores/belt_b3_fo0` — Shoulder Belt (B3) Force

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Shoulder_B3_Force` | — | 1 (from limits) | — |

Limits for `—`:

| row | threshold | rating | color | flag | y_unit | linestyle |
| --- | --- | --- | --- | --- | --- | --- |
| Limit | 0.5 | True | green | lower | 1 | - |
| Limit | 0.5 | False | red | upper | 1 | - |

## `criterion_validation_injury_criteria` — Validation Injury Criteria

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Validation_Injury_Criteria` | — | — | — |

## `criterion_validation_injury_criteria/criterion_hic_15` — HIC 15

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_HIC_15` | — | — | — |

## `criterion_validation_injury_criteria/criterion_head_a3ms` — Head a3ms

| class | source | max rating | aggregation |
| --- | --- | --- | --- |
| `Criterion_Head_a3ms` | — | — | — |
