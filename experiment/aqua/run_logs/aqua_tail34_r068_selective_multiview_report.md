# R068 Selective Multi-View PromptNode Trigger

**Claim boundary**: `selective_multiview_replay_not_fresh_api_run`. This is a replay/cost estimate over existing tail34 traces, not a fresh API run.

## Summary

- Selected accuracy: `31/34`
- ARG baseline: `28/34`
- Full objective selector: `31/34`
- Fix/Harm: `3/0`
- Clean: `28/28`
- Clean Fix/Harm: `1/0`
- Multi-view runs: `22/34`
- Switch tasks: `task_114, task_59, task_108, task_250`

## Cost Estimate

- Estimated selective cost: `$3.597409`
- Full multi-view cost: `$5.050805`
- Cost saving vs full multi-view: `$1.453396`
- Relative cost vs ARG: `3.86x`

## Triggered Tasks

| Task | ARG | Objective | Selected | Source | Trigger reasons | Solved |
| --- | ---: | ---: | ---: | --- | --- | --- |
| task_114 | C | D | D | objective_top | r063_trigger,missing_direct_vote_trigger | True |
| task_56 | A | A | A | baseline | r063_trigger,missing_direct_vote_trigger | True |
| task_107 | B | B | B | baseline | missing_direct_vote_trigger | True |
| task_240 | B | B | B | baseline | r063_trigger,missing_direct_vote_trigger | True |
| task_179 | B | B | B | baseline | missing_direct_vote_trigger | True |
| task_183 | D | D | D | baseline | r063_trigger,missing_direct_vote_trigger | True |
| task_50 | C | C | C | baseline | missing_direct_vote_trigger | True |
| task_251 | A | A | A | baseline | missing_direct_vote_trigger | True |
| task_154 | C | C | C | baseline | r063_trigger,missing_direct_vote_trigger | True |
| task_59 | B | D | D | objective_top | missing_direct_vote_trigger | False |
| task_55 | A | A | A | baseline | missing_direct_vote_trigger | True |
| task_23 | A | A | A | baseline | missing_direct_vote_trigger | True |
| task_7 | C | C | C | baseline | missing_direct_vote_trigger | True |
| task_8 | E | E | E | baseline | r063_trigger,missing_direct_vote_trigger | True |
| task_108 | B | D | D | objective_top | r063_trigger,missing_direct_vote_trigger | True |
| task_139 | D | D | D | baseline | r063_trigger,missing_direct_vote_trigger | False |
| task_250 | A | E | E | objective_top | missing_direct_vote_trigger | True |
| task_35 | A | A | A | baseline | r063_trigger,missing_direct_vote_trigger | True |
| task_70 | C | C | C | baseline | r063_trigger,missing_direct_vote_trigger | True |
| task_6 | D | D | D | baseline | r063_trigger,missing_direct_vote_trigger | True |
| task_28 | B | B | B | baseline | missing_direct_vote_trigger | True |
| task_163 | D | D | D | baseline | missing_direct_vote_trigger | True |

## Interpretation

Replay estimate: run ARG for every task, trigger all four multi-view PromptNode traces only when ARG baseline traces show R063 risk or missing direct A-E vote, then apply the existing objective selector.

This keeps the R065 answer-level signal in replay while cutting the multi-view calls from `34/34` to `22/34`. It still needs a fresh integrated run before paper claims.
