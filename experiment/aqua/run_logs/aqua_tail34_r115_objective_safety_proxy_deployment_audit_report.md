# R115 Objective-Safety Proxy Deployment Audit

**Claim boundary**: deployment dependency audit only; no accuracy, cost-reduction, or API claim

- Learned rule: `diff_and_top_score_ge_3_or_split`
- Rule features: `['objective_prediction_differs_from_baseline', 'objective_top_score', 'baseline_direct_votes_split']`
- Features requiring objective-guided trace: `['objective_prediction_differs_from_baseline', 'objective_top_score']`
- Features requiring ARG baseline trace: `['baseline_direct_votes_split']`
- Requires multi-view objective features: `True`
- Single-template guard sufficient: `False`
- Cheap single-template deployable: `False`
- Cost-reduction claim ready: `False`
- Prospective API ready: `False`
- Input-field violations: `0`

## Supporting Positive Checks

- R113 frozen target agreement: `34/34`
- R114 regression action agreement: `4/4`
- R114 clean fix/harm: `1/0`

## Deployment Blockers

- requires objective-guided multi-view trace features
- single rank5-template features were insufficient in R108
- no prospective API validation with the proxy has been run
- no measured cost reduction for proxy deployment exists

## Interpretation

R115 prevents overclaiming the R113/R114 proxy as a cheap deployed method. The proxy is reproducible and passes the current regression stress, but it still depends on objective-guided multi-view trace features and has no prospective API or measured cost-reduction result.
