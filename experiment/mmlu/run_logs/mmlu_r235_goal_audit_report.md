# R235 Five-Iteration SCI-Q2 Goal Audit

**Claim boundary**: audit only. No new API, no superiority claim, and no SCI-Q2 readiness claim.

## Audit Window

| Run | Outcome |
|---|---|
| R231 | Built leakage-safe tiny diagnostic runner preflight |
| R232 | Independently authorized only the tiny diagnostic |
| R233 | Ran 8 API router calls and 12 deterministic controls |
| R234 | Decomposed failures by task, control, and clean/noisy audit |

## Goal Check

No drift was detected. The negative R233 result is useful because it prevents a weak prompt-router direction from being scaled into a fragile paper claim.

The result also reveals a direct mismatch with the SCI-Q2 goal: the current router does not learn when to abstain. It follows `objective_prediction` on every API-routed task, matches always-switch and node-only controls on `4/4` tasks, and harms one clean task.

## Decision

Status: `aligned_redirect_to_conservative_abstention_training_no_api`

API is blocked again. The next work must build a conservative abstention policy from existing label-free features and the observed failure constraints. The method should only switch when virtual-node evidence is strong enough to avoid clean harms; otherwise it should preserve ARG.

## Authorized Next

- R236: derive a conservative abstention policy from existing label-free features and R234 failure constraints, no API.
- R237: apply the conservative policy to R233 and R218/R221 records offline, no API.
- R238: materialize updated router-final manifests and controls with conservative switch rules, no API.
- R239: update claim matrix and paper plan after offline conservative-policy evidence.
- R240: next mandatory goal audit.

## Forbidden

- No further API before R240 unless offline policy evidence eliminates the clean-harm failure mode.
- No superiority claim over ARG or controls.
- No SCI-Q2 readiness claim.
- No prompt-only router expansion without a learned or explicit abstention boundary.
