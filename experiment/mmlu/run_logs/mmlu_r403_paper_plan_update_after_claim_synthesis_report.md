## R402 Claim Synthesis Update

**Verdict**: `partial` support for a narrowed SCI-Q2 paper claim.

| Claim ID | Status | Paper Use | Evidence |
|---|---|---|---|
| `C1_aqua_audit_clean_gain` | `supported` | `main_result` | AQuA audit-clean tail31: ARG 28/31 vs PromptNode 31/31. |
| `C2_mmlu_stem_gain` | `supported` | `main_transfer_result` | MMLU STEM main97: ARG 88/97 vs PromptNode 95/97, fix/harm 7/0. |
| `C3_history_optionbinding_pilot_gain` | `partial` | `mechanism_pilot_or_appendix` | Fresh history pilot R380/R381: ARG 21/24 vs hybrid 24/24, but single subject and small sample. |
| `C4_mixed_nonmath_no_harm` | `supported` | `boundary_no_harm_result` | Larger mixed nonmath R395/R396: ARG 41/48 vs hybrid 41/48, harm 0. |
| `C5_broad_general_improvement` | `unsupported` | `forbidden_claim` | Mixed nonmath larger split has no positive delta; contrastive branch failed safely. |

**Allowed main text framing**:

PromptNode/PromptEdge graph organization improves audited AQuA tail and MMLU STEM under ARG-Designer-matched settings, while learned safety gates preserve no-harm behavior on broader nonmath multiple-choice transfer. Do not claim universal improvement.

**Forbidden framing**:

- Do not claim broad general improvement across all nonmath/multiple-choice tasks.
- Do not treat the R380 history pilot as a main transfer result.
- Do not integrate the failed R400 contrastive branch.

**Missing before submission freeze**:

- Larger prospective nonmath split with positive gain, not only no-harm.
- Independent integrity audit of all tables before manuscript submission.
- Cost-normalized deployment result if R065/R380 teacher-like paths are used in main text.
- Full paper figures/tables updated with exact claim boundaries.
