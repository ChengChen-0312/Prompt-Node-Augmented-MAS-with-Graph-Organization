# R086 Forced-Template Smoke Gate Report

**Claim boundary**: smoke-gate replay only, not tail34 accuracy

- Clean-positive accepted: `3/3`
- Boundary suppressed: `1/1`
- Gate action counts: `{'accept_template': 3, 'fallback_to_arg': 1}`
- Gate reason counts: `{'weak_non_none_terminal_option': 1, 'router_exact_final_agreement': 2, 'weak_none_of_these_boundary': 1}`
- Decision-field violations: `0`
- Accepted smoke cost: `$0.114505`
- Total smoke cost: `$0.166630`

| Group | Task | Prediction | Gold | Router contract | Gate action | Gate reason | Smoke cost |
| --- | --- | --- | --- | --- | --- | --- | ---: |
| `clean_positive` | `task_56` | `A` | `A` | `NONE/NO_EXACT_OPTION` | `accept_template` | `weak_non_none_terminal_option` | `$0.042030` |
| `clean_positive` | `task_188` | `D` | `D` | `D/EXACT_MATCH` | `accept_template` | `router_exact_final_agreement` | `$0.033405` |
| `clean_positive` | `task_8` | `E` | `E` | `E/EXACT_MATCH` | `accept_template` | `router_exact_final_agreement` | `$0.039070` |
| `boundary` | `task_114` | `E` | `D` | `NONE/NO_EXACT_OPTION` | `fallback_to_arg` | `weak_none_of_these_boundary` | `$0.052125` |

## Interpretation

The gate is a smoke-regression rule, not a validated accuracy method. It accepts exact router/final agreement, permits weak non-`None of these` terminal options for the clean-positive smoke set, and suppresses weak `None of these` boundary decisions such as `task_114`. The next step is to test whether this rule generalizes beyond the four smoke records before spending on a broader forced-template run.
