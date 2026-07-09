# R312 Non-STEM Safety Replay

**Claim boundary**: R312 is an offline safety replay over R311 raw outputs. It supports a non-STEM no-harm boundary only; it does not support a broad non-STEM improvement claim.

- ARG baseline: `37/40`
- Safety replay: `37/40`
- Delta vs ARG: `0`
- Fix/harm vs ARG: `0/0`
- No harm: `True`

## Interpretation

The current non-STEM PromptNodes are useful as warning/lifecycle nodes but not as answer-overriding nodes. Training should not learn to switch from warning-only candidates.

## Claim Permissions

- `nonstem_no_harm_claim_allowed`: `True`
- `nonstem_improvement_claim_allowed`: `False`
- `broad_general_promptnode_claim_allowed`: `False`
- `training_authorized`: `False`
- `sci_q2_ready`: `False`
