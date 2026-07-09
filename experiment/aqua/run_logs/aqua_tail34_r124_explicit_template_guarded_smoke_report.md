# R124 Explicit-Template Guarded Smoke

**Claim boundary**: same-four-task explicit-template guarded smoke; broader claims require the smoke gate to pass

- Total tasks: `4`
- Baseline accuracy: `2/4`
- Selected accuracy: `3/4`
- Switch tasks: `['task_108', 'task_250']`
- Fallback tasks: `['task_8', 'task_188']`
- PromptNode graph evidence on switches: `2/2`
- Switch update2 metadata: `2/2`
- Fix/harm: `1/0`
- Clean fix/harm: `0/0`
- Noisy fix/harm: `1/0`
- Selector input field violations: `0`
- Forced-template cost: `$0.065015`
- Smoke gate passed: `False`
- Broad API allowed next: `False`

| Task | Audit label | Source | ARG | Selected | Truth | Fix | Harm | PN graph | Update2 metadata |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `task_8` | `clean` | `baseline` | `E` | `E` | `E` | `False` | `False` | `False` | `False` |
| `task_108` | `noisy` | `explicit_template_rank1` | `B` | `D` | `D` | `True` | `False` | `True` | `True` |
| `task_188` | `clean` | `baseline` | `D` | `D` | `D` | `False` | `False` | `False` | `False` |
| `task_250` | `clean` | `explicit_template_rank1` | `A` | `A` | `E` | `False` | `False` | `True` | `True` |

## Interpretation

R124 tests only the R123-approved four-task explicit-template guarded policy. The result can permit a broader run only if switches carry PromptNode graph/update2 metadata, there are no selector-input violations, no clean harms occur, and at least one clean fix is recovered.
