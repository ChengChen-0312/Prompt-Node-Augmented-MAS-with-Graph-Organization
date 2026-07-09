# R125 Goal Audit After R121-R125

**Claim boundary**: five-iteration goal audit and correction, not an accuracy result

## Window

- R121: guarded two-view / graph-policy protocol
- R122: strict update2 replay checker
- R123: explicit PromptNode template preflight
- R124: explicit-template guarded smoke
- R125: goal audit and correction

## Verdict

Status: `aligned_after_correction`

R121-R124 remained aligned with the update2 design because they restored first-class PromptNode graph evidence before switching. The new correction is methodological: rank-1 explicit templates are not enough for the SCI-Q2 clean-reasoning claim because the smoke recovers only noisy `task_108` and misses clean `task_250`.

## Evidence

- R123 candidate update2 metadata: `4/4`
- R123 forbidden-field violations: `0/4`
- R124 selected accuracy: `3/4`
- R124 baseline accuracy: `2/4`
- R124 fix/harm: `1/0`
- R124 clean fix/harm: `0/0`
- R124 noisy fix/harm: `1/0`
- R124 PromptNode graph evidence on switches: `2/2`
- R124 switch update2 metadata: `2/2`
- R124 smoke gate passed: `False`
- Broad API allowed next: `False`

## Drift Detected

`rank1_explicit_template_path_restores_update2_evidence_but_fails_clean_fix_gate`

The drift risk is no longer missing virtual-node evidence. It is over-promoting a rank-1 explicit-template path that satisfies update2 metadata requirements but does not recover a clean reasoning fix. For SCI-Q2, this must stay as a negative boundary unless a selector or trained graph policy recovers clean `task_250` without harming `task_8` or `task_188`.

## Correction

- demote rank1 explicit-template selection to mechanism evidence; do not broaden API; train or select a graph/template policy that recovers clean task_250 while preserving task_8 and task_188 clean guards
- Next protocol: `train_or_select_clean_fix_graph_policy_before_smoke`
- Required clean harm guards: `['task_8', 'task_188']`
- Required clean recovery targets: `['task_250']`
- Allowed evidence sources next: `['first200_non_tail34_graph_policy_training', 'explicit_promptnode_template_metadata', 'guarded_multi_view_objective_features_without_tail34_training']`
