# R163 R001-Style Selective PromptNode/PromptEdge Policy Export

**Claim boundary**: Offline target export only; no API calls and no answer-accuracy claim.

## Inputs

- Source rows: R077 clean-fix graph-policy distillation.
- Objective-safety features: R112 first200 targets.
- API calls: `0`.
- Answer accuracy claim: `none`.

## Export Summary

- Policy rows: `800`
- Selective insert rows: `4`
- Fallback rows: `796`
- Matched R112 rows: `800`
- Selector forbidden-field violations: `0`
- PromptEdge type counts: `agent_flow=6, forward_verified=4, verify_contract=4, write_memory=10`
- Output JSONL: `experiment/aqua/aqua_first200_r163_selective_promptedge_policy_rows.jsonl`

## PyG Export

- Manifest JSONL: `experiment/aqua/aqua_first200_r163_selective_promptedge_pt_manifest.jsonl`
- PT files: `4`
- PromptNode PT files: `4`
- PromptNode edge-permission PT files: `4`
- PT outcome-field violations: `0`

## Interpretation

R163 moves the next branch back toward the R001 training paradigm: the exported positives are graph targets that contain PromptNodes and PromptEdge metadata before execution. Unlike R055, the export is selective: fallback rows are explicitly represented and only objective-safety switch rows with high-margin PromptNode graph targets become positive `.pt` files.

This is not a result that PromptNodes improve AQuA accuracy. The next step is R164: train or smoke-test ARGDesigner's graph generator on these selective targets, then audit at R165 before broad API use.
