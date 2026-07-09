# R061 Selective PromptNode Activation Report: sync20

## Boundary

This is a label-free replay over existing ARG and R058 traces. It is not a fresh integrated API run.
The activation gate does not read `true_answer`, `is_solved`, task ids, or clean/noisy audit labels.

## Inputs

- Baseline file: `experiment/aqua/aqua_sync20_eval20_results.jsonl`
- PromptNode file: `experiment/aqua/aqua_sync20_r055_graph_policy_router_contract_terminal_results.jsonl`

## Summary

- Selected accuracy: `17/20` = `85.00%`
- ARG baseline accuracy: `17/20` = `85.00%`
- R058 PromptNode accuracy if dense: `17/20` = `85.00%`
- Delta vs baseline: `0`
- Fix/harm vs baseline: `0/0`
- PromptNode switches: `0`

## Switched Tasks

| task_id | baseline | promptnode | selected | router | binding | solved |
| --- | --- | --- | --- | --- | --- | --- |
| none | - | - | - | - | - | - |

## Claim Boundary

R061 may support a selective-activation hypothesis only as replay evidence. A paper-level system claim still requires a fresh integrated evaluator that runs the same model setting and activates PromptNodes online under this gate.
