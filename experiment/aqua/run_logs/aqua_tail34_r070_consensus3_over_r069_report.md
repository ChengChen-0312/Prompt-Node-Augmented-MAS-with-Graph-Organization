# R070 Consensus-3 Selector over R069 Fresh Traces

**Boundary**: `replay_over_r069_fresh_traces_not_new_api_run`. No new API calls.

## Summary

- Accuracy: `29/34`
- Internal ARG baseline: `26/34`
- Fix/Harm: `3/0`
- Clean: `27/28`
- Clean Fix/Harm: `3/0`
- Multi-view runs inherited from R069: `25/34`
- Switches: `3` (`task_56, task_8, task_188`)
- Cost inherited from R069: `$3.908995`

## Interpretation

Replays a stricter consensus switch rule over R069 fresh traces. It removes the unsupported task_59 switch while preserving accuracy, but does not reduce API cost because it still assumes R069 views were run.
