# R085 Forced-Template Clean-Positive Smoke Report

**Claim boundary**: clean-positive smoke only, not tail34 accuracy

- Clean-positive smoke runs: `3`
- Clean-positive solved: `3`
- Boundary smoke runs: `1`
- Boundary solved: `0`
- PromptNode graph runs: `4`
- Router status counts: `{'NO_EXACT_OPTION': 2, 'EXACT_MATCH': 2}`
- Clean-positive cost: `$0.114505`
- Total smoke cost: `$0.166630`

| Group | Run | Task | Rank | Prediction | Gold | Solved | Router contract | Cost |
| --- | --- | --- | ---: | --- | --- | --- | --- | ---: |
| `clean_positive` | `task56_clean_positive` | `task_56` | `1` | `A` | `A` | `yes` | `NONE/NO_EXACT_OPTION` | `$0.042030` |
| `clean_positive` | `task188_clean_positive` | `task_188` | `1` | `D` | `D` | `yes` | `D/EXACT_MATCH` | `$0.033405` |
| `clean_positive` | `task8_clean_positive` | `task_8` | `1` | `E` | `E` | `yes` | `E/EXACT_MATCH` | `$0.039070` |
| `boundary` | `task114_noisy_boundary_router_hardened` | `task_114` | `1` | `E` | `D` | `no` | `NONE/NO_EXACT_OPTION` | `$0.052125` |

## Interpretation

Rank-1 forced-template PromptNode execution preserves the three clean-positive smoke cases, but the hardened noisy boundary case still fails. This supports a narrow execution and case-selection claim only. It does not establish tail34 accuracy or improvement over the historical ARG-Designer run.

The next experiment should turn this observation into a pre-registered gate: allow explicit PromptNode templates on cleanly bound cases, and suppress or fall back on weak/noisy boundary cases before spending on a broader held-out run.
