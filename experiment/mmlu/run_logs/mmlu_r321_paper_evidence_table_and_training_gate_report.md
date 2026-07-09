# R321 Paper Evidence Table And Training Gate

**Claim boundary**: R321 translates the current results into paper-facing tables and freezes the next training gate. It permits a selector-training preflight, but does not permit training execution yet.

## Main Results

| Slice | ARG baseline | PromptNode | Delta | Fix/Harm | Paper Claim |
|---|---:|---:|---:|---:|---|
| `AQuA_audit_clean_tail31` | `28/31` | `31/31` | `3` | `-` | positive_clean_improvement |
| `AQuA_conservative_remove_114_tail30` | `28/30` | `30/30` | `2` | `-` | positive_under_boundary_label_removal |
| `MMLU_STEM_main97` | `88/97` | `95/97` | `7` | `7/0` | positive_with_completed_controls |
| `MMLU_nonSTEM40_safety_replay` | `37/40` | `37/40` | `0` | `0/0` | no_harm_boundary_only |
| `MMLU_nonSTEM40_raw_warning_override` | `37/40` | `34/40` | `-3` | `0/3` | negative_transfer_limitation |

## Training Gate

- Preflight authorized: `True`
- Execute training authorized: `False`
- Allowed target: Learn a graph-policy selector for PromptNode type, PromptEdge read/write/forward permission, and lifecycle action; do not train a direct answer predictor.

## Forbidden Paper Claims

- Do not claim universal improvement across all multi-choice tasks.
- Do not present warning-only non-STEM nodes as answer-improving nodes.
- Do not hide the raw non-STEM negative transfer row.

- Next required run: `R322_selector_training_preflight`
