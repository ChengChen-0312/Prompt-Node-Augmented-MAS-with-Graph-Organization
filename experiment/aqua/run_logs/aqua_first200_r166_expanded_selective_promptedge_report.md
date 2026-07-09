# R166 Expanded Selective PromptNode/PromptEdge Targets

**Claim boundary**: Offline expanded target export only; no API calls and no answer-accuracy claim.

## Export Summary

- Policy rows: `800`
- Positive graph rows: `76`
- Switch-critical inserts: `4`
- Preserve-safe inserts: `72`
- Suppress/fallback rows: `724`
- Selector forbidden-field violations: `0`
- PromptEdge type counts: `agent_flow=100, forward_verified=76, verify_contract=76, write_memory=176`
- Output JSONL: `experiment/aqua/aqua_first200_r166_expanded_selective_promptedge_rows.jsonl`

## PyG Export

- Manifest JSONL: `experiment/aqua/aqua_first200_r166_expanded_selective_promptedge_pt_manifest.jsonl`
- PT files: `76`
- PromptNode PT files: `76`
- PromptNode edge-permission PT files: `76`
- PT outcome-field violations: `0`

## Interpretation

R166 expands R163's sparse switch-only target set. The export keeps the four switch-critical PromptNode graphs, adds seventy-two preserve-safe PromptNode graphs for structure learning, and keeps seven hundred twenty-four rows as suppress/fallback selector negatives. This is still an offline target artifact, not an answer-accuracy result.
