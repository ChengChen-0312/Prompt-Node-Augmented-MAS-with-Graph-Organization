# R129 Task250 Router-NONE Failure Diagnosis

**Claim boundary**: diagnosis only; no API run, no new accuracy result, and task250 rank5 historical success is not a clean router-supported fix

- Compared runs: `['R128', 'R100', 'R106']`
- Router NONE/NO_EXACT_OPTION runs: `3/3`
- Final option after router NONE runs: `3/3`
- R128 prediction: `A`
- R100 prediction: `E`
- R106 prediction: `E`
- Router-contract-supported clean fix: `False`
- Historical success is nearest-choice coercion: `True`
- Rank selection sufficient: `False`
- Broad API allowed next: `False`
- Next required protocol: `deterministic_none_guard_or_exact_option_repair_before_api`

| Run | Rank | Router option | Binding | Prediction | Gold | Solved | Nearest/best-supported text |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| `R128` | `5` | `NONE` | `NO_EXACT_OPTION` | `A` | `E` | `False` | `True` |
| `R100` | `5` | `NONE` | `NO_EXACT_OPTION` | `E` | `E` | `True` | `True` |
| `R106` | `5` | `NONE` | `NO_EXACT_OPTION` | `E` | `E` | `True` | `True` |

## Interpretation

All three rank-5 executions for `task_250` end with the same terminal router contract: `SUPPORTED_OPTION: NONE` and `BINDING_STATUS: NO_EXACT_OPTION`. The two historical successes, R100 and R106, therefore cannot be claimed as clean router-supported fixes: their final layer selected `E` after the router abstained. R128 selected `A` under the same abstention boundary. The next method step must make the final decision deterministic under router abstention or add an exact-option repair stage before any broader API run.
