# R072 Fresh Integrated Cascade Multi-View PromptNode

**Boundary**: `fresh_integrated_cascade_multiview_promptnode_run`. This run executes cascade PromptNode views online and stops early when the rule fires.

## Summary

- Selected accuracy: `29/34`
- Internal ARG baseline: `27/34`
- Delta vs baseline: `+2`
- Multi-view triggered tasks: `26/34`
- View calls: `58/104`
- Switches: `2`
- Fix/Harm: `2/0`
- Clean: `26/28`
- Clean Fix/Harm: `2/0`
- Noisy/Ambiguous: `3/6`
- Noisy/Ambiguous Fix/Harm: `0/0`
- Cost: `$2.826040`
- Prompt tokens: `192839`
- Completion tokens: `124123`

## Triggered Tasks

| Task | ARG | Selected | Source | View calls | Method | Trigger reasons | Solved |
| --- | ---: | ---: | --- | ---: | --- | --- | --- |
| task_114 | D | D | baseline_early_accept | 3 | None | r063_trigger | True |
| task_56 | None | A | cascade_objective | 3 | conservative | r063_trigger,missing_direct_vote_trigger | True |
| task_179 | B | B | baseline_early_accept | 2 | None | missing_direct_vote_trigger | True |
| task_166 | C | C | baseline_early_accept | 2 | None | missing_direct_vote_trigger | True |
| task_50 | C | C | baseline_early_accept | 2 | None | missing_direct_vote_trigger | True |
| task_251 | A | A | baseline_early_accept | 2 | None | missing_direct_vote_trigger | True |
| task_154 | C | C | baseline_early_accept | 2 | None | r063_trigger,missing_direct_vote_trigger | True |
| task_129 | D | D | baseline_early_accept | 2 | None | r063_trigger,missing_direct_vote_trigger | True |
| task_59 | B | B | baseline | 4 | None | r063_trigger,missing_direct_vote_trigger | False |
| task_55 | A | A | baseline_early_accept | 2 | None | r063_trigger,missing_direct_vote_trigger | True |
| task_23 | A | A | baseline_early_accept | 2 | None | r063_trigger,missing_direct_vote_trigger | True |
| task_7 | C | C | baseline_early_accept | 2 | None | missing_direct_vote_trigger | True |
| task_8 | D | D | baseline | 4 | None | r063_trigger,missing_direct_vote_trigger | False |
| task_108 | D | D | baseline_early_accept | 2 | None | missing_direct_vote_trigger | True |
| task_151 | E | E | baseline_early_accept | 2 | None | missing_direct_vote_trigger | True |
| task_22 | E | E | baseline_early_accept | 2 | None | missing_direct_vote_trigger | True |
| task_139 | D | D | baseline_early_accept | 2 | None | r063_trigger,missing_direct_vote_trigger | False |
| task_228 | C | C | baseline_early_accept | 2 | None | r063_trigger | False |
| task_26 | C | C | baseline_early_accept | 2 | None | r063_trigger,missing_direct_vote_trigger | True |
| task_188 | C | D | cascade_objective | 2 | conservative | r063_trigger,missing_direct_vote_trigger | True |
| task_35 | A | A | baseline_early_accept | 2 | None | r063_trigger,missing_direct_vote_trigger | True |
| task_70 | C | C | baseline_early_accept | 2 | None | missing_direct_vote_trigger | True |
| task_189 | B | B | baseline_early_accept | 2 | None | missing_direct_vote_trigger | True |
| task_6 | D | D | baseline_early_accept | 2 | None | r063_trigger,missing_direct_vote_trigger | True |
| task_28 | B | B | baseline_early_accept | 2 | None | r063_trigger,missing_direct_vote_trigger | True |
| task_163 | D | D | baseline_early_accept | 2 | None | r063_trigger,missing_direct_vote_trigger | True |

## Interpretation

This is the fresh online counterpart to R071. The trigger and cascade decisions exclude true answers, correctness fields, audit labels, and task-id-specific rules.
