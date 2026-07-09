# R149 Transfer Checkpoint or AQuA Replicate Protocol

**Claim boundary**: checkpoint-or-replicate protocol only; AQuA next100 is PromptNode-family evidence, not same-method significance evidence for R147

## Transfer Branch

- Transfer checkpoint available: `False`
- Transfer branch allowed: `False`
- Transfer blocker: `missing_compatible_mmlu_arg_checkpoint`

## AQuA Replicate Branch

- AQuA next100 replicate available: `True`
- next100 selector: `multi_contract_union`
- next100 baseline accuracy: `82/100`
- next100 selected accuracy: `87/100`
- next100 delta vs baseline: `5`
- next100 fix/harm: `5/0`
- next100 McNemar exact p: `0.0625`
- next100 significant at 0.05: `False`
- Same method as R147: `False`
- Combined significance claim allowed: `False`
- Family replicate claim allowed: `True`

## Next Gate

- R150 goal audit required next: `True`
- Broad API allowed next: `False`
- Next protocol: `r150_goal_audit_before_any_more_api`

## Interpretation

R149 keeps the project from overclaiming. Transfer cannot run without a compatible MMLU checkpoint. Existing AQuA next100 evidence is useful as PromptNode-family replication (`87/100` vs `82/100`, `5/0` fix/harm), but because it uses a different multi-contract selector, it cannot be combined with R147 as same-method statistical evidence. The next required step is the scheduled R150 goal audit.
