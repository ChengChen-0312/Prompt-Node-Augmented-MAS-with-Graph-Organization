# R069 Fresh Integrated Comparison

## Summary

- R069 fresh integrated: `29/34`
- R069 internal ARG baseline: `26/34`
- Delta vs internal baseline: `+3`; fix/harm `3/0`
- Clean: `27/28`; clean fix/harm `3/0`
- Multi-view runs: `25/34`; cost `$3.908995`

## Cross-Trace Boundary

- Versus historical R059 ARG: fixes `['task_108']`, harms `[]`, delta `+1`.
- Versus R065 replay objective: fixes `[]`, harms `['task_114', 'task_250']`, delta `-2`.
- R069 internal baseline differs from R059 on `6` tasks, so R069 should not be described as a deterministic replay of R059/R065.

## R069 Switches

| Task | Internal ARG | Selected | Gold | Method | Top score | Solved |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| task_56 | None | A | A | router | 2 | True |
| task_59 | None | B | C | router | 2 | False |
| task_8 | None | E | E | router | 2 | True |
| task_188 | C | D | D | candidate | 2 | True |

## Interpretation

R069 is a fresh integrated run. It improves over its own fresh internal baseline, but the internal baseline differs from the historical R059 trace; therefore R069 should be claimed as fresh integrated evidence with stochastic-baseline caveat, not as a direct reproduction of R065 replay.
