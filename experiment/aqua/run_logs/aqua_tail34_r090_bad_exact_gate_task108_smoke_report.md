# R090 Task108 Forced-Template Bad-Exact Gate Smoke Report

**Claim boundary**: single-task fresh smoke, not tail34 accuracy

- Task: `task_108`
- ARG baseline: `B` solved `0`
- Forced template: `D` solved `1`
- R088 gate: `D` solved `1`
- Gate action: `accept_template`
- Gate reason: `trusted_exact_contract`
- Cost: `$0.034620`
- Decision-field violations: `0`

## Interpretation

`task_108` is the only accepted switch in the R088 R058 replay. The fresh forced-template rank-1 smoke reproduces the same behavior: the explicit PromptNode graph predicts `D`, the R088 gate accepts it as a trusted exact contract, and the ARG baseline record is wrong. This is one fresh task-level mechanism check, not a tail34 accuracy result.
