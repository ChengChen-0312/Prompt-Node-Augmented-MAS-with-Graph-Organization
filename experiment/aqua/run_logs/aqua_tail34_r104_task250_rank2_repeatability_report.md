# R104 Task250 Rank2 Repeatability Audit

**Claim boundary**: task250 rank2 repeatability audit; no new API

- Predictions: `['E', 'A']`
- Unique predictions: `['A', 'E']`
- Stable prediction: `False`
- Solved pattern: `[True, False]`

| Run | Prediction | Truth | Solved | Source |
| --- | --- | --- | --- | --- |
| `R100` | `E` | `E` | `True` | `experiment/aqua/aqua_tail34_r100_forced_template_rank2_task250_results.jsonl` |
| `R103` | `A` | `E` | `False` | `experiment/aqua/aqua_tail34_r103_rank2_regression_smoke_results.jsonl` |

## Interpretation

The same task/template rank is not stable across R100 and R103: it predicts `E` once and `A` once. Template-rank selection alone is not enough; the next selector needs stability, consensus, or repeated-evidence checks before deployment.
