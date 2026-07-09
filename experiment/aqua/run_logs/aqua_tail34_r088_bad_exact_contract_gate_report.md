# R088 Bad-Exact-Contract Gate Report

**Claim boundary**: r058 replay gate candidate, not fresh accuracy

- Tasks: `34`
- ARG baseline solved: `28/34`
- Dense R058 PromptNode solved: `25/34`
- Bad-exact gate solved: `29/34`
- Gate fix/harm vs ARG: `{'fix': 1, 'harm': 0}`
- Accepted switch tasks: `['task_108']`
- Fallback harm-prevented tasks: `['task_188', 'task_56', 'task_6', 'task_8']`
- Gate reasons: `{'trusted_exact_contract': 24, 'unsupported_router_status': 8, 'exact_single_vote_split': 1, 'exact_conflicts_direct_majority': 1}`
- Decision-field violations: `0`

| Task | ARG | R058 PN | Gate | Gold | Gate action | Gate reason |
| --- | --- | --- | --- | --- | --- | --- |
| `task_108` | `B` | `D` | `D` | `D` | `accept_template` | `trusted_exact_contract` |
| `task_114` | `C` | `E` | `C` | `D` | `fallback_to_arg` | `unsupported_router_status` |
| `task_188` | `D` | `C` | `D` | `D` | `fallback_to_arg` | `exact_single_vote_split` |
| `task_56` | `A` | `D` | `A` | `A` | `fallback_to_arg` | `exact_conflicts_direct_majority` |
| `task_59` | `B` | `X` | `B` | `C` | `fallback_to_arg` | `unsupported_router_status` |
| `task_6` | `D` | `E` | `D` | `D` | `fallback_to_arg` | `unsupported_router_status` |
| `task_8` | `E` | `C` | `E` | `E` | `fallback_to_arg` | `unsupported_router_status` |

## Interpretation

R088 fixes the failure mode exposed by R087. It does not trust `EXACT_MATCH` by itself: exact contracts are suppressed when they conflict with a direct-agent majority or when multiple direct agents split and the router only follows a single vote. On dense R058 traces this preserves the useful `task_108` switch and falls back on the three harmful R058 switches. This is still a replay-derived gate candidate, not a fresh forced-template accuracy result.
