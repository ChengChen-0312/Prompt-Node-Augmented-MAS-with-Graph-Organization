# R205 Five-Iteration SCI-Q2 Goal Audit

**Claim boundary**: audit only. No API evaluation, no new accuracy claim, and no claim that PromptNode/PromptEdge exceeds ARG-Designer.

## Audit Decision

Status: `aligned_stop_mmlu_api_scale_return_to_method_and_paper`

No goal drift was detected, but the MMLU branch should not be scaled further right now. R202 random12 preserved accuracy (`11/12` vs `11/12`) and caused no harm, but it did not improve over ARG.

This means MMLU is useful as robustness/safety/negative evidence, not as the current main SCI-Q2 result.

## Authorized Next

- R206: method-redesign memo for learned edge ordering, router-final design, and projection ablations.
- R207: consolidate AQuA R065 and MMLU R181-R204 into claim/evidence table.
- R208: design negative controls.
- R209: prepare paper outline with AQuA R065 as main accuracy signal and MMLU as transfer evidence.
- R210: mandatory audit before new API or paper drafting scale-up.

## Forbidden

- Do not run more MMLU API before method redesign or R210 audit.
- Do not claim MMLU transfer improvement from R202.
- Do not present hybrid projection as fully learned edge-linking.
- Do not use sync20 as the main result.
