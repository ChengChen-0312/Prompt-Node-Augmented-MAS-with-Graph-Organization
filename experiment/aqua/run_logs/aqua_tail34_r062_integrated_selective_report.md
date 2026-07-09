# R062 Integrated Selective PromptNode Report: tail34

## Boundary

This is a fresh integrated run. The evaluator executes ARG first and runs PromptNodes only when the direct-vote prefilter passes.
The gate does not read `true_answer`, `is_solved`, task ids, or clean/noisy labels.

## Summary

- Selected accuracy: `28/34` = `82.35%`
- ARG baseline inside R062: `28/34` = `82.35%`
- Delta vs baseline: `0`
- PromptNode runs: `1/34`
- PromptNode switches: `1`
- Fix/harm vs baseline: `0/0`
- Cost: `$0.970595`

## Switches

| task_id | baseline | promptnode | selected | router | binding | solved |
| --- | --- | --- | --- | --- | --- | --- |
| task_108 | D | D | D | D | EXACT_MATCH | True |
