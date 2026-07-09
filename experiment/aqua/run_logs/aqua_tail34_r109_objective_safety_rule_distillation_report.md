# R109 Objective-Safety Rule Distillation

**Claim boundary**: rule distillation over R096 targets; no new accuracy or cheap-proxy claim

- Rows: `34`
- Target agreement: `34/34`
- Switch tasks: `['task_108', 'task_250']`
- Objective-diff suppressed tasks: `['task_114', 'task_59']`
- Rule input field violations: `0`
- Requires multi-view objective features: `True`
- Cheap single-template proxy ready: `False`

## Distilled Rule

`switch_to_objective iff objective_prediction_differs_from_baseline and (objective_top_score>=3 or baseline_direct_votes_split)`

## Switch Tasks

| Task | Reason | Objective score | Baseline split | Audit label |
| --- | --- | --- | --- | --- |
| `task_108` | `baseline_direct_split_allows_switch` | `2` | `True` | `noisy` |
| `task_250` | `objective_top_score_ge3` | `3` | `False` | `clean` |

## Objective-Diff Suppressed Tasks

| Task | Reason | Objective score | Baseline split | Audit label |
| --- | --- | --- | --- | --- |
| `task_114` | `insufficient_safety_evidence` | `2` | `False` | `noisy` |
| `task_59` | `insufficient_safety_evidence` | `2` | `False` | `noisy` |

## Interpretation

The R096 target policy is exactly captured by a small objective-safety rule, but R108 shows the required objective features cannot be replaced by the current single rank5-template trace features. This is a rule-specification artifact for a future proxy or selector, not a new accuracy result.
