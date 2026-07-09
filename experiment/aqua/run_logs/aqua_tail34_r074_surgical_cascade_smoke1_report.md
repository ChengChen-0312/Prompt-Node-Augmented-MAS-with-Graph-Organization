# R072 Fresh Integrated Cascade Multi-View PromptNode

**Boundary**: `fresh_integrated_cascade_multiview_promptnode_run`. This run executes cascade PromptNode views online and stops early when the rule fires.

## Summary

- Selected accuracy: `1/1`
- Internal ARG baseline: `0/1`
- Delta vs baseline: `+1`
- Multi-view triggered tasks: `1/1`
- View calls: `2/4`
- Switches: `1`
- Fix/Harm: `1/0`
- Clean: `0/0`
- Clean Fix/Harm: `0/0`
- Noisy/Ambiguous: `1/1`
- Noisy/Ambiguous Fix/Harm: `1/0`
- Cost: `$0.123275`
- Prompt tokens: `7909`
- Completion tokens: `5582`

## Triggered Tasks

| Task | ARG | Selected | Source | View calls | Method | Trigger reasons | Solved |
| --- | ---: | ---: | --- | ---: | --- | --- | --- |
| task_114 | C | D | cascade_objective | 2 | router | r063_trigger,missing_direct_vote_trigger | True |

## Interpretation

This is the fresh online counterpart to R071. The trigger and cascade decisions exclude true answers, correctness fields, audit labels, and task-id-specific rules.
