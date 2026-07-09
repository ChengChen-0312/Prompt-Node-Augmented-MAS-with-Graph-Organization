# R261 Result-to-Claim Update After MMLU Transfer V1/V2

**Claim boundary**: claim-package update only. No API, no new accuracy claim, and no SCI-Q2 readiness claim.

## Claim Updates

| Claim | Status | Evidence |
|---|---|---|
| AQuA held-out selector can improve over ARG | Supported offline/scope-limited | R065 tail34 `31/34` vs ARG `28/34`; R242 frozen replay `29/34` vs `28/34` |
| PromptNode lifecycle and edge actions are represented | Supported as annotation | R247 `75` annotations; lifecycle update/prune/merge/compress/upgrade; edge read/forward/write |
| MMLU transfer probe protocol is leakage-safe | Supported as protocol | R248-R252/R258 feature tables and preflight, leakage `0` |
| MMLU PN/PE v1 transfer beats controls | Not supported | R253-R254: proposed `10/16`, plain `12/16`, node-only `11/16` |
| MMLU guarded PN/PE v2 fixes v1 | Not supported | R259: v2 `9/16`, fix/harm `1/0`, lower than v1 and controls |
| PromptEdge text independently improves accuracy | Not supported | R243 and R253-R254: node-only matches or exceeds proposed |
| Current package is SCI-Q2 ready | Not supported | Needs stronger held-out/live graph-policy evidence, cost-normalized tables, citation audit, and paper draft |

## Paper Framing

The manuscript should not claim transfer superiority. MMLU should be presented as a rigorous negative-control and failure-analysis section: the method is promising on AQuA selector evidence, but prompt-only PN/PE transfer is not robust enough.

The strongest claim remains:

> First-class PromptNode/PromptEdge graph primitives plus a label-free selector can improve AQuA held-out replay under strict claim boundaries.

The next paper package should emphasize reproducibility, cost, negative controls, and honest limitations instead of expanding API experiments.

## Next

R262 should generate paper-ready tables for the current evidence package.
