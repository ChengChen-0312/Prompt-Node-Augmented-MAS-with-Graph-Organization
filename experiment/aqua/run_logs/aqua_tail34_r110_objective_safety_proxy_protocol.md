# R110 Objective-Safety Proxy Protocol

**Claim boundary**: protocol only; no trained proxy, accuracy, or SCI claim

- Train source rows: `800`
- Train clean-fix preserve rows: `76`
- Existing selector eval agreement: `0.9675`
- Tail34 eval target rows: `34`
- Tail34 training allowed: `False`
- Required rule features: `['objective_prediction_differs_from_baseline', 'objective_top_score', 'baseline_direct_votes_split']`
- Proxy candidate families: `['lightweight_multiview_objective', 'graph_policy_selector']`
- Input field violations: `0`

## Forbidden Tail34 Training Sources

- `experiment/aqua/aqua_tail34_r096_objective_safety_policy_targets.jsonl`
- `experiment/aqua/res_logs/aqua_tail34_r109_objective_safety_rule_distillation_summary.json`
- `experiment/aqua/aqua_tail34_r106_rank5_regression_smoke_results.jsonl`

## Minimum Next Gate

train on first200/non-tail34 only; evaluate target agreement on frozen R109 tail34 rule targets; then run a small clean-harm/recovery smoke before broad API use

## Interpretation

R110 freezes the next proxy-training boundary. Tail34 R096/R109 can evaluate whether a proxy matches the objective-safety rule, but those rows cannot be training examples. This keeps the SCI-Q2 story defensible by separating method iteration, proxy training, and held-out validation.
