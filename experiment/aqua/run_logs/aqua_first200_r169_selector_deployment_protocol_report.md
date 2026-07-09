# R169 Selector-Gated PromptEdge Deployment Protocol

**Claim boundary**: Protocol only. No API calls, no answer-accuracy result, and no SCI-Q2 readiness claim.

## Purpose

R167 proved that the graph generator can emit PromptNodes before execution, but it over-generates them. R168 supplied a lightweight target-agreement selector. R169 freezes how those two pieces may be combined before any API evaluation.

## Required Artifacts

- R166 expanded targets: `experiment/aqua/aqua_first200_r166_expanded_selective_promptedge_rows.jsonl`
- R167 checkpoint: `experiment/aqua/output/aqua_r166_expanded_selective_promptedge_r167_short/ef_best_model.pth`
- R168 selector summary: `experiment/aqua/res_logs/aqua_first200_r168_promptedge_selector_summary.json`

## Selector Gate

The default action is `fallback_to_arg`.

PromptNode graph execution is allowed only when all conditions hold:

1. R168 selector predicts `positive_graph_target`.
2. The generated graph contains `PN_Memory`, `PN_Verifier`, and `PN_Router`.
3. The generated graph is a DAG.
4. PromptEdge metadata contains a write-memory, verify-contract, and forward-verified path.
5. Final decision uses router suppression for `NO_EXACT_OPTION`; it must not choose the nearest option after a no-exact-option contract.

Forbidden selector/deployment inputs:

- `true_answer`
- `predicted_answer`
- `is_solved`
- `clean_label`
- `audit_label`
- `task_id`

## Current Gate Evidence

- R168 eval target agreement: `0.995`
- R168 eval positive recall: `0.971`
- R168 input-field violations: `0`

These numbers meet the protocol threshold for a bounded smoke, but they are target agreement only. They do not prove answer accuracy.

## Next Run Boundary

R170 goal audit is mandatory before API use. If R170 passes, R171 may run only a bounded smoke:

- maximum API tasks: `4`
- report internal ARG baseline, selector decision, PromptNode graph evidence, fix/harm, clean fix/harm when audit labels exist, and cost
- no broad evaluation and no paper claim from the smoke alone
