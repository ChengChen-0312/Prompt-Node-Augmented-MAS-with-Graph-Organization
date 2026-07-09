# R266 AQuA Tail34 Audit-Clean Rescore

**Claim boundary**: No API; post-hoc rescore over existing ARG and R065 predictions. Original data is unchanged.

## Score Table

| Scenario | ARG | R065 | Delta | Notes |
|---|---:|---:|---:|---|
| `official_tail34` | `28/34` | `31/34` | `3` | Original AQuA labels, no exclusions. |
| `exclude_59_139_228` | `28/31` | `31/31` | `3` | User-requested clean filter: remove task_59/task_139/task_228 only. |
| `exclude_59_139_228_correct_114` | `29/31` | `30/31` | `1` | Sensitivity: remove the three bad tasks and correct task_114 from D to C. |
| `exclude_59_139_228_114` | `28/30` | `30/30` | `2` | Conservative clean filter: remove the three bad tasks and remove task_114 as boundary-label noise. |

## Task 114 Audit

- Official label: `D`
- Deterministic strict label: `C`
- Error category: `official_label_boundary_error`
- Range: min `{'n': 36.0, 'x': 28.0}`, max `{'n': 72.0, 'x': 59.029437251523}`
- Reason: At n=36, x=28 exactly, so strict option D (28 < x < 60) is false; option C contains the full sampled range.

## Paper Guidance

- Keep the original AQuA score for comparability.
- Use the audit-clean score as the primary robustness table only if the appendix discloses the exclusion/correction manifest.
- Do not train toward these corrected test labels; use them for evaluation reporting only.
