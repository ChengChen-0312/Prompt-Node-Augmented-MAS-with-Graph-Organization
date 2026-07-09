# R087 R086 Gate on R058 Stress Report

**Claim boundary**: r058 stress replay, not a new accuracy method

- Tasks: `34`
- ARG baseline solved: `28/34`
- Dense R058 PromptNode solved: `25/34`
- R086-gated replay solved: `26/34`
- Gate fix/harm vs ARG: `{'fix': 1, 'harm': 3}`
- Gate actions: `{'accept_template': 29, 'fallback_to_arg': 5}`
- Gate reasons: `{'router_exact_final_agreement': 26, 'weak_none_of_these_boundary': 1, 'weak_non_none_terminal_option': 3, 'unsupported_router_status': 4}`
- Decision-field violations: `0`

| Task | ARG | R058 PN | Gate | Gold | Gate action | Gate reason |
| --- | --- | --- | --- | --- | --- | --- |
| `task_108` | `B` | `D` | `D` | `D` | `accept_template` | `router_exact_final_agreement` |
| `task_114` | `C` | `E` | `C` | `D` | `fallback_to_arg` | `weak_none_of_these_boundary` |
| `task_179` | `B` | `B` | `B` | `B` | `fallback_to_arg` | `unsupported_router_status` |
| `task_188` | `D` | `C` | `C` | `D` | `accept_template` | `router_exact_final_agreement` |
| `task_35` | `A` | `A` | `A` | `A` | `fallback_to_arg` | `unsupported_router_status` |
| `task_56` | `A` | `D` | `D` | `A` | `accept_template` | `router_exact_final_agreement` |
| `task_59` | `B` | `X` | `B` | `C` | `fallback_to_arg` | `unsupported_router_status` |
| `task_6` | `D` | `E` | `E` | `D` | `accept_template` | `weak_non_none_terminal_option` |
| `task_8` | `E` | `C` | `E` | `E` | `fallback_to_arg` | `unsupported_router_status` |

## Interpretation

The R086 smoke gate does not generalize to the dense R058 PromptNode candidate pool. It improves over dense R058 (`26/34` vs `25/34`) but remains below the ARG baseline (`28/34`) and introduces three harms. This rejects promoting the current gate to an online full-tail34 method. The next gate must distinguish bad exact-router contracts from reliable exact contracts, not only suppress weak `None of these` cases.
