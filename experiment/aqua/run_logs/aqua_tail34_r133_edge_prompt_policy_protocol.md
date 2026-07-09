# R133 Edge-Prompt Policy Protocol

**Claim boundary**: protocol only; prompt-as-edge design and repair boundary, no API, accuracy, or cost result

- Protocol only: `True`
- No API run: `True`
- Prompt as first-class edge: `True`
- Node-only PromptNode sufficient: `False`
- Uses tail34 training source: `False`
- R132 smoke gate passed: `False`
- R132 exact-option repair required: `True`
- Switch tasks: `['task_108', 'task_250']`
- Fallback tasks: `['task_8', 'task_188']`
- Edge prompt schema fields: `['budget', 'edge_prompt_type', 'lifecycle_actions', 'option_binding_policy', 'permissions', 'prompt_contract', 'robustness_scope', 'source_role', 'target_role']`
- Edge prompt types: `['evidence_write', 'memory_to_verifier_read', 'mismatch_repair_escalation', 'router_to_final_answer_contract', 'verifier_to_router_forward']`
- Switches with edge prompt specs: `2/2`
- Switches with repair edge prompt: `2/2`
- Edge-prompt selector input violations: `0`
- Multi-dataset transfer required: `True`
- No task-id routing: `True`
- Broad API allowed next: `False`
- Next protocol: `edge_prompt_exact_option_repair_protocol_before_api`

| Task | Planned action | Template rank | Edge prompts | Repair edge | Selector violation |
| --- | --- | ---: | ---: | --- | --- |
| `task_8` | `fallback_to_arg` | `None` | `0` | `False` | `False` |
| `task_108` | `switch_to_promptnode_template` | `5` | `7` | `True` | `False` |
| `task_188` | `fallback_to_arg` | `None` | `0` | `False` | `False` |
| `task_250` | `switch_to_promptnode_template` | `5` | `7` | `True` | `False` |

## Interpretation

R133 incorporates the prompt-as-edge constraint. The method direction is no longer just adding PromptNode roles; communication edges also carry contracts governing what evidence may be written, read, forwarded, repaired, or abstained. This directly addresses the R132 failure mode: abstention is integrity-preserving, but clean recovery requires a repair edge that is still label-free, auditable, and transfer-tested.

This is a protocol artifact only. It blocks broad API expansion until the edge-prompt repair protocol is implemented and passes the same four-task clean gate.
