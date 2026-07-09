# R132 Deterministic Router-NONE Guard Smoke

**Claim boundary**: same-four-task deterministic router-NONE smoke; broad claims require clean recovery, full held-out validation, and transfer

- Decision method: `DeterministicRouterContractFinalRefer`
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
- Router-NONE abstained: `1/1`
- Forced option after router NONE prevented: `1/1`
- Selector input field violations: `0`
- Forced cost: `$0.069920`
- Integrity gate passed: `True`
- Smoke gate passed: `False`
- Broad API allowed next: `False`
- Exact-option repair required: `True`

| Task | Label | Source | Rank | Baseline | Selected | Truth | Router | Abstained | Fix | Harm |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| `task_8` | `clean` | `baseline` | `None` | `E` | `E` | `E` | `/` | `False` | `False` | `False` |
| `task_108` | `noisy` | `rank5_DeterministicRouterContractFinalRefer` | `5` | `B` | `D` | `D` | `D/EXACT_MATCH` | `False` | `True` | `False` |
| `task_188` | `clean` | `baseline` | `None` | `D` | `D` | `D` | `/` | `False` | `False` | `False` |
| `task_250` | `clean` | `rank5_DeterministicRouterContractFinalRefer` | `5` | `A` | `None.` | `E` | `NONE/NO_EXACT_OPTION/CONFLICT` | `True` | `False` | `False` |

## Interpretation

R132 tests the R131 deterministic final guard only on the same four regression tasks. The integrity gate checks whether router-NONE evidence stays abstaining. The smoke gate still requires clean recovery without clean harm; if clean `task_250` remains unrecovered, the next step must be exact-option repair rather than broader API evaluation.
