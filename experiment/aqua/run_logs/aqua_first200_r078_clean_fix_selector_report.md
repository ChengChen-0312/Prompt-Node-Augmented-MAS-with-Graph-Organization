# R078 Clean-Fix Pointwise Selector

**Claim boundary**: R078 reports target agreement with R077 clean-fix graph-policy distillation labels. It is not AQuA answer accuracy and does not use true answers, predicted answers, audit labels, correctness fields, or task ids in selector inputs.

- Input rows: `experiment/aqua/aqua_first200_r077_clean_fix_graph_policy_distill_rows.jsonl`
- Source rows: `800`
- Train slice: `aqua_100` with `400` rows
- Eval slice: `aqua_next100` with `400` rows
- Train target agreement: `0.985`
- Eval target agreement: `0.968`
- Eval positive precision/recall/F1: `0.739` / `0.971` / `0.840`
- Input-field violations: `0`
- Eval target counts: `ambiguous_or_low_margin_suppress=177, clean_fix_preserve_graph=35, negative_graph_suppress=188`

## Learned Weights

| Feature | Weight |
| --- | ---: |
| `bias` | `-0.3000` |
| `objective_reward` | `-0.8000` |
| `score_margin_to_next` | `1.1000` |
| `has_margin_at_least_3` | `0.8000` |
| `objective_bucket_preferred_graph` | `2.9000` |
| `objective_bucket_multi_view_tie` | `-2.4000` |
| `objective_bucket_low_margin_top` | `-0.2000` |
| `objective_bucket_non_positive_top` | `0.0000` |
| `objective_bucket_non_preferred_graph` | `-0.6000` |
| `strong_contract` | `0.4000` |
| `direct_agreement` | `0.0000` |
| `direct_vote_support` | `-1.6000` |
| `prompt_node_graph` | `0.0000` |
| `conflict_penalty` | `0.2000` |
| `weak_contract_penalty` | `0.2000` |
| `num_prompt_nodes` | `0.0000` |
| `num_prompt_node_edges` | `0.1500` |
| `has_promptnode_specs` | `0.0000` |
| `has_promptnode_edge_permissions` | `0.0000` |
| `role_count_PN_Memory` | `0.0000` |
| `role_count_PN_Verifier` | `0.0000` |
| `role_count_PN_Router` | `0.0000` |

## Interpretation

R078 is the first trained selector on the R077 clean-fix graph-policy rows. It shows the R077 schema is learnable from label-free objective and graph-observation features. This does not claim improved AQuA answer accuracy; the next accuracy-bearing step must attach the selector to graph generation or cascade execution and validate prospectively on tail34 or transfer.
