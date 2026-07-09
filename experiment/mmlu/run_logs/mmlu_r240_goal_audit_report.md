# R240 Five-Iteration SCI-Q2 Goal Audit

**Claim boundary**: audit only. No API, no superiority claim, and no SCI-Q2 readiness claim.

## Audit Window

| Run | Outcome |
|---|---|
| R236 | Derived conservative abstention policies offline; selected `baseline_consensus_guard_top3` |
| R237 | Replayed policy on R218 mini-manifest and R233 subset |
| R238 | Exported conservative proposed/control manifests |
| R239 | Updated claim matrix and paper plan |

## Goal Check

No drift was detected. The work moved from a failed prompt-only router toward the user's intended direction: a graph-policy/selector that decides when PromptNode/PromptEdge evidence can affect the MAS output.

The current evidence is promising but still not sufficient for SCI-Q2. R236-R237 are offline replay results, not trained policy or live held-out evaluation.

## Decision

Status: `aligned_continue_train_time_abstention_policy_no_api`

API remains blocked. The next stage should fit an interpretable train-time abstention policy from label-free PN/PE features and evaluate it on frozen splits and controls before any further model calls.

## Authorized Next

- R241: build train/frozen feature table for abstention policy, no API.
- R242: fit interpretable train-time abstention policy and evaluate frozen split, no API.
- R243: compare trained policy against R238 controls and R236 explicit rule, no API.
- R244: extract case studies for fix, abstain-protected clean case, and no-fix cases, no API.
- R245: next mandatory goal audit.

## Forbidden

- No further API before a trained/fitted policy passes frozen-eval and control checks.
- No superiority claim over ARG from offline replay alone.
- No SCI-Q2 readiness claim.
- No prompt-only router expansion.
