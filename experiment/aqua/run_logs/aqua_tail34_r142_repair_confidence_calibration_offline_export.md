# R142 Repair-Confidence Calibration Offline Export

**Claim boundary**: offline calibration export only; no API, final-gate change, accuracy, transfer, robustness, or SCI-readiness claim

- Offline export only: `True`
- No API run: `True`
- Uses tail34 training source: `False`
- Direct threshold lowering allowed: `False`
- Synthetic control rows: `6`
- Accepted positive controls: `3`
- Rejected negative controls: `3`
- Forbidden training-field violations: `0`
- R139 task250 eval only: `True`
- R139 task250 used for training: `False`
- R139 task250 calibrated confidence: `0.95`
- R139 task250 calibration would pass: `True`
- Broad API allowed next: `False`
- Next protocol: `calibrated_repair_final_gate_offline_replay`

## Interpretation

R142 exports synthetic calibration controls and verifies that no tail34-specific training field is present. The R139 task250 row is evaluated only as a diagnostic. This supports building an offline calibrated final-gate replay next, but it is not an accuracy result and does not change the production gate.
