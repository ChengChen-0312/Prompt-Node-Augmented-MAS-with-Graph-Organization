# R216 Non-Abstain Router-Final Target Design

**Claim boundary**: design only. No target export, no API evaluation, and no accuracy claim.

## Why This Is Needed

R211-R214 made router-final safe and auditable, but all labels are still `abstain/NONE`. That cannot improve accuracy. The next method step needs non-abstain router-final targets without leaking gold labels or overfitting tail34.

## Existing Evidence

| Source | Evidence | Use |
|---|---|---|
| R112 first200 feature export | `200` rows, `11` `switch_to_objective`, `0` policy-input violations | train/proxy source |
| R096 tail34 policy targets | `34` rows, `2` switches: `task_108`, `task_250`, `0` input violations | frozen eval only |
| R109 rule distillation | `34/34` agreement with R096 | rule specification |
| R113 proxy rule | train `200/200`, frozen tail34 `34/34` target agreement | reproducibility evidence, not accuracy |

## Target Mapping

| Source action | Router action | Target option label |
|---|---|---|
| `fallback_to_arg` | `abstain` | `NONE` |
| `switch_to_objective` | `switch_to_objective` | `policy_input.objective_prediction` |

This makes router-final answer-changing labels possible while keeping them tied to label-free objective-safety evidence.

## Model-Visible Fields

Allowed:

- `policy_input.baseline_prediction`
- `policy_input.objective_prediction`
- `policy_input.objective_prediction_differs_from_baseline`
- `policy_input.objective_top_score`
- `policy_input.baseline_direct_majority`
- `policy_input.baseline_direct_majority_count`
- `policy_input.baseline_direct_valid_vote_count`
- `policy_input.baseline_direct_votes_split`
- `promptedge_permissions`
- `router_final_schema.allowed_option_labels`

Forbidden:

- `task_id`
- `analysis`
- `clean_label`
- `gold_binding_status`
- `rationale_issue`
- `true_answer`
- `is_correct`
- `correctness`
- `audit_label`
- `source_run`

## Split Discipline

- R112 first200 can be used for target extraction and training/proxy work.
- R096/R109 tail34 must remain frozen evaluation targets only.
- Tail34 switch labels cannot be used to tune thresholds.
- Any future MMLU claim must come from held-out/random transfer evaluation, not from these AQuA targets.

## Risks

- `objective_prediction` is a model-derived candidate label. It is allowed, but the paper must explain that it is not gold.
- The rule still depends on multi-view objective features, so it is not yet a cheap deployment.
- A non-abstain target may improve AQuA replay while still failing MMLU transfer; do not overclaim robustness.

## Next

R217 should implement a target extractor with tests:

1. `switch_to_objective` rows produce `router_action=switch_to_objective`.
2. `fallback_to_arg` rows produce `router_action=abstain`.
3. `task_id`, `analysis`, gold/correctness/audit fields stay out of `model_visible_fields`.
4. tail34 rows are marked `frozen_eval_only`, not training.
