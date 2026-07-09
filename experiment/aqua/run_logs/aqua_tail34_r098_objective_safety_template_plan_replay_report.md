# R098 R097 Template Plan Replay over R092 Forced Results

**Claim boundary**: R097 plan replay over R092 forced-template results; no new API; not R095 reproduction

- ARG baseline solved: `28/34`
- Template-plan replay solved: `29/34`
- Switch plan count: `2`
- Forced result available for switches: `2`
- Desired prediction matches: `1`
- Desired prediction mismatches: `['task_250']`
- Fix/harm: `1/0`
- Clean fix/harm: `0/0`
- Noisy fix/harm: `1/0`

## Switch Replay

| Task | Audit label | ARG | R095 objective | R092 template | Match | Selected | Fix | Harm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `task_108` | `noisy` | `B` | `D` | `D` | `True` | `D` | `True` | `False` |
| `task_250` | `clean` | `A` | `E` | `A` | `False` | `A` | `False` | `False` |

## Interpretation

The explicit R083 rank-1 template plan reproduces the noisy `task_108` switch but not the clean `task_250` objective switch. Therefore R097 should not be promoted to a full held-out run as-is; the next step must search or train a template/graph policy that can recover the clean switch before spending on full API validation.
