# R141 Repair-Confidence Calibration Protocol

**Claim boundary**: calibration protocol only; no API, threshold change, accuracy, transfer, robustness, or SCI-readiness claim

- Protocol only: `True`
- No API run: `True`
- R140 alignment confirmed: `True`
- R139 forwarding fixed: `True`
- R139 low-confidence rejection: `True`
- R139 task250 repair confidence: `0.5`
- R139 repair min confidence: `0.8`
- Direct threshold lowering allowed: `False`
- Uses tail34 training source: `False`
- Broad API allowed next: `False`
- Next protocol: `repair_confidence_calibration_offline_export`

## Allowed Sources

- `first200_non_tail34_option_binding_audit`
- `first200_non_tail34_graph_policy_rows`
- `first200_non_tail34_objective_safety_features`
- `synthetic_numeric_repair_controls`

## Forbidden Sources

- `tail34_true_answers_or_clean_labels`
- `tail34_task_ids`
- `tail34_r096_r109_r113_eval_targets_as_training`
- `r137_or_r139_switch_predictions_as_training_labels`
- `r139_task250_confidence_as_threshold_target`

## Calibration Features

- `repair_binding_status`
- `repair_distance_ratio`
- `repair_confidence_text_bucket`
- `verifier_router_repair_agreement`
- `direct_majority_contradiction`
- `option_text_exactness`
- `candidate_source_count`
- `numeric_distance_bucket`

## Success Gates

- `offline_calibration_uses_no_forbidden_source`
- `same_four_task_clean_harm_0_on_task_8_task_188`
- `same_four_task_clean_recovery_task_250`
- `same_four_task_noisy_task_108_not_regressed`
- `broad_tail34_still_blocked_until_four_task_gate_passes`

## Interpretation

R141 does not change the final repair threshold. It freezes a non-leaky calibration route so any future confidence change is supported by non-tail34 evidence or synthetic controls rather than task250-specific tuning. The next step is an offline export/checker before any further API smoke.
