# R063 Risk-Aware PromptNode Replay Report: tail34

## Boundary

This is an exploratory replay over existing R062 baseline records and dense R060 PromptNode traces.
The risk features and gate do not read `true_answer`, `is_solved`, task ids, or clean/noisy labels.
Because tail34 has already informed R063 design, this cannot be treated as a fresh held-out accuracy claim.

## Inputs

- Baseline file: `experiment/aqua/aqua_tail34_r062_integrated_selective_results.jsonl`
- Dense PromptNode file: `experiment/aqua/aqua_tail34_r058_router_contract_terminal_results.jsonl`

## Summary

- Selected accuracy: `28/34` = `82.35%`
- Baseline accuracy: `28/34` = `82.35%`
- Dense PromptNode accuracy: `25/34` = `73.53%`
- PromptNode run count: `12/34`
- PromptNode switch count: `1`
- Fix/harm vs baseline: `0/0`

## PromptNode Would Run

| task_id | baseline | dense PN | selected | risk reasons | selection reason | block reason | solved |
| --- | --- | --- | --- | --- | --- | --- | --- |
| task_56 | E | D | baseline | low_direct_coverage |  | router_not_compatible | False |
| task_251 | A | A | baseline | low_direct_coverage |  | router_not_compatible | True |
| task_154 | C | C | baseline | low_direct_coverage |  | router_not_compatible | True |
| task_59 | None | None | baseline | final_direct_mismatch,invalid_baseline_prediction,low_direct_coverage |  | invalid_promptnode_prediction | False |
| task_55 | A | A | baseline | low_direct_coverage |  | router_not_compatible | True |
| task_23 | A | A | baseline | low_direct_coverage |  | router_not_compatible | True |
| task_108 | D | D | promptnode | direct_conflict | strong_router_resolves_conflict |  | True |
| task_139 | D | D | baseline | low_direct_coverage |  | no_strong_router_contract | False |
| task_250 | E | A | baseline | final_direct_mismatch |  | no_strong_router_contract | True |
| task_188 | D | C | baseline | low_direct_coverage |  | router_not_compatible | True |
| task_28 | B | B | baseline | low_direct_coverage |  | router_not_compatible | True |
| task_163 | D | D | baseline | low_direct_coverage |  | router_not_compatible | True |
