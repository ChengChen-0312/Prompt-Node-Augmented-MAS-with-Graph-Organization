# R317 Claim Matrix After Controls

**Claim boundary**: R317 updates R313 with R316 controls. It does not broaden claims: non-STEM remains no-harm only under warning-only lifecycle safety replay.

| Slice | Baseline | Proposed | Delta | Fix/Harm | Claim |
|---|---:|---:|---:|---:|---|
| `aqua_audit_clean` | `28/31` | `31/31` | `3` | `-` | positive_clean_improvement |
| `aqua_conservative_remove_114` | `28/30` | `30/30` | `2` | `-` | positive_under_boundary_label_removal |
| `mmlu_stem_main97` | `88/97` | `95/97` | `7` | `7/0` | positive_diagnostic_with_controls |
| `mmlu_nonstem_raw` | `37/40` | `34/40` | `-3` | `0/3` | negative_transfer_without_warning_only_gate |
| `mmlu_nonstem_safety_replay` | `37/40` | `37/40` | `0` | `0/0` | no_harm_boundary_only |
| `mmlu_nonstem_plain_requery` | `37/40` | `37/40` | `0` | `1/1` | cost_matched_plain_requery_ties_arg_but_not_beaten |
| `mmlu_nonstem_node_only_no_edge_text` | `37/40` | `35/40` | `-2` | `0/2` | remove_promptedge_text_harms_nonstem_safety |

## Paper Guidance

- Do not claim non-STEM improvement: plain requery ties ARG and raw PromptNode harms.
- Use non-STEM as a boundary/no-harm result after lifecycle safety replay.
- Use no-edge-text harm as evidence that PromptEdges are not just decorative text.
- Keep the positive claim on AQuA audit-clean and MMLU STEM until broader held-out validation is run.
