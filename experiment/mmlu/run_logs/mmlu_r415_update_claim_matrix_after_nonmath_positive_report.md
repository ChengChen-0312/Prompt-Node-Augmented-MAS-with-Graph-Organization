## R415 Nonmath Positive Claim Update

**Verdict**: `partial+` support for a narrowed SCI-Q2 paper claim after a fresh targeted nonmath result.

| Claim ID | Status | Paper Use | Evidence |
|---|---|---|---|
| `C1_aqua_audit_clean_gain` | `supported` | `main_result` | AQuA audit-clean tail31: ARG 28/31 vs PromptNode 31/31. |
| `C2_mmlu_stem_gain` | `supported` | `main_transfer_result` | MMLU STEM main97: ARG 88/97 vs PromptNode 95/97, fix/harm 7/0. |
| `C3_history_optionbinding_pilot_gain` | `partial` | `mechanism_pilot_or_appendix` | Fresh history pilot R380/R381: ARG 21/24 vs hybrid 24/24, but single subject and small sample. |
| `C4_mixed_nonmath_no_harm` | `supported` | `boundary_no_harm_result` | Larger mixed nonmath R395/R396: ARG 41/48 vs hybrid 41/48, harm 0. |
| `C5_broad_general_improvement` | `unsupported` | `forbidden_claim` | Mixed nonmath larger split has no positive delta; contrastive branch failed safely. |
| `C6_definition_challenge_fresh_positive` | `supported_narrow` | `targeted_nonmath_transfer_result_or_appendix` | Fresh DefinitionChallenge split: ARG 21/24 vs DefinitionChallenge 22/24; candidate pool 21/24; fix/harm/wrong-forward 1/0/0. |

**Updated allowed framing**:

PromptNode/PromptEdge graph organization improves audited AQuA and MMLU STEM under ARG-Designer-matched settings, and a targeted DefinitionChallenge PromptNode/PromptEdge gate gives a fresh positive no-harm result on concept-definition nonmath transfer. Broader nonmath improvement remains unclaimed.

**Still forbidden**:

- Do not claim broad nonmath or universal multiple-choice improvement.
- Do not treat the same-split R411 gate ablation as evidence.
- Do not treat the targeted DefinitionChallenge result as a substitute for independent integrity audit.

**Remaining gaps before submission freeze**:

- Independent experiment integrity audit before paper claim authorization.
- Cost-normalized table that includes R065, R306, R413, and plain-requery controls.
- A larger nonmath split is still needed before claiming broad nonmath transfer.
- Final paper figures/tables updated with exact claim boundaries.
