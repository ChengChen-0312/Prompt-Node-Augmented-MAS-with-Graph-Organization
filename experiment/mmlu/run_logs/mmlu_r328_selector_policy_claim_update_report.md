# R328 Selector Policy Claim Update

**Claim boundary**: R328 updates the claim matrix after the augmented selector dry run. It permits only an offline feasibility claim for graph-policy learning and a PromptEdge safety-feature claim, not an external accuracy claim.

## Selector Claim Permissions

- `offline_selector_feasibility_claim_allowed`: `True`
- `promptedge_safety_feature_claim_allowed`: `True`
- `external_accuracy_improvement_claim_allowed`: `False`
- `api_execution_allowed`: `False`
- `selector_training_main_result_allowed`: `False`
- `sci_q2_ready`: `False`

## Paper Text Guidance

- Describe the selector as a transparent offline graph-policy dry run.
- Use it to support that PromptNode type, PromptEdge text, permissions, and lifecycle actions are trainable graph features.
- Do not report it as a new MMLU/AQuA accuracy number until a prospective API or held-out replay is run.

- Next required run: `R329_case_study_extraction`
