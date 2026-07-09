# R123 Explicit PromptNode Template Preflight

**Claim boundary**: preflight over explicit PromptNode template candidates; no API, accuracy, or cost result

- Preflight only: `True`
- No API run: `True`
- Regression tasks: `['task_8', 'task_108', 'task_188', 'task_250']`
- Candidate source tasks: `4/4`
- Candidate tasks with update2 metadata: `4/4`
- Candidate forbidden-field violations: `0/4`
- Top candidate PromptNode roles: `['PN_Memory', 'PN_Router', 'PN_Verifier']`
- R097 API-required tasks: `['task_108', 'task_250']`
- R097 fallback tasks in regression set: `['task_8', 'task_188']`
- Same four-task smoke allowed next: `True`
- Broad API allowed next: `False`
- Next protocol: `same_four_task_explicit_template_guarded_smoke`

| Task | Candidates | Update2 metadata | Forbidden-field violation | R097 action | API required | Top support | PN roles |
| --- | ---: | --- | --- | --- | --- | ---: | --- |
| `task_8` | `5` | `True` | `False` | `fallback_to_arg` | `False` | `35` | `PN_Memory,PN_Router,PN_Verifier` |
| `task_108` | `5` | `True` | `False` | `switch_to_objective` | `True` | `35` | `PN_Memory,PN_Router,PN_Verifier` |
| `task_188` | `5` | `True` | `False` | `fallback_to_arg` | `False` | `35` | `PN_Memory,PN_Router,PN_Verifier` |
| `task_250` | `5` | `True` | `False` | `switch_to_objective` | `True` | `35` | `PN_Memory,PN_Router,PN_Verifier` |

## Interpretation

R123 separates two facts that were conflated after R122. The R083 candidate pool does contain first-class PromptNode graph candidates for the four regression tasks, with identities, permissions, budgets, lifecycle actions, and no runtime-answer fields. However, the current R097 switch plan only attaches templates for `task_108` and `task_250`, so broad API evaluation remains blocked. The next permitted step is a same-four-task guarded smoke that records explicit template evidence on every candidate switch before any larger tail34 run.
