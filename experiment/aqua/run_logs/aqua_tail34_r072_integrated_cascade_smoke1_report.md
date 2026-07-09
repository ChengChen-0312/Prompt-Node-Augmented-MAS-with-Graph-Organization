# R072 Fresh Integrated Cascade Multi-View PromptNode

**Boundary**: `fresh_integrated_cascade_multiview_promptnode_run`. This run executes cascade PromptNode views online and stops early when the rule fires.

## Summary

- Selected accuracy: `1/1`
- Internal ARG baseline: `1/1`
- Delta vs baseline: `+0`
- Multi-view triggered tasks: `1/1`
- View calls: `2/4`
- Switches: `0`
- Fix/Harm: `0/0`
- Clean: `0/0`
- Clean Fix/Harm: `0/0`
- Noisy/Ambiguous: `1/1`
- Noisy/Ambiguous Fix/Harm: `0/0`
- Cost: `$0.122255`
- Prompt tokens: `7795`
- Completion tokens: `5552`

## Triggered Tasks

| Task | ARG | Selected | Source | View calls | Method | Trigger reasons | Solved |
| --- | ---: | ---: | --- | ---: | --- | --- | --- |
| task_114 | D | D | baseline_early_accept | 2 | None | r063_trigger,missing_direct_vote_trigger | True |

## Interpretation

This is the fresh online counterpart to R071. The trigger and cascade decisions exclude true answers, correctness fields, audit labels, and task-id-specific rules.
