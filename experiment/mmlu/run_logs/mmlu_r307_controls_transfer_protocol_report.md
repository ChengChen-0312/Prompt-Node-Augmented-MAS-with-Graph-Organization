# R307 Controls And Transfer Protocol

**Claim boundary**: Protocol freeze only. It blocks training until negative controls, ablations, and at least two transfer settings are evaluated.

- Current best: `R306` main97 `95/97` with fix/harm `2/0`
- Training authorized next: `False`

## Negative Controls

- `no_nonmath_promptnodes`: R304 baseline stack without R305/R306 non-math nodes.
- `random_forward`: Randomly forward the same number of candidate nodes as R306; must not match R306 gain.
- `always_forward`: Forward every non-empty candidate; expected to expose harm if SafetyGate is removed.
- `no_safety_gate`: Verifier candidates bypass PN_SafetyGate and go straight to router.
- `random_promptnode_type`: Replace each candidate type with a random type while keeping candidate label hidden from gate.
- `no_lifecycle`: Disable compress/prune/upgrade annotations and test whether graph policy degrades.

## Required Transfer Splits

- `AQuA_tail34_audit_clean`: Run the same node catalog on AQuA tail34 audit-clean with task_59/task_139/task_228 excluded or appendix-only.
- `MMLU_non_STEM_multiple_choice`: Create a non-STEM multiple-choice split to test instruction/semantic nodes outside formula-heavy STEM.
- `MMLU_STEM_main97`: Retain current main97 as development/diagnostic split, not the only evidence.

## Training Entry Criteria

- `main97_no_harm`: R306 or later keeps main official and audit-clean harm at 0.
- `controls_pass`: No negative control beats the gated method at equal switch budget.
- `transfer_not_negative`: At least one non-AQuA transfer split has positive gain or statistically non-negative delta.
- `type_coverage`: At least four PromptNode families contribute candidates, with at least two non-symbolic families.
- `leakage_pass`: Training inputs exclude task_id, true_answer, correctness, and audit labels.

## Next Runs

- R308 random/always-forward negative controls
- R309 per-node ablation table
- R310 AQuA transfer stack replay
- R311 MMLU non-STEM transfer split preflight
