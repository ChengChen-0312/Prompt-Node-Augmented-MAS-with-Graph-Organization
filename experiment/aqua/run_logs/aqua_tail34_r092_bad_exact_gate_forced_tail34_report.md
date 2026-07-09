# R092 Bad-Exact Gate Forced-Template Tail34 Report

**Claim boundary**: full tail34 forced-template validation with frozen R088 gate

- Tasks: `34`
- ARG baseline solved: `28/34`
- Forced-template solved: `25/34`
- R088-gated solved: `27/34`
- Gate fix/harm vs ARG: `{'fix': 1, 'harm': 2}`
- Fix tasks: `['task_108']`
- Harm tasks: `['task_8', 'task_188']`
- Prevented-harm tasks: `['task_56', 'task_6']`
- Baseline-wrong still wrong: `['task_114', 'task_59', 'task_139', 'task_228', 'task_250']`
- Gate actions: `{'fallback_to_arg': 7, 'accept_template': 27}`
- Gate reasons: `{'unsupported_router_status': 7, 'trusted_exact_contract': 27}`
- Decision-field violations: `0`
- Total forced-template cost: `$1.286050`

| Task | ARG | Forced template | Gate | Gold | Gate action | Gate reason |
| --- | --- | --- | --- | --- | --- | --- |
| `task_114` | `C` | `E` | `C` | `D` | `fallback_to_arg` | `unsupported_router_status` |
| `task_56` | `A` | `E` | `A` | `A` | `fallback_to_arg` | `unsupported_router_status` |
| `task_107` | `B` | `B` | `B` | `B` | `accept_template` | `trusted_exact_contract` |
| `task_240` | `B` | `B` | `B` | `B` | `accept_template` | `trusted_exact_contract` |
| `task_179` | `B` | `B` | `B` | `B` | `accept_template` | `trusted_exact_contract` |
| `task_166` | `C` | `C` | `C` | `C` | `accept_template` | `trusted_exact_contract` |
| `task_183` | `D` | `D` | `D` | `D` | `accept_template` | `trusted_exact_contract` |
| `task_50` | `C` | `C` | `C` | `C` | `accept_template` | `trusted_exact_contract` |
| `task_143` | `E` | `E` | `E` | `E` | `accept_template` | `trusted_exact_contract` |
| `task_251` | `A` | `A` | `A` | `A` | `accept_template` | `trusted_exact_contract` |
| `task_154` | `C` | `C` | `C` | `C` | `accept_template` | `trusted_exact_contract` |
| `task_129` | `D` | `D` | `D` | `D` | `accept_template` | `trusted_exact_contract` |
| `task_59` | `B` | `E` | `B` | `C` | `fallback_to_arg` | `unsupported_router_status` |
| `task_55` | `A` | `A` | `A` | `A` | `accept_template` | `trusted_exact_contract` |
| `task_23` | `A` | `A` | `A` | `A` | `accept_template` | `trusted_exact_contract` |
| `task_7` | `C` | `C` | `C` | `C` | `accept_template` | `trusted_exact_contract` |
| `task_8` | `E` | `A` | `A` | `E` | `accept_template` | `trusted_exact_contract` |
| `task_108` | `B` | `D` | `D` | `D` | `accept_template` | `trusted_exact_contract` |
| `task_151` | `E` | `E` | `E` | `E` | `accept_template` | `trusted_exact_contract` |
| `task_22` | `E` | `E` | `E` | `E` | `accept_template` | `trusted_exact_contract` |
| `task_139` | `D` | `D` | `D` | `E` | `fallback_to_arg` | `unsupported_router_status` |
| `task_228` | `C` | `C` | `C` | `B` | `accept_template` | `trusted_exact_contract` |
| `task_250` | `A` | `A` | `A` | `E` | `fallback_to_arg` | `unsupported_router_status` |
| `task_173` | `C` | `C` | `C` | `C` | `accept_template` | `trusted_exact_contract` |
| `task_26` | `C` | `C` | `C` | `C` | `accept_template` | `trusted_exact_contract` |
| `task_188` | `D` | `C` | `C` | `D` | `accept_template` | `trusted_exact_contract` |
| `task_35` | `A` | `A` | `A` | `A` | `fallback_to_arg` | `unsupported_router_status` |
| `task_57` | `D` | `D` | `D` | `D` | `accept_template` | `trusted_exact_contract` |
| `task_62` | `B` | `B` | `B` | `B` | `accept_template` | `trusted_exact_contract` |
| `task_70` | `C` | `C` | `C` | `C` | `accept_template` | `trusted_exact_contract` |
| `task_189` | `B` | `B` | `B` | `B` | `accept_template` | `trusted_exact_contract` |
| `task_6` | `D` | `E` | `D` | `D` | `fallback_to_arg` | `unsupported_router_status` |
| `task_28` | `B` | `B` | `B` | `B` | `accept_template` | `trusted_exact_contract` |
| `task_163` | `D` | `D` | `D` | `D` | `accept_template` | `trusted_exact_contract` |

## Interpretation

This report applies the frozen R088 bad-exact-contract gate to forced-template PromptNode records. A positive result can support broader held-out validation only if it exceeds the ARG baseline without introducing observed harm; otherwise the forced rank-1 template policy should return to template selection or graph-policy training. The current full tail34 result is negative for the frozen R088/R091 gate because it preserves one fix but introduces two harms.
