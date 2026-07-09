# R308 Goal Audit After Non-Math PromptNode Expansion

**Claim boundary**: Goal-audit checkpoint only. R308 does not train, does not call APIs, and does not add accuracy-bearing rules; it verifies that R303-R307 still serve the SCI-Q2 PromptNode graph-policy goal.

## Current Best

- ARG main97: `88/97`
- R304 symbolic/math PromptNode stack: `93/97`
- R306 expanded non-math stack: `95/97`
- R306 vs ARG delta: `+7`
- R306 vs R304 non-math delta: `+2`
- Cumulative fix/harm vs ARG on main97: `7/0`

## Goal Alignment

- `aligned_with_promptnode_goal`: `True`
- `nonmath_promptnodes_added`: `True`
- `math_patch_risk_reduced`: `True`
- `audit_excluded_policy_respected`: `True`
- `training_deferred_as_requested`: `True`
- `controls_and_transfer_not_done`: `True`
- `sci_q2_goal_not_yet_satisfied`: `True`

## PromptNode Coverage

- Non-math families available: `6`
- Non-math candidate records: `15`
- Non-math switches: `MMLU-machine_learning_test-81, MMLU-conceptual_physics_test-41`

## Training Gate

- `training_authorized`: `False`
- `mmlu_main97_claim`: `diagnostic_supported`
- `transfer_generalization_claim`: `not_yet_supported`
- `sci_q2_ready`: `False`
- `paper_main_claim_allowed`: `False`

## Risks

- R306 improves MMLU main97, but negative controls have not yet ruled out route-budget or random-forward effects.
- The non-math library exists, but only two non-math switches currently affect accuracy; stronger coverage is needed before training.
- AQuA and non-STEM transfer are still untested under the expanded node catalog.
- PromptEdge constraints are specified conceptually, but not yet isolated in a control or ablation.

## Next Required Run

`R309_negative_controls`

- Run no-nonmath, random-forward, always-forward, no-safety-gate, random-type, and no-lifecycle controls.
- Reject training if any cheap control matches or exceeds R306 without worse harm.
- Then run per-node ablations and at least one non-AQuA/non-STEM transfer split before authorizing training.
