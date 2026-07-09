# R301 Conservative Census Gate

**Claim boundary**: Accuracy-bearing offline gate over existing ARG transfer outputs. It demonstrates a generic PromptNode/PromptEdge logic, but still needs prospective validation before a broad SCI-Q2 claim.

- Official: R301 `89/100` vs ARG `88/100`; delta `1`
- Audit-clean: R301 `91/100` vs ARG `90/100`; delta `1`
- Official fix/harm: `1/0`
- Audit-clean fix/harm: `1/0`
- Switches: `1`; tasks `['MMLU-high_school_statistics_test-32']`
- Beats ARG official/audit-clean: `True` / `True`
- No-harm official/audit-clean: `True` / `True`

## Interpretation

R301 fixes the complete-population-vs-inference statistics failure through a generic PromptNode gate. It intentionally keeps the ARG answer on known noisy physics and chemistry items instead of optimizing toward wrong labels. The next step is to train this as a SafetyGatePN with asymmetric loss and validate prospectively.
