# R118 Lightweight Objective Probe Replay

**Claim boundary**: offline probe replay only; no new API, measured cost, or accuracy claim

- Replay only: `True`
- Candidate subsets: `10`
- One-view successes: `1`
- Two-view successes: `3`
- Best min-view subset: `['calibrated']`
- Best min-view target agreement: `34/34`
- Recommended probe protocol: `calibrated_single_view_probe`
- API result ready: `False`

| Subset | Views | Agreement | Switches | False switches | Missed switches |
| --- | ---: | ---: | --- | --- | --- |
| `router` | `1` | `33/34` | `['task_108']` | `[]` | `['task_250']` |
| `candidate` | `1` | `33/34` | `['task_108']` | `[]` | `['task_250']` |
| `conservative` | `1` | `33/34` | `['task_108']` | `[]` | `['task_250']` |
| `calibrated` | `1` | `34/34` | `['task_108', 'task_250']` | `[]` | `[]` |
| `router,candidate` | `2` | `33/34` | `['task_108']` | `[]` | `['task_250']` |
| `router,conservative` | `2` | `33/34` | `['task_108']` | `[]` | `['task_250']` |
| `router,calibrated` | `2` | `34/34` | `['task_108', 'task_250']` | `[]` | `[]` |
| `candidate,conservative` | `2` | `33/34` | `['task_108']` | `[]` | `['task_250']` |
| `candidate,calibrated` | `2` | `34/34` | `['task_108', 'task_250']` | `[]` | `[]` |
| `conservative,calibrated` | `2` | `34/34` | `['task_108', 'task_250']` | `[]` | `[]` |

## Interpretation

R118 shows that the calibrated view alone reproduces the frozen R109 objective-safety target actions in an offline replay. This supports making `calibrated_single_view_probe` the first R117 smoke candidate, but it is not a measured API result or cost claim.
