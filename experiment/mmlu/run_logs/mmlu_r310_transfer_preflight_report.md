# R310 Transfer Preflight

**Claim boundary**: R310 freezes transfer evidence and creates a fixed MMLU non-STEM preflight split. It does not run ARG/PromptNode inference on non-STEM and therefore does not support a non-STEM accuracy claim.

## Existing Evidence

- AQuA audit-clean: R065 `31/31` vs ARG `28/31`
- MMLU STEM main97: R306 `95/97` vs R304 `93/97`; cheap control threat `False`

## Non-STEM Preflight

- Records: `40` across `8` subjects
- Candidate records: `13`
- Candidate type counts: `{'instruction_ambiguity_verifier': 13, 'none': 27}`
- Accuracy available: `False`

## Claim Permissions

- `aqua_clean_claim_allowed`: `True`
- `mmlu_stem_diagnostic_claim_allowed`: `True`
- `mmlu_nonstem_accuracy_claim_allowed`: `False`
- `transfer_accuracy_claim_allowed`: `False`
- `training_claim_allowed`: `False`
- `sci_q2_ready`: `False`

## Next

- Run ARG baseline and expanded PromptNode/PromptEdge graph on the fixed R310 non-STEM split using gpt-4o-2024-08-06.
- Score official accuracy, fix/harm, token cost, and cost-normalized accuracy.
- If non-STEM is no-harm or positive, then proceed to ablations; if it is negative, narrow the paper claim to STEM/math-plus-semantic multiple choice.
