# R262 AQuA Paper-Ready Result Tables

**Claim boundary**: No-API table export only; supports paper framing, not new accuracy claims.

| Run | Accuracy | Delta vs ARG | Fix/Harm | Clean Fix/Harm | Cost | Cost x ARG | Boundary |
|---|---:|---:|---:|---:|---:|---:|---|
| `ARG` ARG tail34 baseline | `28/34` | `0` | `0/0` | `0/0` | `$0.932850` | `1.0` | baseline |
| `R065` objective-guided multi-view teacher | `31/34` | `3` | `3/0` | `1/0` | `$5.050805` | `5.414381` | expensive replay teacher |
| `R068` selective multi-view replay | `31/34` | `3` | `3/0` | `1/0` | `$3.597409` | `3.856364` | selective_multiview_replay_not_fresh_api_run |
| `R069` fresh integrated selective multi-view | `29/34` | `1` | `3/0` | `3/0` | `$3.908995` | `4.190379` | fresh_integrated_selective_multiview_promptnode_run |
| `R072` fresh integrated cascade | `29/34` | `1` | `2/0` | `2/0` | `$2.826040` | `3.029469` | fresh_integrated_cascade_multiview_promptnode_run |
| `R147` frozen selector replay | `30/34` | `2` | `2/0` | `1/0` | `$1.003560` | `1.0758` | frozen selector replay |

## Boundary Assessment

- Best accuracy run: `R065`
- Best fresh-cost run: `R072`
- Best cost-normalized run: `ARG`
- R065 is expensive teacher: `True`

## Interpretation

R065 remains the best AQuA accuracy teacher, but it is not the deployment method. The next step is to distill its trigger behavior into a cheaper selector and evaluate that selector without API.
