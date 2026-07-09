# R100 Task250 Template Rank Sweep Report

**Claim boundary**: one-task task250 rank sweep; not held-out accuracy

- Task: `task_250`
- Desired prediction: `E`
- Sweep ranks: `[2, 3, 4, 5]`
- Matching ranks: `[2, 5]`
- Non-matching ranks: `[3, 4]`
- Best matching rank: `2`
- Total cost: `$0.146630`

| Rank | Prediction | Matches desired | Solved | Cost | Prompt tokens | Completion tokens |
| ---: | --- | --- | --- | ---: | ---: | ---: |
| `2` | `E` | `True` | `True` | `$0.038215` | `2858` | `1595` |
| `3` | `A` | `False` | `False` | `$0.036710` | `2866` | `1492` |
| `4` | `A` | `False` | `False` | `$0.034870` | `3146` | `1276` |
| `5` | `E` | `True` | `True` | `$0.036835` | `3587` | `1260` |

## Interpretation

Ranks 2 and 5 recover the clean `task_250` target prediction `E`, while ranks 3 and 4 fall back to `A`. This gives a concrete template-rank candidate for the next clean-safe smoke, but it is a one-task search and cannot be reported as held-out accuracy.
