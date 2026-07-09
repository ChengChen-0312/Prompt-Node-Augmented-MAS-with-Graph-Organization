# R074 Fresh Integrated Surgical Cascade PromptNode

**Boundary**: `fresh_integrated_cascade_multiview_promptnode_run`. This run executes cascade PromptNode views online and stops early when the rule fires.

## Summary

- Selected accuracy: `29/34`
- Internal ARG baseline: `28/34`
- Delta vs baseline: `+1`
- Multi-view triggered tasks: `13/34`
- View calls: `28/52`
- Trigger policy: `r073_surgical`
- Switches: `3`
- Fix/Harm: `1/0`
- Clean: `26/28`
- Clean Fix/Harm: `0/0`
- Noisy/Ambiguous: `3/6`
- Noisy/Ambiguous Fix/Harm: `1/0`
- Cost: `$1.828715`
- Prompt tokens: `129376`
- Completion tokens: `78789`

## Triggered Tasks

| Task | ARG | Selected | Source | View calls | Method | Trigger reasons | Solved |
| --- | ---: | ---: | --- | ---: | --- | --- | --- |
| task_114 | D | D | baseline_early_accept | 2 | None | r063_trigger,missing_direct_vote_trigger | True |
| task_56 | D | E | cascade_objective | 2 | router | r063_trigger,missing_direct_vote_trigger | False |
| task_166 | C | C | baseline_early_accept | 2 | None | r063_trigger,missing_direct_vote_trigger | True |
| task_183 | D | D | baseline_early_accept | 2 | None | r063_trigger,missing_direct_vote_trigger | True |
| task_143 | E | E | baseline_early_accept | 2 | None | r063_trigger,missing_direct_vote_trigger | True |
| task_251 | A | A | baseline_early_accept | 2 | None | r063_trigger,missing_direct_vote_trigger | True |
| task_59 | D | A | cascade_objective | 4 | calibrated | r063_trigger,missing_direct_vote_trigger | False |
| task_55 | A | A | baseline_early_accept | 2 | None | r063_trigger,missing_direct_vote_trigger | True |
| task_7 | C | C | baseline_early_accept | 2 | None | r063_trigger,missing_direct_vote_trigger | True |
| task_108 | A | D | cascade_objective | 2 | router | r063_trigger,missing_direct_vote_trigger | True |
| task_139 | D | D | baseline_early_accept | 2 | None | r063_trigger,missing_direct_vote_trigger | False |
| task_189 | B | B | baseline_early_accept | 2 | None | r063_trigger,missing_direct_vote_trigger | True |
| task_28 | B | B | baseline_early_accept | 2 | None | r063_trigger,missing_direct_vote_trigger | True |

## Interpretation

This fresh online cascade run excludes true answers, correctness fields, audit labels, and task-id-specific rules from trigger and cascade decisions.
