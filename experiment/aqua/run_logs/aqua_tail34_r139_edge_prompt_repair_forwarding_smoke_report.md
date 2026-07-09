# R139 Edge-Prompt Repair-Forwarding Smoke

**Claim boundary**: same-four-task repair-forwarding smoke; forwarding is fixed but clean recovery, broad held-out evaluation, transfer, robustness, and SCI-readiness remain unsupported

- Decision method: `EdgePromptRepairContractFinalRefer`
- Baseline accuracy: `2/4`
- Selected accuracy: `3/4`
- Switch tasks: `['task_108', 'task_250']`
- Fallback tasks: `['task_8', 'task_188']`
- PN graph evidence on switches: `2/2`
- Switch update2 metadata: `2/2`
- Fix/harm: `1/0`
- Clean fix/harm: `0/0`
- Noisy fix/harm: `1/0`
- Switch router repair fields present: `2/2`
- Switch router repair option non-none: `1/2`
- task250 verifier repair candidate present: `True`
- task250 router repair forwarded: `True`
- Verifier-router repair forwarding gap: `False`
- task250 router repair option: `E`
- task250 router repair binding status: `NUMERIC_NEAREST_WITH_TYPO_CHECK`
- task250 router repair confidence: `0.5`
- Repair minimum confidence: `0.8`
- task250 repair confidence gate passed: `False`
- task250 repair forwarded but rejected for low confidence: `True`
- Forced cost: `$0.071475`
- Integrity gate passed: `True`
- Smoke gate passed: `False`
- Broad API allowed next: `False`
- Next protocol: `r140_goal_audit_then_repair_confidence_calibration_protocol`

| Task | Label | Source | Baseline | Selected | Truth | Router repair | Repair confidence | Gate passed | Fix | Harm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `task_8` | `clean` | `baseline` | `E` | `E` | `E` | `` | `` | `False` | `False` | `False` |
| `task_108` | `noisy` | `rank5_EdgePromptRepairContractFinalRefer` | `B` | `D` | `D` | `NONE` | `0.0` | `False` | `True` | `False` |
| `task_188` | `clean` | `baseline` | `D` | `D` | `D` | `` | `` | `False` | `False` | `False` |
| `task_250` | `clean` | `rank5_EdgePromptRepairContractFinalRefer` | `A` | `None.` | `E` | `E` | `0.50` | `False` | `False` | `False` |

## Interpretation

R139 fixes the R137 Verifier-to-Router forwarding gap: task250 now carries `REPAIR_OPTION: E` with `NUMERIC_NEAREST_WITH_TYPO_CHECK`. The final repair gate still rejects it because the router confidence is `0.50`, below the `0.80` threshold. This preserves conservatism but does not pass the clean recovery gate. The next step is the scheduled R140 goal audit, then a calibration protocol if the goal remains aligned.
