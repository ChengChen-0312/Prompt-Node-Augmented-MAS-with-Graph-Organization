# R073 Surgical Cascade Trigger Replay

**Boundary**: `replay_over_r072_fresh_cascade_traces_not_new_api_run`. This is a replay over R072 fresh cascade traces, not a new API run.

## Rule

Run cascade views only when baseline is invalid, or when baseline has weak final support, low direct coverage, at most two non-PromptNode outputs, and no direct option conflict.

## Summary

- Selected accuracy: `29/34`
- Internal ARG baseline: `27/34`
- Delta vs baseline: `+2`
- Multi-view triggered tasks: `10/34`
- View calls: `21/40`
- Switches: `2`
- Fix/Harm: `2/0`
- Clean: `26/28`
- Clean Fix/Harm: `2/0`
- Estimated cost: `$1.618315`
- Saving vs R072: `$1.207725`
- Relative cost vs ARG: `1.73x`

## Boundary

R073 is a trigger-compression hypothesis. It can justify a fresh API run or train-time selector target, but it cannot be reported as measured billing.
