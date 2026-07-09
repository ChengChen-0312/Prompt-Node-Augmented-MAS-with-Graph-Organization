# R074 Fresh Surgical Cascade Cost Comparison

**Boundary**: `fresh_integrated_surgical_cascade_promptnode_run`.

| Run | Type | Accuracy | Cost | Notes |
| --- | --- | ---: | ---: | --- |
| R059 | Historical ARG baseline | `28/34` | `$0.932850` | Prospective held-out ARG baseline. |
| R069 | Fresh integrated four-view selective PromptNode | `29/34` | `$3.908995` | Positive integrated run, but costly. |
| R072 | Fresh integrated cascade PromptNode | `29/34` | `$2.826040` | Measured cascade cost reduction. |
| R073 | Surgical trigger replay over R072 | `29/34` | `$1.618315` estimated | Replay/cost hypothesis, not measured billing. |
| R074 | Fresh integrated surgical cascade PromptNode | `29/34` | `$1.828715` measured | Lower cost than R072, but only `+1` over its internal ARG baseline. |

R074 saves `$0.997325` relative to R072 and `$2.080280` relative to R069. It costs `1.96x` the R059 ARG baseline and uses `28/52` possible PromptNode view calls across `13/34` triggered tasks.

The accuracy result is still `29/34`, not the R065/R068 replay ceiling of `31/34`. Its only fix is `task_108`, which is in the noisy/ambiguous audit split, so R074 is an efficiency result rather than a clean-reasoning improvement result.
