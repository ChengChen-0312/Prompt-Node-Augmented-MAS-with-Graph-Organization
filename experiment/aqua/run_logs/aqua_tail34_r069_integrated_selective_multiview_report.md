# R069 Fresh Integrated Selective Multi-View PromptNode

**Boundary**: `fresh_integrated_selective_multiview_promptnode_run`. This run executes ARG first, triggers multi-view PromptNodes online, and applies the label-free objective selector.

## Summary

- Selected accuracy: `29/34`
- ARG baseline inside R069: `26/34`
- Delta vs baseline: `+3`
- Multi-view runs: `25/34`
- Switches: `4`
- Fix/Harm: `3/0`
- Clean: `27/28`
- Clean Fix/Harm: `3/0`
- Noisy/Ambiguous: `2/6`
- Noisy/Ambiguous Fix/Harm: `0/0`
- Cost: `$3.908995`
- Prompt tokens: `265865`
- Completion tokens: `171978`

## Triggered Tasks

| Task | ARG | Selected | Source | Method | Top score | Trigger reasons | Solved |
| --- | ---: | ---: | --- | --- | ---: | --- | --- |
| task_56 | None | A | objective_top | router | 2 | r063_trigger,missing_direct_vote_trigger | True |
| task_107 | B | B | baseline | None | 2 | r063_trigger | True |
| task_166 | C | C | baseline | None | 3 | missing_direct_vote_trigger | True |
| task_183 | D | D | baseline | None | 3 | r063_trigger,missing_direct_vote_trigger | True |
| task_143 | E | E | baseline | None | 3 | missing_direct_vote_trigger | True |
| task_251 | A | A | baseline | None | 3 | missing_direct_vote_trigger | True |
| task_154 | C | C | baseline | None | 3 | r063_trigger,missing_direct_vote_trigger | True |
| task_129 | D | D | baseline | None | 3 | missing_direct_vote_trigger | True |
| task_59 | None | B | objective_top | router | 2 | r063_trigger,missing_direct_vote_trigger | False |
| task_55 | A | A | baseline | None | 2 | missing_direct_vote_trigger | True |
| task_7 | C | C | baseline | None | 3 | r063_trigger,missing_direct_vote_trigger | True |
| task_8 | None | E | objective_top | router | 2 | r063_trigger,missing_direct_vote_trigger | True |
| task_108 | D | D | baseline | None | 3 | r063_trigger,missing_direct_vote_trigger | True |
| task_151 | E | E | baseline | None | 3 | missing_direct_vote_trigger | True |
| task_139 | D | D | baseline | None | 2 | missing_direct_vote_trigger | False |
| task_250 | None | None | baseline | None | 3 | r063_trigger,missing_direct_vote_trigger | False |
| task_173 | C | C | baseline | None | 3 | missing_direct_vote_trigger | True |
| task_26 | C | C | baseline | None | 3 | missing_direct_vote_trigger | True |
| task_188 | C | D | objective_top | candidate | 2 | missing_direct_vote_trigger | True |
| task_35 | A | A | baseline | None | 3 | r063_trigger,missing_direct_vote_trigger | True |
| task_70 | C | C | baseline | None | 3 | missing_direct_vote_trigger | True |
| task_189 | B | B | baseline | None | 3 | r063_trigger,missing_direct_vote_trigger | True |
| task_6 | D | D | baseline | None | 3 | missing_direct_vote_trigger | True |
| task_28 | B | B | baseline | None | 3 | r063_trigger,missing_direct_vote_trigger | True |
| task_163 | D | D | baseline | None | 3 | missing_direct_vote_trigger | True |

## Interpretation

This is the prospective counterpart to R068. The trigger excludes true answers, correctness, clean/noisy labels, and task-id-specific rules. Post-hoc accuracy and audit splits are diagnostics only.
