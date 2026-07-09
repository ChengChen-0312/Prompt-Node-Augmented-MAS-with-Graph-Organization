# R258 PromptNode/PromptEdge V2 Preflight

**Claim boundary**: Preflight only; no API execution, no accuracy claim, and no SCI-Q2 readiness claim.

- Records/tasks: `32` / `16`
- Variant counts: `{'arg_baseline_fixed': 16, 'proposed_v2_independent_guarded_pnpe': 16}`
- API-required records: `16`
- Leakage violations: `0`
- Estimated cost: `$0.050030` / cap `$0.450000`
- Preflight pass: `True`
- Authorized API next: `True`

## Boundary

This run only materializes v2 manifests and cost/leakage checks. It does not call the model.
