# R075 Fresh Cascade Pareto Report

## Summary

| Run | Accuracy | Baseline | Clean | Fix/Harm | Clean Fix/Harm | Triggered | View Calls | Cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R069 | 29/34 | 26/34 | 27/28 | 3/0 | 3/0 | 25/34 | None | $3.908995 |
| R072 | 29/34 | 27/34 | 26/28 | 2/0 | 2/0 | 26/34 | 58/104 | $2.826040 |
| R074 | 29/34 | 28/34 | 26/28 | 1/0 | 0/0 | 13/34 | 28/52 | $1.828715 |

## Interpretation

- Accuracy-cost frontier: `R074`.
- Clean-mechanism frontier: `R069, R072, R074`.
- R072 clean fixes lost by R074: `task_188, task_56`.
- R074 new fix not in R072: `task_108`.

R074 is best on accuracy-cost among measured fresh runs, but R069/R072 carry the clean-fix mechanism signal. The next method should preserve clean fixes while reducing cost.
