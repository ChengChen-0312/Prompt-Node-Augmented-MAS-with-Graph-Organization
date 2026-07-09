# R072 Fresh Cascade Cost Comparison

**Boundary**: `fresh_integrated_cascade_multiview_promptnode_run`.

| Run | Type | Accuracy | Cost | Notes |
| --- | --- | ---: | ---: | --- |
| R059 | Historical ARG baseline | `28/34` | `$0.932850` | Prospective held-out ARG baseline. |
| R069 | Fresh integrated four-view selective PromptNode | `29/34` | `$3.908995` | Positive integrated run, but costly. |
| R071 | Cascade replay over R069 traces | `29/34` | `$2.599491` estimated | Replay/cost model, not measured API billing. |
| R072 | Fresh integrated cascade PromptNode | `29/34` | `$2.826040` measured | Same accuracy as R069 with fewer measured view calls. |

R072 saves `$1.082955` relative to R069 and costs `3.03x` the R059 ARG baseline. It uses `58/104` possible PromptNode view calls, a `44.2%` reduction versus running all views on all triggered tasks.

R072 supports a measured cost-reduction claim for the integrated multi-view system. It does not support a claim that the fresh system reaches the R065/R068 replay ceiling of `31/34`, and it does not remove the need for transfer validation or train-time graph-policy validation.
