# R091 Bad-Exact Gate Forced-Template Mini-Set Report

**Claim boundary**: five-task forced-template mini-set, not tail34 accuracy

- Tasks: `5`
- ARG baseline solved: `3/5`
- Forced-template solved: `4/5`
- R088-gated solved: `4/5`
- Gate fix/harm vs ARG: `{'fix': 1, 'harm': 0}`
- Accepted tasks: `['task_188', 'task_8', 'task_108']`
- Fallback tasks: `['task_56', 'task_114']`
- Total forced-template cost: `$0.201250`
- Decision-field violations: `0`

| Task | ARG | Forced template | Gate | Gold | Gate action | Gate reason | Cost |
| --- | --- | --- | --- | --- | --- | --- | ---: |
| `task_56` | `A` | `A` | `A` | `A` | `fallback_to_arg` | `unsupported_router_status` | `$0.042030` |
| `task_188` | `D` | `D` | `D` | `D` | `accept_template` | `trusted_exact_contract` | `$0.033405` |
| `task_8` | `E` | `E` | `E` | `E` | `accept_template` | `trusted_exact_contract` | `$0.039070` |
| `task_114` | `C` | `E` | `C` | `D` | `fallback_to_arg` | `unsupported_router_status` | `$0.052125` |
| `task_108` | `B` | `D` | `D` | `D` | `accept_template` | `trusted_exact_contract` | `$0.034620` |

## Interpretation

The current five forced-template smoke records show the first small positive pattern for the R088 gate: it keeps the `task_108` fresh fix, falls back on weak or unsupported cases, and introduces no observed harm against the ARG baseline. The set was assembled from iterative smoke tasks, so it cannot be used as a tail34 accuracy claim.
