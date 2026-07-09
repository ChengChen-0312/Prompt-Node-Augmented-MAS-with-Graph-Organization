# R096 Objective-Safety Policy Target Export

**Claim boundary**: policy-target export from R095 replay; no new accuracy result

- Rows: `34`
- Target action counts: `{'fallback_to_arg': 32, 'switch_to_objective': 2}`
- Switch target tasks: `['task_108', 'task_250']`
- Clean switch targets: `['task_250']`
- Noisy switch targets: `['task_108']`
- Policy input field violations: `0`
- Target JSONL: `experiment/aqua/aqua_tail34_r096_objective_safety_policy_targets.jsonl`

## Switch Targets

| Task | Audit label | Target reason | Objective top score | Baseline split |
| --- | --- | --- | ---: | --- |
| `task_108` | `noisy` | `baseline_direct_split_allows_switch` | `2` | `True` |
| `task_250` | `clean` | `objective_top_score_ge3` | `3` | `False` |

## Interpretation

R096 converts the R095 replay decision into leakage-checked policy targets. The exported policy inputs exclude task ids, gold labels, correctness, and audit labels. This is a bridge toward an explicit PromptNode graph-policy/template selector, not a new accuracy result.
