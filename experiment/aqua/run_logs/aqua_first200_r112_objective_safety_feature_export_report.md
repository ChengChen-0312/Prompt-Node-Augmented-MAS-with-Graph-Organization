# R112 First200 Objective-Safety Feature Export

**Claim boundary**: first200 feature export and proxy target construction only; no trained proxy or accuracy claim

- Rows: `200`
- Baseline source rows: `200`
- Objective source rows: `200`
- Required rule features: `['objective_prediction_differs_from_baseline', 'objective_top_score', 'baseline_direct_votes_split']`
- Exported required features: `['objective_prediction_differs_from_baseline', 'objective_top_score', 'baseline_direct_votes_split']`
- Missing required features: `[]`
- Uses tail34 training source: `False`
- Policy-input field violations: `0`
- Baseline-prediction mismatches: `11`
- Target actions: `{'fallback_to_arg': 189, 'switch_to_objective': 11}`
- Target reasons: `{'baseline_direct_split_allows_switch': 1, 'insufficient_safety_evidence': 9, 'objective_top_score_ge3': 10, 'same_prediction_as_arg': 180}`
- Objective differs count: `20`
- Baseline direct-votes split count: `3`
- Switch target tasks: `['task_152', 'task_172', 'task_95', 'task_135', 'task_122', 'task_149', 'task_176', 'task_184', 'task_197', 'task_67', 'task_207']`

## Interpretation

R112 supplies the missing first200/non-tail34 inputs required by the R110 proxy protocol. It reconstructs ARG direct-vote split from the two first200 ARG baseline slices and joins it with first200 objective-guided selector traces. The resulting rows can train or validate a proxy for the R109 objective-safety rule without using tail34 training data.

This is not a trained proxy, a held-out accuracy result, or evidence that the method exceeds ARG. The next gate is to train or fit a proxy only on these non-tail34 rows and evaluate agreement on the frozen R109 tail34 targets.
