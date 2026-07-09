# R111 Objective-Safety Proxy Feature Gap

**Claim boundary**: feature coverage audit only; no proxy training or accuracy claim

- Required feature count: `3`
- Existing R078 feature count: `22`
- Directly covered required features: `[]`
- Proxy training ready: `False`
- Recommended next artifact: `first200_objective_safety_feature_export`

## Missing Required Features

- `objective_prediction_differs_from_baseline`
- `objective_top_score`
- `baseline_direct_votes_split`

## Interpretation

R078 is useful evidence that first200 graph-policy targets are learnable, but it is not a valid proxy for the R109 objective-safety rule. The required objective-vs-baseline and direct-split fields must be exported for first200/non-tail34 data before training the R110 proxy.
