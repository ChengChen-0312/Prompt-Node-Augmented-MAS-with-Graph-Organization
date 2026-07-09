# R170 SCI-Q2 Goal Audit

**Claim boundary**: Goal audit only. Allows only a bounded smoke; no broad evaluation, no answer-accuracy result, and no SCI-Q2 readiness claim.

## Window

R170 audits R166-R170.

## Verdict

- Status: `aligned_allow_bounded_smoke_only`
- Drift: `false`
- Broad API allowed: `false`
- Bounded smoke allowed: `true`
- Maximum next API tasks: `4`
- Next audit: `R175`

## Evidence

| Run | Evidence | Boundary |
| --- | --- | --- |
| R166 | Expanded positives to `76`, with `4` switch-critical, `72` preserve-safe, `724` suppress/fallback, and `0` violations. | Offline target export only. |
| R167 | Short-trained 3 epochs; checkpoint saved; sampled graphs `64/64` with PromptNodes and `64/64` DAG. | Graph-generation audit only; PN rate `1.0` shows over-generation risk. |
| R168 | Selector reached eval agreement `0.995`, positive recall `0.971`, input violations `0`. | Target agreement only. |
| R169 | Froze default `fallback_to_arg` deployment protocol with PromptNode/PromptEdge evidence requirements. | Protocol only. |

## Goal Alignment

- The branch is back on the R001-style graph-generator training path.
- PromptNodes remain first-class graph nodes before execution.
- PromptEdge semantics are represented and audited.
- Sync20 noisy-label overclaiming is avoided.
- Broad API is still blocked.

## R171 Boundary

R171 may run only a bounded selector-gated smoke:

- maximum API tasks: `4`
- report internal ARG baseline, selector decision, generated PromptNode graph evidence, fix/harm, and cost
- stop if a clean harm appears
- do not claim SCI-Q2 readiness or broad superiority

The purpose is to test whether the R168 gate prevents R167's dense-PN overgeneration from becoming an answer-level harm.
