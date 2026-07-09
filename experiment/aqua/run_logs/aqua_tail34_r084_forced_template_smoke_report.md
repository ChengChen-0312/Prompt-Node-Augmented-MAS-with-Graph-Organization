# R084 Forced-Template PromptNode Smoke Report

**Claim boundary**: R084 is smoke-only evidence for forced-template execution plumbing and qualitative failure analysis. It is not a tail34 accuracy result and does not justify full-run claims.

- Smoke runs: `4`
- Solved runs: `1`
- PromptNode graph runs: `4`
- Router status counts: `{'EXACT_MATCH': 2, 'NO_EXACT_OPTION': 2}`
- Total smoke cost: `$0.204925`

| Run | Task | Rank | Prediction | Gold | Solved | Router contract | Cost |
| --- | --- | ---: | --- | --- | --- | --- | ---: |
| `rank1_task114_initial` | `task_114` | `1` | `C` | `D` | `no` | `C/EXACT_MATCH` | `$0.051690` |
| `rank5_task114_initial` | `task_114` | `5` | `C` | `D` | `no` | `C/EXACT_MATCH` | `$0.059080` |
| `rank1_task56_initial` | `task_56` | `1` | `A` | `A` | `yes` | `NONE/NO_EXACT_OPTION` | `$0.042030` |
| `rank1_task114_router_hardened` | `task_114` | `1` | `E` | `D` | `no` | `NONE/NO_EXACT_OPTION` | `$0.052125` |

## Interpretation

The forced-template execution hook is functional: every smoke run executed an explicit PromptNode graph before final aggregation. The smoke results do not justify a full tail34 run yet. `task_56` succeeds, but `task_114` shows that noisy/unsupported boundary cases require stronger routing or abstention logic; after router-contract hardening, the router no longer emits an erroneous `C/EXACT_MATCH`, but the system still does not recover the official label `D` from weak evidence.
