# R117 Lightweight Objective-Trace Protocol

**Claim boundary**: protocol only; no new accuracy, cost, or API result

- Protocol only: `True`
- No API run: `True`
- Model: `gpt-4o-2024-08-06`
- Candidate protocols: `['two_view_objective_probe', 'graph_policy_topk_probe']`
- Regression tasks: `['task_8', 'task_108', 'task_188', 'task_250']`
- Required suppressed harms: `['task_8']`
- Required clean recoveries: `['task_250']`
- No clean harm required: `True`
- Baseline-only trigger allowed: `False`
- Tail34 training allowed: `False`
- Broad API before smoke: `False`
- Max PromptNode views per triggered task: `2`
- Full multi-view cost reference: `$5.050805`
- Measured cost target upper bound: `$1.828715`

## Gates

- Cost: measured total cost must be below R074 measured cost and far below full multi-view before an efficiency claim is allowed
- Accuracy: four-task smoke must preserve R114 behavior: suppress task_8 harm, recover task_250, and introduce no clean harm

## Forbidden Shortcuts

- `baseline_only_direct_vote_trigger`
- `single_rank5_template_guard`
- `tail34_training_or_threshold_tuning`
- `broad_api_before_regression_smoke`

## Interpretation

R117 freezes the next prospective direction without spending API. It requires a lightweight objective-trace or graph-policy signal because R116 rejected baseline-only triggers, and it blocks broad evaluation until the four-task clean-harm/recovery smoke passes with measured cost.
