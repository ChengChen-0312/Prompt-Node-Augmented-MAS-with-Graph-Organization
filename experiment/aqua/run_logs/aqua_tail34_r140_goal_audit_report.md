# R140 Goal Audit After R136-R140

**Claim boundary**: five-iteration goal audit and correction, not an accuracy result

## Window

- R136: repair-field prompting pre-smoke
- R137: repair-field API smoke with forwarding gap
- R138: router repair-forwarding prompt hardening
- R139: repair-forwarding API smoke with low-confidence rejection
- R140: five-iteration goal audit

## Verdict

Status: `aligned_continue_with_calibration_protocol`
Drift detected: `False`
Drift type: `none_forwarding_fixed_but_threshold_overfit_blocked`

The R136-R139 window stayed aligned with the SCI-Q2 goal because it kept PromptNode as a first-class node/edge graph mechanism, blocked broad API, and did not lower the final repair threshold to fit task250. The forwarding gap is fixed, but the clean gate is still not met.

## Evidence

- Maintained update2 alignment: `True`
- Maintained edge-prompt alignment: `True`
- Maintained robustness alignment: `True`
- Forwarding gap fixed: `True`
- Clean gate still not met: `True`
- Confidence calibration needed: `True`
- Threshold lowering without protocol allowed: `False`
- R139 selected accuracy: `3/4`
- R139 clean fix/harm: `0/0`
- R139 task250 repair option: `E`
- R139 task250 repair confidence: `0.5`
- R139 repair min confidence: `0.8`
- R139 smoke gate passed: `False`
- Broad API allowed next: `False`

## Correction

- do not lower the repair confidence threshold directly on task250; first design a leakage-safe calibration protocol using non-tail34 evidence and then retest only the same four-task gate
- Next protocol: `repair_confidence_calibration_protocol_before_api`
- Calibration protocol requirements: `['no tail34 labels or task ids as threshold-training features', 'calibrate confidence mapping on first200/non-tail34 or synthetic format controls', 'keep task_8 and task_188 as clean harm guards', 'require task_250 clean recovery before broad tail34', 'run transfer validation before robustness or SCI-Q2 readiness claims']`
- Required clean harm guards: `['task_8', 'task_188']`
- Required clean recovery targets: `['task_250']`
- Noisy optional targets: `['task_108']`
- Next goal audit due: `R145`

## Current Best Signals

- Best tail34 signal: `R065 objective-guided replay 31/34 versus ARG 28/34`
- Best fresh integrated signal: `R074 fresh surgical cascade 29/34 versus internal ARG 28/34`
- Current edge-prompt signal: `R139 fixes repair forwarding but remains 3/4 on the four-task gate`
