# R269 Critical Smoke Replay

**Claim boundary**: no_api_critical_case_replay

| Task | ARG | R267 | Official gold | R267 official | R267 corrected/sensitivity | Source |
|---|---:|---:|---:|---:|---:|---|
| `task_114` | `C` | `C` | `D` | `False` | `True` | `baseline` |
| `task_59` | `B` | `B` | `C` | `False` | `False` | `baseline` |
| `task_108` | `B` | `D` | `D` | `True` | `True` | `safety_accept_objective` |
| `task_250` | `A` | `E` | `E` | `True` | `True` | `safety_accept_objective` |
| `task_8` | `E` | `E` | `E` | `True` | `True` | `baseline` |
| `task_188` | `D` | `D` | `D` | `True` | `True` | `baseline` |

- Critical official fix/harm: `2/0`
- Critical task114-corrected fix/harm: `3/0`

Use this as preflight evidence only; fresh API is still required before a deployable student selector claim.
