# R319 Updated Ablation Table

**Claim boundary**: R319 updates the ablation ledger only. It does not train and does not broaden claims.

| Ablation | Status | Slice | Full | Observed | Fix/Harm | Interpretation |
|---|---|---|---:|---:|---:|---|
| `remove_nonmath_promptnodes` | `completed` | `MMLU_STEM_main97` | `95/97` | `93/97` | `-` | nonmath_nodes_add_two_clean_repairs |
| `remove_safety_gate` | `completed` | `MMLU_STEM_main97` | `95/97` | `83/97` | `2/12` | safety_gate_prevents_large_harm |
| `remove_lifecycle_prune` | `completed` | `MMLU_STEM_main97` | `95/97` | `95/97` | `2/0` | accuracy_ties_but_cost_worse |
| `random_forward_same_budget` | `completed` | `MMLU_STEM_main97` | `95/97` | `92/97` | `0/1` | not_explained_by_random_switch_budget |
| `random_promptnode_type` | `completed` | `MMLU_STEM_main97` | `95/97` | `93/97` | `0/0` | node_identity_matters_for_gate |
| `always_forward_candidate_nodes` | `completed` | `MMLU_STEM_main97` | `95/97` | `95/97` | `2/0` | accuracy_ties_but_cost_worse |
| `answer_bearing_vs_warning_only_promptnodes` | `completed` | `MMLU_nonSTEM40` | `37/40` | `37/40` | `0/0` | warning_nodes_are_lifecycle_nodes_not_answer_nodes |
| `remove_promptedge_text` | `completed` | `MMLU_nonSTEM40` | `37/40` | `35/40` | `0/2` | removing_promptedge_text_harms_nonstem_safety |
| `remove_symbolic_verifier_family` | `completed` | `MMLU_STEM_main97` | `95/97` | `90/97` | `2/0` | symbolic_family_adds_five_stem_repairs |
| `cost_matched_plain_requery` | `completed` | `MMLU_nonSTEM40` | `37/40` | `37/40` | `1/1` | plain_requery_ties_arg_but_has_fix_and_harm |

- Priority pending: `[]`
