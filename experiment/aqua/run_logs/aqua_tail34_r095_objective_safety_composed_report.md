# R095 Objective-Safety Composed Selector Report

**Claim boundary**: label-free replay over R065 multi-view traces; not an explicit forced-template or transfer result

- Tasks: `34`
- ARG baseline solved: `28/34`
- R065 objective selector solved: `31/34`
- Safety-composed solved: `30/34`
- Safety-composed fix/harm: `{'fix': 2, 'harm': 0}`
- Accepted switches: `['task_108', 'task_250']`
- Suppressed switches: `['task_114', 'task_59']`
- Clean/noisy buckets: `{'noisy': {'num_tasks': 6, 'baseline_solved': 1, 'objective_selector_solved': 3, 'gate_solved': 2, 'fix_harm': {'fix': 1, 'harm': 0}, 'fix_tasks': ['task_108'], 'harm_tasks': []}, 'clean': {'num_tasks': 28, 'baseline_solved': 27, 'objective_selector_solved': 28, 'gate_solved': 28, 'fix_harm': {'fix': 1, 'harm': 0}, 'fix_tasks': ['task_250'], 'harm_tasks': []}}`
- Decision-field violations: `0`

## Switch Rows

| Task | Audit label | ARG | Objective | Safety-composed | Gold | Action | Reason | Objective top score | Baseline valid/majority votes |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| `task_114` | `noisy` | `C` | `D` | `C` | `D` | `fallback_to_arg` | `insufficient_safety_evidence` | `2` | `1`/`1` |
| `task_59` | `noisy` | `B` | `D` | `B` | `C` | `fallback_to_arg` | `insufficient_safety_evidence` | `2` | `2`/`2` |
| `task_108` | `noisy` | `B` | `D` | `D` | `D` | `accept_objective` | `baseline_direct_split_allows_switch` | `2` | `2`/`1` |
| `task_250` | `clean` | `A` | `E` | `E` | `E` | `accept_objective` | `objective_top_score_ge3` | `3` | `2`/`2` |

## Interpretation

R095 composes R094's clean-harm safety idea with R065's multi-view objective signal. It keeps the clean fix `task_250` through the high objective score and keeps the noisy `task_108` fix through baseline direct-vote split, while suppressing weaker noisy switches. This is the strongest current paper direction, but it remains a replay over R065 multi-view traces and lacks explicit forced-template PromptNode graph metadata.
