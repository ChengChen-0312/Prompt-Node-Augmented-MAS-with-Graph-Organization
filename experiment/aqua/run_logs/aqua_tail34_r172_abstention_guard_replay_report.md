# R172 PromptEdge Abstention Guard Replay

**Claim boundary**: No-API replay of R171 records after adding PromptEdge abstention fallback; validates safety gate only, not new accuracy evidence.

- No new API: `True`
- Selected accuracy: `4/4`
- Internal ARG baseline accuracy: `4/4`
- Delta vs baseline: `+0`
- PromptEdge run count inherited from R171: `3`
- Switch tasks after guard: `['task_108']`
- Fallback tasks after guard: `['task_8', 'task_188', 'task_250']`
- Fix/Harm: `0/0`
- Clean fix/harm: `0/0`
- Selector input violations: `0`
- Source R171 cost: `$0.224830`

| Task | ARG | PromptEdge | Selected source | Selected | Truth | Runtime fallback reason | Fix | Harm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `task_8` | `E` | `None` | `baseline` | `E` | `E` | `promptedge_abstained_or_invalid_option` | `False` | `False` |
| `task_108` | `D` | `D` | `selector_gated_promptedge` | `D` | `D` | `` | `False` | `False` |
| `task_188` | `D` | `None` | `baseline` | `D` | `D` | `selector_negative` | `False` | `False` |
| `task_250` | `E` | `None` | `baseline` | `E` | `E` | `promptedge_abstained_or_invalid_option` | `False` | `False` |

## Interpretation

The R172 guard fixes the R171 safety failure by preserving the ARG answer whenever the PromptEdge path abstains or emits a non A-E prediction. This removes the clean harms on task_8 and task_250, but it does not improve over the internal ARG baseline on this four-task smoke.
