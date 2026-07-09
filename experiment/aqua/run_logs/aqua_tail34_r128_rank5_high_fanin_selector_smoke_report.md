# R128 Rank5 High-Fanin Selector Smoke

**Claim boundary**: same-four-task rank5 high-fanin selector smoke; broad claims require a fresh R128 API run and separate audit

- Baseline accuracy: `2/4`
- Selected accuracy: `3/4`
- Switch tasks: `['task_108', 'task_250']`
- Fallback tasks: `['task_8', 'task_188']`
- Selected template ranks: `{'task_108': 5, 'task_250': 5}`
- PromptNode graph evidence on switches: `2/2`
- Switch update2 metadata: `2/2`
- High-fanin Memory bridge on switches: `2/2`
- Fix/harm: `1/0`
- Clean fix/harm: `0/0`
- Noisy fix/harm: `1/0`
- Selector input field violations: `0`
- Forced cost: `$0.075725`
- Smoke gate passed: `False`
- Broad API allowed next: `False`

| Task | Label | Source | Rank | Baseline | Selected | Truth | Fix | Harm | PN graph | High fan-in |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| `task_8` | `clean` | `baseline` | `None` | `E` | `E` | `E` | `False` | `False` | `False` | `False` |
| `task_108` | `noisy` | `explicit_template_rank5_high_fanin` | `5` | `B` | `D` | `D` | `True` | `False` | `True` | `True` |
| `task_188` | `clean` | `baseline` | `None` | `D` | `D` | `D` | `False` | `False` | `False` | `False` |
| `task_250` | `clean` | `explicit_template_rank5_high_fanin` | `5` | `A` | `A` | `E` | `False` | `False` | `True` | `True` |

## Interpretation

R128 evaluates the R127 plan only on the same four regression tasks. Passing this smoke would support a bounded clean-fix mechanism claim, but broad tail34 or transfer evaluation still requires a separate audit decision.
