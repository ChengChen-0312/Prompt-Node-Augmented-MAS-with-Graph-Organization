# R126 Clean-Fix Graph-Policy Selector Protocol

**Claim boundary**: protocol only; no training, API, accuracy, or cost result

- Protocol only: `True`
- No API run: `True`
- Uses tail34 training source: `False`
- First200 template count: `17`
- First200 clean-fix positive rows: `76`
- First200 objective-safety rows: `200`
- Candidate selector families: `['graph_policy_selector', 'template_rank_policy', 'guarded_multiview_distillation']`
- Required clean harm guards: `['task_8', 'task_188']`
- Required clean recovery targets: `['task_250']`
- Noisy optional targets: `['task_108']`
- Broad API before smoke: `False`
- Next smoke protocol: `four_task_clean_fix_graph_policy_selector_smoke`

## Allowed Training Sources

- `experiment/aqua/aqua_first200_r077_clean_fix_graph_policy_distill_rows.jsonl`
- `experiment/aqua/aqua_first200_r082_clean_fix_graph_templates.jsonl`
- `experiment/aqua/aqua_first200_r112_objective_safety_feature_targets.jsonl`

## Forbidden Training Sources

- `tail34_r096_policy_targets`
- `tail34_r109_rule_distillation`
- `tail34_r113_eval_targets`
- `tail34_r114_regression_replay`
- `tail34_r124_outputs`
- `tail34_true_answers_or_clean_labels`

## Interpretation

R126 freezes the next path after the R125 audit. The next selector may learn from first200 clean-fix graph-policy/template artifacts and first200 objective-safety features, but tail34 artifacts may only be used as frozen evaluation or regression gates. The next API step remains blocked until a four-task clean-fix selector smoke is defined and passes.
