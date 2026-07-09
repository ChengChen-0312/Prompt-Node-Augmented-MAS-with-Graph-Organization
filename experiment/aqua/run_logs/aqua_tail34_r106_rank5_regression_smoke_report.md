# R106 Rank5 Regression Smoke Report

**Claim boundary**: four-task rank5 regression smoke; consensus not clean-safe

- Baseline solved: `2/4`
- Rank5 solved: `3/4`
- Fix/harm: `2/1`
- Clean fix/harm: `1/1`
- Noisy fix/harm: `1/0`
- Clean harm guard harms: `['task_8']`
- Clean recovery targets solved: `['task_250']`
- Rank2/rank5 consensus tasks: `['task_108']`
- Consensus clean recovery solved: `[]`
- Total cost: `$0.166430`

| Task | Role | Audit label | ARG | Rank2 | Rank5 | Truth | Fix | Harm | Rank2=Rank5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `task_8` | `clean_harm_guard` | `clean` | `E` | `E` | `C` | `E` | `False` | `True` | `False` |
| `task_108` | `noisy_optional_target` | `noisy` | `B` | `D` | `D` | `D` | `True` | `False` | `True` |
| `task_188` | `clean_harm_guard` | `clean` | `D` | `C` | `D` | `D` | `False` | `False` | `False` |
| `task_250` | `clean_recovery_target` | `clean` | `A` | `A` | `E` | `E` | `True` | `False` | `False` |

## Interpretation

Rank5 recovers clean `task_250` and noisy `task_108`, but it also harms clean guard `task_8`. Rank2/rank5 agreement is too conservative for clean recovery because the only agreement point is noisy `task_108`. This rejects both plain rank5 deployment and simple rank-consensus gating as SCI-Q2-level evidence.
