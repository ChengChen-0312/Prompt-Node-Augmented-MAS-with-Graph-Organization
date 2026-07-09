# R267 Cost-Safety Combined Selector

**Claim boundary**: no_api_replay_over_r068_trigger_and_r095_safety_gate

## Scores

| View | Score | Wrong tasks |
|---|---:|---|
| Official tail34 | `30/34` | `['task_114', 'task_59', 'task_139', 'task_228']` |
| Exclude 59/139/228 | `30/31` | `['task_114']` |
| Exclude 59/139/228 + correct 114 | `31/31` | `[]` |
| Exclude 59/139/228/114 | `30/30` | `[]` |

## Decisions

- Accepted switches: `['task_108', 'task_250']`
- Suppressed switches: `['task_114', 'task_59']`
- Estimated cost from zero: `$3.597409`
- Marginal API cost after R068 traces: `$0.0`

## Interpretation

R267 keeps R068's reduced multi-view trigger cost and applies R095's safety gate. It loses one official point relative to R065/R068 by suppressing task_114, but becomes audit-correct when task_114 is treated as a boundary-label error.
