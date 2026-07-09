# R229 Claim Matrix And Paper Plan Update

**Claim boundary**: planning and claim-boundary update only. No API evaluation, no accuracy claim, and no SCI-Q2 readiness claim.

## Updated Claim Matrix

| Claim | Status | Evidence |
|---|---|---|
| Negative controls are executable as artifacts | Supported as artifacts | R221: 4 manifests, `268` rows |
| Control manifests pass leakage checks | Supported | R222: `0` leakage violations |
| Cost-matched ARG comparator is protocol-ready | Supported as protocol | R226: cost cap `$0.45`, estimated ARG re-query cost `$0.121684` for 4 tasks |
| Proposed/control router-final variants can emit uniform runtime logs | Supported as dry-run infrastructure | R228: `335` records, `106` would-switch, `0` leakage violations, `0` missing fields |
| Router-final improves answer accuracy over controls | Not supported | No model/API answer-level evaluation yet |
| Router-final improves over ARG under matched cost | Not supported | Cost-matched ARG is a protocol artifact, not an executed comparison |
| Current package is SCI-Q2 ready | Not supported | Accuracy, robustness, lifecycle case studies, and citation audit remain incomplete |

## Paper Plan Impact

R229 changes the paper plan from "controls must be built" to "controls and runtime accounting are ready for a small pre-registered diagnostic." The method story remains PromptNode/PromptEdge as first-class graph primitives with prompt-as-edge support, but the empirical story must still be framed as incomplete until answer-level results exist.

## Next Decision Point

R230 must check the goal before any API use. The audit should decide whether the infrastructure is now sufficient to authorize a tiny diagnostic on the pre-registered cost-matched set. If authorized, the diagnostic must compare:

- proposed router-final,
- abstain-only router,
- random-switch same-rate,
- always-switch-to-objective,
- node-only/no-PromptEdge-text,
- cost-matched ARG re-query.

Any result must report accuracy, clean/noisy split if available, fix/harm, clean fix/harm, cost, and cost-normalized metrics. Superiority claims remain forbidden until those numbers exist.
