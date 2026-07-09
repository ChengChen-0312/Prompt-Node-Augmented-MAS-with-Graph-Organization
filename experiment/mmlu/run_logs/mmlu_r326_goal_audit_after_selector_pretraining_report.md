# R326 Goal Audit After Selector Pretraining

**Claim boundary**: R326 is the required five-iteration audit after R321-R325. The direction remains aligned with the SCI-Q2 goal because training is being converted into a graph-policy selector with leakage controls and hard negatives. However, selector training is not yet a paper claim.

## Alignment

- `still_aligned_with_sci_q2_goal`: `True`
- `paper_evidence_table_created`: `True`
- `selector_manifest_frozen_without_leakage`: `True`
- `promptnode_first_class_features_preserved`: `True`
- `promptedge_and_lifecycle_features_preserved`: `True`
- `hard_negative_gap_detected_and_addressed`: `True`
- `warning_only_override_block_preserved`: `True`
- `training_not_overclaimed`: `True`

## Claim Permissions

- `offline_selector_retraining_allowed`: `True`
- `api_execution_allowed`: `False`
- `selector_training_paper_claim_allowed`: `False`
- `aqua_clean_improvement_allowed`: `True`
- `mmlu_stem_improvement_allowed`: `True`
- `mmlu_nonstem_no_harm_allowed`: `True`
- `broad_general_promptnode_claim_allowed`: `False`
- `sci_q2_ready`: `False`

## Course Correction

- Continue with offline augmented selector retraining before any API run.
- Treat R323 perfect accuracy as feasibility only because R324 showed easy-feature separability.
- Use R325 hard negatives to force the selector to learn PromptEdge text and lifecycle safety, not just candidate confidence.
- Keep the paper claim restricted to AQuA audit-clean, MMLU STEM positive, and non-STEM no-harm until prospective transfer improves.

- Next required run: `R327_augmented_selector_retraining_dry_run`
