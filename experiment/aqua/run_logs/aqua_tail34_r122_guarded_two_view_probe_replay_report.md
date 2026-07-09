# R122 Guarded Two-View Probe Replay

**Claim boundary**: guarded replay over existing traces; no new API or accuracy improvement claim

- Replay only: `True`
- Total tasks: `34`
- Baseline accuracy: `28/34`
- Objective accuracy: `31/34`
- Guarded accuracy: `28/34`
- Objective switch tasks: `['task_114', 'task_59', 'task_108', 'task_250']`
- Guarded switch tasks: `[]`
- Guarded Fix/Harm: `0/0`
- Guarded Clean Fix/Harm: `0/0`
- PromptNode graph evidence rows: `0/34`
- Strong router-contract rows: `0/34`
- Blocks all objective switches: `True`
- Update2 evidence ready: `False`

| Task | ARG | Objective | Guarded | Truth | Objective source | Switch allowed | Update2 evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `task_114` | `C` | `D` | `C` | `D` | `objective_top` | `False` | `False` |
| `task_59` | `B` | `D` | `B` | `C` | `objective_top` | `False` | `False` |
| `task_108` | `B` | `D` | `B` | `D` | `objective_top` | `False` | `False` |
| `task_250` | `A` | `E` | `A` | `E` | `objective_top` | `False` | `False` |

## Interpretation

R122 shows that the strict R121 update2 guard blocks the existing objective switches because the stored objective traces do not contain explicit PromptNode graph or strong router-contract evidence. This is a necessary negative boundary: the next positive method must produce first-class PromptNode evidence prospectively, not only replay direct-vote support.
