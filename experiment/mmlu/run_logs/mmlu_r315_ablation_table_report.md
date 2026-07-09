# R315 Ablation Table

**Claim boundary**: R315 consolidates completed ablations and marks required pending ablations. It does not train, does not call APIs, and does not make new accuracy claims.

| Ablation | Status | Slice | Full | Observed | Interpretation | Priority |
|---|---|---|---:|---:|---|---:|
| `remove_nonmath_promptnodes` | `completed` | `MMLU_STEM_main97` | `95/97` | `93/97` | nonmath_nodes_add_two_clean_repairs | `1` |
| `remove_safety_gate` | `completed` | `MMLU_STEM_main97` | `95/97` | `83/97` | safety_gate_prevents_large_harm | `1` |
| `remove_lifecycle_prune` | `completed` | `MMLU_STEM_main97` | `95/97` | `95/97` | accuracy_ties_but_cost_worse | `1` |
| `random_forward_same_budget` | `completed` | `MMLU_STEM_main97` | `95/97` | `92/97` | not_explained_by_random_switch_budget | `1` |
| `random_promptnode_type` | `completed` | `MMLU_STEM_main97` | `95/97` | `93/97` | node_identity_matters_for_gate | `2` |
| `always_forward_candidate_nodes` | `completed` | `MMLU_STEM_main97` | `95/97` | `95/97` | accuracy_ties_but_cost_worse | `2` |
| `answer_bearing_vs_warning_only_promptnodes` | `completed` | `MMLU_nonSTEM40` | `37/40` | `37/40` | warning_nodes_are_lifecycle_nodes_not_answer_nodes | `1` |
| `remove_promptedge_text` | `pending` | `MMLU_STEM_main97_and_nonSTEM40` | `pending` | `pending` | not_measured_yet | `1` |
| `remove_symbolic_verifier_family` | `pending` | `MMLU_STEM_main97` | `pending` | `pending` | not_measured_yet | `1` |
| `cost_matched_plain_requery` | `pending` | `AQuA_tail34_MMLU_STEM_main97_nonSTEM40` | `pending` | `pending` | not_measured_yet | `1` |

## Priority Pending

- `remove_promptedge_text`
- `remove_symbolic_verifier_family`
- `cost_matched_plain_requery`
