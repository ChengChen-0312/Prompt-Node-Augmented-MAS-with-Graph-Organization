# R114 Objective-Safety Proxy Regression Stress

**Claim boundary**: four-task regression replay of R113 over R106/R107 traces; no new API or held-out accuracy claim

- Learned rule: `diff_and_top_score_ge_3_or_split`
- Tasks: `4`
- Proxy action agreement with R107: `4/4`
- Baseline solved: `2/4`
- Rank5 solved: `3/4`
- Proxy guarded solved: `4/4`
- Proxy switch tasks: `['task_108', 'task_250']`
- Proxy fallback tasks: `['task_8', 'task_188']`
- Suppressed rank5 harms: `['task_8']`
- Clean recovery tasks: `['task_250']`
- Proxy fix/harm: `2/0`
- Proxy clean fix/harm: `1/0`
- Proxy noisy fix/harm: `1/0`
- Proxy input-field violations: `0`

| Task | Label | Proxy action | ARG | Rank5 | Proxy guarded | Truth | Fix | Harm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `task_8` | `clean` | `fallback_to_arg` | `E` | `C` | `E` | `E` | `False` | `False` |
| `task_108` | `noisy` | `accept_rank5` | `B` | `D` | `D` | `D` | `True` | `False` |
| `task_188` | `clean` | `fallback_to_arg` | `D` | `D` | `D` | `D` | `False` | `False` |
| `task_250` | `clean` | `accept_rank5` | `A` | `E` | `E` | `E` | `True` | `False` |

## Interpretation

R114 checks that the R113 proxy reproduces the known R107 clean-harm/recovery behavior on the four-task regression set. It is a replay over existing traces, not a new API result and not a broad held-out accuracy claim.
