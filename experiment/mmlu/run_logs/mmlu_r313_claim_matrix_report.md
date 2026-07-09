# R313 Claim Matrix

**Claim boundary**: R313 consolidates evidence only. It does not start training and does not convert diagnostic results into a final SCI-Q2 claim without ablations and prospective held-out validation.

## Evidence

| Slice | Baseline | Proposed | Delta | Fix/Harm | Claim |
|---|---:|---:|---:|---:|---|
| `aqua_audit_clean` | `28/31` | `31/31` | `3` | `-` | positive_clean_improvement |
| `aqua_conservative_remove_114` | `28/30` | `30/30` | `2` | `-` | positive_under_boundary_label_removal |
| `mmlu_stem_main97` | `88/97` | `95/97` | `7` | `7/0` | positive_diagnostic_with_controls |
| `mmlu_nonstem_raw` | `37/40` | `34/40` | `-3` | `0/3` | negative_transfer_without_warning_only_gate |
| `mmlu_nonstem_safety_replay` | `37/40` | `37/40` | `0` | `0/0` | no_harm_boundary_only |

## Claim Permissions

- `aqua_clean_improvement_allowed`: `True`
- `mmlu_stem_improvement_allowed`: `True`
- `mmlu_nonstem_no_harm_allowed`: `True`
- `mmlu_nonstem_improvement_allowed`: `False`
- `broad_general_promptnode_claim_allowed`: `False`
- `training_authorized`: `False`
- `sci_q2_ready`: `False`

## Required Ablations

- `remove_safety_gate`
- `remove_lifecycle_prune`
- `remove_promptedge_text`
- `remove_nonmath_promptnodes`
- `remove_symbolic_verifier_family`
- `answer_bearing_vs_warning_only_promptnodes`
- `cost_matched_plain_requery`
