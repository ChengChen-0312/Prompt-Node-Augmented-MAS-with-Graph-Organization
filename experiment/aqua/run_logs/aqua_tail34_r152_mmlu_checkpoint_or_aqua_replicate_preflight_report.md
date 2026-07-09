# R152 MMLU Checkpoint or AQuA Replicate Preflight

**Claim boundary**: preflight only; no API run, no transfer result, no independent AQuA replicate, and no SCI-Q2 readiness claim

## Transfer Branch

- MMLU transfer data ready: `True`
- MMLU transfer rows: `100`
- MMLU evaluator available: `True`
- Compatible MMLU ARG checkpoint available: `False`
- MMLU checkpoint candidates: `[]`
- Transfer branch allowed: `False`

## AQuA Same-Method Replicate Branch

- AQuA dataset rows: `254`
- AQuA known split row count: `254`
- AQuA unseen row count: `0`
- R112 uses next100 in rule training: `True`
- Independent same-method AQuA replicate ready: `False`
- Same-method replicate blocker: `no_unseen_aqua_rows_and_next100_used_in_r112_rule_training`

## Next Gate

- Broad API allowed next: `False`
- Chosen next work: `r153_mmlu_checkpoint_build_or_import_protocol`
- Next goal audit due: `R155`

## Interpretation

R152 does not support running transfer API yet: the transfer split and evaluator exist, but no compatible MMLU ARG checkpoint is available. It also blocks an independent AQuA same-method replicate claim because all 254 AQuA rows are already covered by existing splits and next100 was used in the R112 rule-training source. The next defensible step is to build or import a compatible MMLU ARG checkpoint before transfer.
