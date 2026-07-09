# R173 Action-Aware Selector Replay

**Claim boundary**: No-API replay of R171 records after splitting preserve-safe insertion from switch-critical override. Safety/diagnosis only, not new accuracy evidence.

- No new API: `True`
- Selected accuracy: `4/4`
- Internal ARG baseline accuracy: `4/4`
- Delta vs baseline: `+0`
- Switch tasks after action gate: `[]`
- Fallback tasks after action gate: `['task_8', 'task_108', 'task_188', 'task_250']`
- Fix/Harm: `0/0`
- Clean fix/harm: `0/0`
- Selector input violations: `0`
- Source R171 cost: `$0.224830`

| Task | Prior action | ARG | PromptEdge | Selected source | Selected | Truth | Runtime fallback reason | Fix | Harm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `task_8` | `preserve_safe_insert` | `E` | `None` | `baseline` | `E` | `E` | `promptedge_abstained_or_invalid_option` | `False` | `False` |
| `task_108` | `preserve_safe_insert` | `D` | `D` | `baseline` | `D` | `D` | `selector_prior_preserve_safe_not_switch_critical` | `False` | `False` |
| `task_188` | `` | `D` | `None` | `baseline` | `D` | `D` | `selector_negative` | `False` | `False` |
| `task_250` | `preserve_safe_insert` | `E` | `None` | `baseline` | `E` | `E` | `promptedge_abstained_or_invalid_option` | `False` | `False` |

## Interpretation

R173 identifies the main methodological flaw after R171/R172: the R168 selector learned one positive class for both preserve-safe PromptNode insertion and switch-critical override. After separating the actions, all four smoke rows fall back to ARG because their live priors are preserve-safe or missing. This is safer but cannot improve accuracy; the next model iteration needs a true two-head policy: one head learns PromptNode/PromptEdge insertion, the other learns when a PromptEdge output is allowed to override ARG.
