# R131 Deterministic Router-NONE Guard Protocol

**Claim boundary**: implementation and offline guard protocol only; no API, cost, or accuracy result

- Decision method: `DeterministicRouterContractFinalRefer`
- Decision method registered: `True`
- Implementation only: `True`
- No API run: `True`
- Router-NONE terminal guard predictions: `3/3`
- Forced option after router NONE prevented: `3/3`
- Parser prediction for abstain: `None.`
- Broad API allowed next: `False`
- Same-four-task smoke allowed next: `True`
- Next protocol: `same_four_task_deterministic_router_none_smoke`

| Run | Source prediction | Guard prediction | Guard raw response | Prevented forced option |
| --- | --- | --- | --- | --- |
| `R128` | `A` | `None.` | `no valid option is supported` | `True` |
| `R100` | `E` | `None.` | `no valid option is supported` | `True` |
| `R106` | `E` | `None.` | `no valid option is supported` | `True` |

## Interpretation

R131 implements a deterministic final decision method for the R129 failure mode. When the terminal PN_Router contract abstains with `NONE/NO_EXACT_OPTION` and no direct majority is available, the final node returns a lower-case abstention string instead of any A-E label. This prevents the AQuA parser from extracting a false option from `NONE`. It is an offline implementation/protocol result; the next step is only the same four-task smoke, not broad tail34 or transfer.
