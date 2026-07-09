# R061 Selective PromptNode Activation Report: tail34

## Boundary

This is a label-free replay over existing ARG and R058 traces. It is not a fresh integrated API run.
The activation gate does not read `true_answer`, `is_solved`, task ids, or clean/noisy audit labels.

## Inputs

- Baseline file: `experiment/aqua/aqua_tail34_arg_baseline_results.jsonl`
- PromptNode file: `experiment/aqua/aqua_tail34_r058_router_contract_terminal_results.jsonl`

## Summary

- Selected accuracy: `29/34` = `85.29%`
- ARG baseline accuracy: `28/34` = `82.35%`
- R058 PromptNode accuracy if dense: `25/34` = `73.53%`
- Delta vs baseline: `1`
- Fix/harm vs baseline: `1/0`
- PromptNode switches: `1`

## Switched Tasks

| task_id | baseline | promptnode | selected | router | binding | solved |
| --- | --- | --- | --- | --- | --- | --- |
| task_108 | B | D | D | D | EXACT_MATCH | True |

## Claim Boundary

R061 may support a selective-activation hypothesis only as replay evidence. A paper-level system claim still requires a fresh integrated evaluator that runs the same model setting and activates PromptNodes online under this gate.
