# R271 Tail34 Final Claim Table

**Claim boundary**: paper_table_generation_only_no_new_api

| Variant | Official | Excl. 59/139/228 | Correct 114 | Excl. 114 | Cost | Role |
|---|---:|---:|---:|---:|---:|---|
| `ARG` | `28/34` | `28/31` | `29/31` | `28/30` | `$0.93285` | baseline |
| `R065` | `31/34` | `31/31` | `30/31` | `30/30` | `$5.050805` | highest official replay score, noisy task114 risk |
| `R068` | `31/34` | `31/31` | `30/31` | `30/30` | `$3.597409` | cost-reduced replay retaining R065 score |
| `R095` | `30/34` | `30/31` | `31/31` | `30/30` | `$5.050805` | safety-gated replay, not cost-reduced |
| `R267` | `30/34` | `30/31` | `31/31` | `30/30` | `$3.597409` | cost-reduced plus safety-gated replay |

Report official and audit-clean columns side by side. Use R065/R068 for the official improvement signal and R095/R267 for the safety/audit-clean interpretation. Do not claim broad transfer superiority.
