# R089 Bad-Exact Gate on Forced-Template Smoke Report

**Claim boundary**: forced-template smoke replay, not tail34 accuracy

- Smoke rows: `4`
- ARG baseline solved: `3/4`
- Forced-template solved: `3/4`
- R088-gated solved: `3/4`
- Gate fix/harm vs ARG: `{'fix': 0, 'harm': 0}`
- Accepted tasks: `['task_188', 'task_8']`
- Fallback tasks: `['task_56', 'task_114']`
- Gate reasons: `{'unsupported_router_status': 2, 'trusted_exact_contract': 2}`
- Decision-field violations: `0`

| Task | ARG | Forced template | Gate | Gold | Gate action | Gate reason |
| --- | --- | --- | --- | --- | --- | --- |
| `task_56` | `A` | `A` | `A` | `A` | `fallback_to_arg` | `unsupported_router_status` |
| `task_188` | `D` | `D` | `D` | `D` | `accept_template` | `trusted_exact_contract` |
| `task_8` | `E` | `E` | `E` | `E` | `accept_template` | `trusted_exact_contract` |
| `task_114` | `C` | `E` | `C` | `D` | `fallback_to_arg` | `unsupported_router_status` |

## Interpretation

The R088 gate is non-harmful on the current forced-template smoke set: it accepts exact trusted contracts for `task_188` and `task_8`, while falling back on weak or unsupported contracts for `task_56` and `task_114`. This remains a four-record smoke replay and does not establish tail34 accuracy.
