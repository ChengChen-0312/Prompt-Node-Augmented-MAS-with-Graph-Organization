# R137 Edge-Prompt Repair Smoke

**Claim boundary**: same-four-task edge-prompt repair smoke; broad claims require clean recovery, full held-out validation, and transfer

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
- Switch router repair option non-none: `0/2`
- task250 verifier repair candidate present: `True`
- task250 router repair forwarded: `False`
- Verifier-router repair forwarding gap: `True`
- Forced cost: `$0.074315`
- Integrity gate passed: `True`
- Smoke gate passed: `False`
- Broad API allowed next: `False`
- Next protocol: `router_repair_field_forwarding_prompt_hardening`

| Task | Label | Source | Baseline | Selected | Truth | Router repair | Verifier repair candidate | Fix | Harm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `task_8` | `clean` | `baseline` | `E` | `E` | `E` | `` | `False` | `False` | `False` |
| `task_108` | `noisy` | `rank5_EdgePromptRepairContractFinalRefer` | `B` | `D` | `D` | `NONE` | `False` | `True` | `False` |
| `task_188` | `clean` | `baseline` | `D` | `D` | `D` | `` | `False` | `False` | `False` |
| `task_250` | `clean` | `rank5_EdgePromptRepairContractFinalRefer` | `A` | `None.` | `E` | `NONE` | `True` | `False` | `False` |

## Interpretation

R137 confirms the repair fields are emitted in PN_Router output, so the edge-prompt interface is live. However, task250 still fails because PN_Verifier suggests a repair candidate while PN_Router forwards `REPAIR_OPTION: NONE`. The next correction is therefore the verifier-to-router repair forwarding prompt, not broader evaluation.
