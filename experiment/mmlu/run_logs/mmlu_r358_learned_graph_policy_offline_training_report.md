# R358 Learned Graph-Policy Offline Training

**Claim boundary**: R358 trains an offline graph-policy gate on leakage-safe features. It is an internal feasibility result, not a held-out API evaluation or paper claim.

- Model: `logistic_regression_liblinear_balanced`
- Train/dev/test records: `236/35/63`
- Test F1: `1.0`
- Test FP/FN: `0/0`
- Top positive features: `['candidate_evidence_count', 'gate_score', 'candidate_has_answer_label', 'lifecycle_has_upgrade', 'candidate_confidence']`
- Next required run: `R359_learned_graph_policy_fresh_eval_preflight`
