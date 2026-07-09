# R143 Calibrated Repair Final-Gate Offline Replay

**Claim boundary**: offline replay over R139 traces only; no API, production final-gate change, transfer, robustness, or SCI-readiness claim

- Offline replay only: `True`
- No API run: `True`
- Uses tail34 training source: `False`
- Baseline accuracy: `2/4`
- R139 selected accuracy: `3/4`
- Calibrated selected accuracy: `4/4`
- Clean fix/harm: `1/0`
- Noisy fix/harm: `1/0`
- task250 calibrated prediction: `E`
- task250 calibrated confidence: `0.95`
- Clean harm guard passed: `True`
- Same-four-task gate offline passed: `True`
- Broad API allowed next: `False`
- Next protocol: `calibrated_repair_final_gate_implementation_presmoke`

| Task | Label | Baseline | R139 Selected | Calibrated | Truth | Calibrated Confidence | Fix | Harm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `task_8` | `clean` | `E` | `E` | `E` | `E` | `0.0` | `False` | `False` |
| `task_108` | `noisy` | `B` | `D` | `D` | `D` | `0.0` | `True` | `False` |
| `task_188` | `clean` | `D` | `D` | `D` | `D` | `0.0` | `False` | `False` |
| `task_250` | `clean` | `A` | `None.` | `E` | `E` | `0.95` | `True` | `False` |

## Interpretation

R143 is an offline replay over existing R139 traces. It suggests the calibrated repair gate can recover task250 without harming the clean guards, but it is not a fresh API result and does not change the production final decision method.
