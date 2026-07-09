# R107 Objective-Safety Rank5 Guard Replay

**Claim boundary**: four-task replay over R106 rank5 outputs and R095 objective-safety features

- Baseline solved: `2/4`
- Rank5 solved: `3/4`
- Guarded solved: `4/4`
- Switch tasks: `['task_108', 'task_250']`
- Fallback tasks: `['task_8', 'task_188']`
- Fix/harm: `2/0`
- Clean fix/harm: `1/0`
- Noisy fix/harm: `1/0`
- Suppressed rank5 harms: `['task_8']`
- Selector input field violations: `0`

| Task | Action | ARG | Rank5 | Guarded | Truth | Audit label | Fix | Harm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `task_8` | `fallback_to_arg` | `E` | `C` | `E` | `E` | `clean` | `False` | `False` |
| `task_108` | `accept_rank5` | `B` | `D` | `D` | `D` | `noisy` | `True` | `False` |
| `task_188` | `fallback_to_arg` | `D` | `D` | `D` | `D` | `clean` | `False` | `False` |
| `task_250` | `accept_rank5` | `A` | `E` | `E` | `E` | `clean` | `True` | `False` |

## Interpretation

The R095 objective-safety guard suppresses the R106 rank5 clean harm on `task_8` while preserving the rank5 clean recovery on `task_250`. This is still only a four-task replay over existing features and outputs; it is a candidate guard for the next smoke/prospective validation, not a held-out result.
