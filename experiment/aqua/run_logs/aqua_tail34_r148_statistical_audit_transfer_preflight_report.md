# R148 Tail34 Statistical Audit and Transfer Preflight

**Claim boundary**: statistical audit and transfer preflight only; no new API, fresh full-run, transfer, robustness, or SCI-readiness claim

## Tail34 Replay Statistics

- Baseline accuracy: `28/34`
- Selected accuracy: `30/34`
- Accuracy delta: `0.058824`
- Baseline Wilson 95% CI: `[0.664863, 0.91651]`
- Selected Wilson 95% CI: `[0.733792, 0.953286]`
- Paired improvements: `2`
- Paired regressions: `0`
- McNemar exact two-sided p: `0.5`
- Significant at 0.05: `False`
- Baseline correct per dollar: `30.015544`
- Selected correct per dollar: `29.893579`
- Cost-normalized superiority supported: `False`

## Transfer Preflight

- MMLU transfer JSONL exists: `True`
- MMLU transfer rows: `100`
- MMLU task split exists: `True`
- MMLU evaluator exists: `True`
- MMLU subject count: `15`
- MMLU ARG checkpoint available: `False`
- Transfer API allowed next: `False`
- Broad API allowed next: `False`
- Next protocol: `r149_transfer_checkpoint_or_aqua_replicate_protocol`

## Interpretation

The R147 replay improves accuracy by two paired fixes and zero regressions, but with only two discordant pairs the exact McNemar p-value is `0.5`; the result is not statistically significant. Transfer data and evaluator scaffolding exist, but no compatible local MMLU ARG checkpoint was found, so transfer API remains blocked until the checkpoint path is supplied or a new compatible checkpoint is produced.
