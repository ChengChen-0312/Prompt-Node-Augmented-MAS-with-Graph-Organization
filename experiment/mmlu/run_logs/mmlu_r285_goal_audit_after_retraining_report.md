# R285 Goal Audit After Retraining

**Claim boundary**: Goal audit only. It checks whether R281-R284 stayed aligned with the SCI-Q2 research goal and whether checkpoint-level API evaluation is justified.

## Status

- Goal alignment: `aligned_but_blocked_on_structure`
- Protocol followed: `True`
- Clean ARG retrained: `True`
- PromptNode retrained with required roles: `True`
- PromptNode generates PN: `True`
- PromptNode all-PN-role rate: `0.125`
- PromptNode contract-ready rate: `0.041666666666666664`
- API eval allowed next: `False`
- SCI-Q2 ready: `False`

## Blockers

- R284 shows PromptNode generation exists but full PN/PE contract structure is unstable.

## Decision

Do not run costly checkpoint-level API evaluation yet; first improve the train-time graph policy or decoding so generated PromptNode graphs contain the complete Memory -> Verifier -> Router contract path reliably.

## Next Runs

- `R286_constrained_promptnode_decoding`
- `R287_promptnode_chain_retrain`
- `R288_no_api_graph_audit`
- `R289_checkpoint_level_api_eval_if_R288_passes`
- `R290_goal_audit`
