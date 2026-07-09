# R113 Objective-Safety Proxy Rule Learner

**Claim boundary**: rule-proxy target agreement only; no answer accuracy or prospective API claim

- Train source: `experiment/aqua/aqua_first200_r112_objective_safety_feature_targets.jsonl`
- Frozen eval source: `experiment/aqua/res_logs/aqua_tail34_r109_objective_safety_rule_distillation_summary.json`
- Train rows: `200`
- Frozen eval rows: `34`
- Candidate rules: `16`
- Learned rule: `diff_and_top_score_ge_3_or_split`
- Train target agreement: `200/200`
- Frozen tail34 target agreement: `34/34`
- Frozen tail34 switch tasks: `['task_108', 'task_250']`
- Uses tail34 training source: `False`
- Proxy input-field violations: `0`

## Interpretation

R113 fits a compact proxy rule on R112 first200/non-tail34 target rows and evaluates it on the frozen R109 tail34 targets. This supports target-agreement reproducibility for the objective-safety rule, but it is not an answer-accuracy result and does not remove the need for prospective API validation or transfer testing.
