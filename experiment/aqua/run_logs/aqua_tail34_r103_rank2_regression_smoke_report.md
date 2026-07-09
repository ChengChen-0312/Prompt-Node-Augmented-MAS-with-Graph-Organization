# R103 Rank2 Regression Smoke Report

**Claim boundary**: four-task rank2 regression smoke; rejects R101 heuristic as deployable selector

- Baseline solved: `2/4`
- Rank2 solved: `2/4`
- Fix/harm: `1/1`
- Clean fix/harm: `0/1`
- Noisy fix/harm: `1/0`
- Clean harm guard harms: `['task_188']`
- Clean recovery targets solved: `[]`
- Total cost: `$0.160200`

| Task | Role | Audit label | ARG | Rank2 | Truth | Fix | Harm |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `task_8` | `clean_harm_guard` | `clean` | `E` | `E` | `E` | `False` | `False` |
| `task_108` | `noisy_optional_target` | `noisy` | `B` | `D` | `D` | `True` | `False` |
| `task_188` | `clean_harm_guard` | `clean` | `D` | `C` | `D` | `False` | `True` |
| `task_250` | `clean_recovery_target` | `clean` | `A` | `A` | `E` | `False` | `False` |

## Interpretation

The R101 rank2 hypothesis does not survive the regression smoke: it fixes noisy `task_108`, but harms clean guard `task_188` and fails to reproduce the clean `task_250` recovery. Do not use this heuristic as a deployable selector.
