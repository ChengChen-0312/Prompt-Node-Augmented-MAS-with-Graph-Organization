# R059-R060 Tail34 ARG vs R058 PromptNode Validation

**Claim boundary**: Tail34 is a pre-registered held-out AQuA slice. These same-model runs use `gpt-4o-2024-08-06`. The result is prospective evidence against using dense generated PromptNode graphs as the main accuracy method.

## Results

| Variant | Output file | Accuracy | Fix/Harm vs ARG | Cost |
| --- | --- | ---: | ---: | ---: |
| R059 ARG baseline | `experiment/aqua/aqua_tail34_arg_baseline_results.jsonl` | `28/34` | `0/0` | `$0.932850` |
| R060 R058 PromptNode router-contract terminal | `experiment/aqua/aqua_tail34_r058_router_contract_terminal_results.jsonl` | `25/34` | `1/4` | `$1.079990` |

## Fix/Harm Rows

- R060 fixes `task_108`: ARG predicts `B`, R060 predicts `D`, gold `D`.
- R060 harms `task_56`: ARG predicts `A`, R060 predicts `D`, gold `A`.
- R060 harms `task_8`: ARG predicts `E`, R060 predicts `C`, gold `E`.
- R060 harms `task_188`: ARG predicts `D`, R060 predicts `C`, gold `D`.
- R060 harms `task_6`: ARG predicts `D`, R060 predicts `E`, gold `D`.

## Interpretation

The held-out tail34 result is a hard failure for dense generated PromptNode execution as a main accuracy claim. R058 is structurally faithful to the user's design: PromptNodes are generated before execution, canonicalized into Memory->Verifier->Router lifecycle, and consumed through a router-contract final. However, on unseen rows it introduces more harms than fixes.

This strengthens the paper direction rather than ending it: the method should move from dense PromptNode generation to selective PromptNode activation. The next graph policy should decide when a PromptNode lifecycle is needed, not force it on every task.
