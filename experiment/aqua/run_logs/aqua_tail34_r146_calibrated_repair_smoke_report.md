# R146 Bounded Calibrated Repair API Smoke

**Claim boundary**: same-four-task bounded calibrated repair API smoke; clean repair is supported on the regression gate, but broad held-out evaluation, transfer, robustness, and SCI-readiness remain unsupported

- Decision method: `CalibratedEdgePromptRepairContractFinalRefer`
- Baseline accuracy: `2/4`
- Selected accuracy: `4/4`
- Switch tasks: `['task_108', 'task_250']`
- Fallback tasks: `['task_8', 'task_188']`
- PN graph evidence on switches: `2/2`
- Switch update2 metadata: `2/2`
- Fix/harm: `2/0`
- Clean fix/harm: `1/0`
- Noisy fix/harm: `1/0`
- Switch router repair fields present: `2/2`
- Switch router repair option non-none: `1/2`
- task250 verifier repair candidate present: `True`
- task250 router repair forwarded: `True`
- Verifier-router repair forwarding gap: `False`
- task250 router repair option: `E`
- task250 raw router repair confidence: `0.75`
- task250 calibrated repair confidence: `0.85`
- Repair minimum confidence: `0.8`
- task250 calibrated repair gate passed: `True`
- Forced cost: `$0.070710`
- Integrity gate passed: `True`
- Smoke gate passed: `True`
- Broad API allowed next: `False`
- Next protocol: `r147_bounded_smoke_result_to_claim_and_expansion_protocol`

| Task | Label | Source | Baseline | Selected | Truth | Router repair | Raw repair confidence | Calibrated confidence | Fix | Harm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `task_8` | `clean` | `baseline` | `E` | `E` | `E` | `` | `` | `` | `False` | `False` |
| `task_108` | `noisy` | `rank5_CalibratedEdgePromptRepairContractFinalRefer` | `B` | `D` | `D` | `NONE` | `0.0` | `` | `True` | `False` |
| `task_188` | `clean` | `baseline` | `D` | `D` | `D` | `` | `` | `` | `False` | `False` |
| `task_250` | `clean` | `rank5_CalibratedEdgePromptRepairContractFinalRefer` | `A` | `E` | `E` | `E` | `0.75` | `0.85` | `True` | `False` |

## Interpretation

R146 is the first fresh bounded API smoke where the calibrated repair final gate recovers clean `task_250` while preserving the fallback clean guards. This supports a same-four-task smoke claim only. It does not authorize broad tail34, transfer, robustness, or SCI-readiness claims until a separate result-to-claim and expansion protocol freezes the next evaluation scope.
