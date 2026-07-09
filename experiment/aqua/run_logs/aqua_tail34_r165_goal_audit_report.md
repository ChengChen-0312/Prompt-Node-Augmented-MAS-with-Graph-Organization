# R165 SCI-Q2 Goal Audit

**Claim boundary**: Goal audit only. No API calls, no answer-accuracy result, and no SCI-Q2 readiness claim.

## Window

R165 audits R161-R165.

## Verdict

- Status: `aligned_but_not_sci_q2_ready`
- Drift: `false`
- Broad API allowed: `false`
- Next audit: `R170`

## Evidence

| Run | Evidence | Boundary |
| --- | --- | --- |
| R161 | Built a compatible MMLU ARG checkpoint. | Checkpoint only, no downstream accuracy claim. |
| R162 | MMLU STEM transfer ARG baseline reached `88/100`. | ARG baseline only, no PromptNode comparison. |
| R163 | Exported R001-style selective PromptNode/PromptEdge policy rows: `800` rows, `4` selective inserts, `796` fallback, `0` selector violations, `4` `.pt` files. | Offline target export only. |
| R164 | Loaded R163 `.pt` files through ARGDesigner forward path: dataset `4`, finite loss `true`. | Train-path smoke only. |

## Goal Alignment

- ARG-Designer remains the primary baseline.
- The same-model direction is preserved.
- PromptNodes remain first-class graph nodes before execution.
- Prompt-as-edge is now represented through typed PromptEdge metadata.
- Sync20 noisy-label overclaiming is avoided.

## Remaining Blockers

1. R162 is only an ARG transfer baseline; no PromptNode/PromptEdge transfer comparison exists.
2. R163 has only `4` selective positive targets, too sparse for a stable training claim.
3. R164 verifies compatibility only; it does not produce a trained selective model.
4. No held-out PromptNode/PromptEdge run currently exceeds ARG under matched budget.
5. Edge semantics are metadata-conditioned so far, not yet a learned edge-label loss.

## Correction

The next run should not launch broad API evaluation. R166 should expand selective training targets without leakage by separating:

- switch-critical positives: high-confidence cases where objective evidence differs from ARG;
- preserve-safe positives: high-margin PromptNode graph targets that do not require answer switching but teach stable PromptNode/PromptEdge structure;
- suppress/fallback negatives: low-margin, ambiguous, or dense-PN-risk cases.

R167 can then run bounded training smoke or short fine-tune. Broad API remains blocked until a learned or frozen selector has enough non-leaky training support.
