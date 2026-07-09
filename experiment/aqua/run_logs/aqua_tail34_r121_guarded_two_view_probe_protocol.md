# R121 Guarded Two-View / Graph-Policy Probe Protocol

**Claim boundary**: protocol only; no new API, accuracy, or cost result

- Protocol only: `True`
- No API run: `True`
- Regression tasks: `['task_8', 'task_108', 'task_188', 'task_250']`
- Candidate protocols: `['guarded_router_calibrated_two_view', 'guarded_candidate_calibrated_two_view', 'train_time_graph_policy_probe']`
- Max PromptNode views per task: `2`
- Broad API before smoke: `False`
- Explicit PromptNode evidence required: `True`
- Strong contract or two-view agreement required: `True`
- Blocks direct-vote-only switches: `True`
- R119 clean harm blocked by protocol: `True`
- R119 PromptNode graph hits: `0/4`
- R119 strong router-contract rows: `0/4`

## Required Gate Checks

- `no_switch_without_explicit_promptnode_graph_or_strong_contract`
- `no_switch_without_two_view_nonbaseline_agreement_unless_graph_policy_confident`
- `no_broad_api_before_same_four_task_smoke_passes`
- `same_model_gpt_4o_2024_08_06`
- `tail34_artifacts_not_training_data`

## Interpretation

R121 corrects the R119 drift before spending more API. The next smoke must not switch when the only support is a calibrated direct-vote signal without explicit PromptNode graph or strong router-contract evidence. This keeps the method aligned with the update2 first-class virtual-node design.
