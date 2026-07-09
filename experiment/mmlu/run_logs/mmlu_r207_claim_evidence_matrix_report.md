# R207 Consolidated Claim-Evidence Matrix

**Claim boundary**: no API, no new experiment, and no inflated paper claim. External result-to-claim review is pending because the Codex MCP reviewer is not available in the current toolset.

## Deterministic Evidence Check

The key numbers were checked against local source reports by direct text match:

| Number | Source |
|---|---|
| AQuA sync20 ARG `17/20` | `experiment/aqua/run_logs/aqua_sync20_eval20_breakdown.md` |
| Same LLM `gpt-4o-2024-08-06` | `experiment/aqua/run_logs/aqua_sync20_eval20_breakdown.md`, `experiment/aqua/run_logs/aqua_tail34_multiview_promptnode_validation_report.md` |
| AQuA tail34 ARG `28/34` | `experiment/aqua/run_logs/aqua_tail34_multiview_promptnode_validation_report.md` |
| AQuA tail34 objective selector `31/34` | `experiment/aqua/run_logs/aqua_tail34_multiview_promptnode_validation_report.md` |
| AQuA clean split `28/28`, clean fix/harm `1/0` | `experiment/aqua/run_logs/aqua_tail34_multiview_promptnode_validation_report.md` |
| MMLU raw contract-ready `2/50` | `experiment/mmlu/run_logs/mmlu_r188_promptedge_e5_generated_graph_audit_report.md` |
| MMLU projected contract-ready `50/50` | `experiment/mmlu/run_logs/mmlu_r189_promptedge_projection_audit_report.md` |
| MMLU random12 `11/12` vs `11/12` | `experiment/mmlu/run_logs/mmlu_r202_random12_diagnostic_report.md`, `experiment/mmlu/run_logs/mmlu_r204_claim_evidence_update_report.md` |

## Claims

| Candidate Paper Claim | Status | Evidence | Boundary |
|---|---|---|---|
| ARG-Designer baseline was reproduced under the same model setting | Supported | R001 AQuA sync20: `17/20`, `gpt-4o-2024-08-06` | This is a baseline reproduction, not our improvement |
| Objective-guided PromptNode multi-view can exceed ARG-Designer on AQuA tail34 | Supported, scope-limited | R065: `31/34` vs `28/34`, fix/harm `3/0`, clean `28/28` | Replay over multi-view traces; expensive; partial update2 compliance |
| Gain is not only noisy-label exploitation | Supported, scope-limited | R065 clean split: `28/28`, clean fix/harm `1/0` | Tail34 is only 34 tasks |
| First-class PromptNode/PromptEdge can be made executable before inference | Supported as engineering/mechanism | R181-R184 code path, R189 projected contract-ready `50/50` | Hybrid constrained decoder |
| Learned PN/PE graph policy already learns robust edge topology by itself | Not supported | R188 raw contract-ready only `2/50` | Needs projection or stronger topology loss |
| Projected PromptEdge improves MMLU transfer accuracy | Not supported | R202 random12: `11/12` vs `11/12`, fixes/harms `0/0` | Safety signal only |
| Current system is SCI-Q2 ready | Not yet supported | AQuA accuracy and MMLU graph mechanism are still separated | Needs ablations, cost analysis, and transfer/robustness evidence |

## Recommended Paper Position

The defensible paper direction is:

> PromptNode/PromptEdge graph augmentation can expose useful verification and routing evidence beyond ARG-Designer. On AQuA tail34, objective-guided multi-view PromptNode selection improves over ARG-Designer, while MMLU transfer experiments show that first-class PN/PE graph execution is structurally feasible but needs better learned activation and router-final training.

This is not yet a full submission claim. It is a coherent SCI-Q2 research direction if the next iteration closes the gap between AQuA accuracy gains and MMLU first-class graph mechanism.

## Forbidden Claims

- Do not claim broad multi-agent superiority.
- Do not claim MMLU transfer improvement.
- Do not claim fully learned edge-linking while projection is required.
- Do not claim R065 fully satisfies update2.
- Do not hide the multi-view cost.

## Next

R208 should define negative controls and ablations before any new API run.
