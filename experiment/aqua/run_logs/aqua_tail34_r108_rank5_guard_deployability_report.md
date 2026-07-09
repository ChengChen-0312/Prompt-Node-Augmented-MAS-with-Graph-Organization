# R108 Rank5 Guard Deployability Audit

**Claim boundary**: feature audit only; no accuracy or new selector claim

- Ambiguous single-template groups: `1`
- Ambiguous no-exact/diff tasks: `['task_8', 'task_250']`
- Objective features separate ambiguous tasks: `True`
- Single-template guard sufficient: `False`
- Selector input field violations: `0`

| Task | R107 action | ARG | Rank5 | Rank5 binding | Supported option kind | Rank5 differs | Objective differs | Objective score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `task_8` | `fallback_to_arg` | `E` | `C` | `NO_EXACT_OPTION` | `none` | `True` | `False` | `2` |
| `task_108` | `accept_rank5` | `B` | `D` | `EXACT_MATCH` | `specific` | `True` | `True` | `2` |
| `task_188` | `fallback_to_arg` | `D` | `D` | `EXACT_MATCH` | `specific` | `False` | `False` | `1` |
| `task_250` | `accept_rank5` | `A` | `E` | `NO_EXACT_OPTION` | `none` | `True` | `True` | `3` |

## Interpretation

`task_8` and `task_250` share the same label-normalized single-template pattern: rank5 differs from ARG, emits `NO_EXACT_OPTION`, and uses the same rank5 graph. They require different actions, so the current evidence does not justify a cheap single-template guard. The separating signal comes from the objective-safety features, which means the next step must train or approximate that objective rather than trusting rank5 traces alone.
