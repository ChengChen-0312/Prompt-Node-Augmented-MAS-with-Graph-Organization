# R071 Cascade Multi-View Replay over R069 Fresh Traces

**Boundary**: `cascade_replay_over_r069_fresh_traces_not_new_api_run`. No new API calls.

## Summary

- Accuracy: `29/34`
- Internal ARG baseline: `26/34`
- Fix/Harm: `3/0`
- Clean: `27/28`
- Clean Fix/Harm: `3/0`
- Multi-view triggered tasks: `25/34`
- Cascade view calls: `56/100`
- Switches: `3` (`task_56, task_8, task_188`)
- Estimated cost: `$2.599491`
- Estimated cost saving vs R069: `$1.309504`
- View-call reduction: `44.0%`

## Interpretation

Replay estimate over R069 fresh traces: run views sequentially, early-accept a valid ARG baseline after two supporting views, and switch only when the objective selector plus view support threshold is satisfied.

This preserves R069/R070 accuracy in replay while cutting PromptNode view calls. It is a cost model over existing traces, not a new integrated API result.
