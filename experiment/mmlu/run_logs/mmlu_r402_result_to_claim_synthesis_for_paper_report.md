# R402 Result-To-Claim Synthesis For Paper

**Claim boundary**: R402 applies the result-to-claim gate. The current evidence partially supports a narrowed paper: strong clean gains on AQuA and MMLU STEM, plus no-harm boundaries on mixed nonmath. It does not support broad general improvement claims.

- Overall claim supported: `partial`
- Supported claims: `['C1_aqua_audit_clean_gain', 'C2_mmlu_stem_gain', 'C4_mixed_nonmath_no_harm']`
- Partial claims: `['C3_history_optionbinding_pilot_gain']`
- Unsupported claims: `['C5_broad_general_improvement']`

## Suggested Claim

PromptNode/PromptEdge graph organization improves audited AQuA tail and MMLU STEM under ARG-Designer-matched settings, while learned safety gates preserve no-harm behavior on broader nonmath multiple-choice transfer. Do not claim universal improvement.

## Missing Evidence

- Larger prospective nonmath split with positive gain, not only no-harm.
- Independent integrity audit of all tables before manuscript submission.
- Cost-normalized deployment result if R065/R380 teacher-like paths are used in main text.
- Full paper figures/tables updated with exact claim boundaries.

- Next required run: `R403_paper_plan_update_after_claim_synthesis`
