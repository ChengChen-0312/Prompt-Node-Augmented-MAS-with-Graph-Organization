# R097 Objective-Safety Template Plan

**Claim boundary**: explicit template plan from R096/R083; no new API or accuracy result

- Rows: `34`
- Target action counts: `{'fallback_to_arg': 32, 'switch_to_objective': 2}`
- Switch targets: `['task_108', 'task_250']`
- Switch targets with template candidates: `['task_108', 'task_250']`
- Missing switch templates: `[]`
- Switch targets with update2 metadata: `2`
- Selector input field violations: `0`
- Plan JSONL: `experiment/aqua/aqua_tail34_r097_objective_safety_template_plan.jsonl`

## Switch Plan

| Task | Audit label | Target reason | Status | Template rank | Support | PN roles | Update2 metadata |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| `task_108` | `noisy` | `baseline_direct_split_allows_switch` | `template_attached` | `1` | `35` | `PN_Memory,PN_Verifier,PN_Router` | `True` |
| `task_250` | `clean` | `objective_top_score_ge3` | `template_attached` | `1` | `35` | `PN_Memory,PN_Verifier,PN_Router` | `True` |

## Interpretation

R097 attaches explicit R083 PromptNode graph templates to the R096 switch targets. The selector inputs exclude answer labels, correctness flags, task ids, target labels, and clean/noisy audit labels. This is an executable-plan bridge for a future API run, not a new accuracy result.
