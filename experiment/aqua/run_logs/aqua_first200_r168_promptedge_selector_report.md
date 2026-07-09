# R168 PromptEdge Selector

**Claim boundary**: R168 trains a lightweight selector over R166 PromptNode/PromptEdge targets. It reports target agreement only, not AQuA answer accuracy.

- Source rows: `800`
- Train slice: `aqua_100` with `400` rows
- Eval slice: `aqua_next100` with `400` rows
- Train target agreement: `1.000`
- Eval target agreement: `0.995`
- Eval positive precision/recall/F1: `0.971` / `0.971` / `0.971`
- Input-field violations: `0`
- Eval target counts: `preserve_safe_insert=33, suppress_or_fallback=365, switch_critical_insert=2`

## Learned Weights

| Feature | Weight |
| --- | ---: |
| `bias` | `-0.4000` |
| `score_margin_to_next` | `0.5500` |
| `has_margin_at_least_3` | `0.9000` |
| `objective_bucket_preferred_graph` | `2.4500` |
| `objective_bucket_multi_view_tie` | `-2.1500` |
| `objective_bucket_low_margin_top` | `-0.2500` |
| `objective_bucket_non_positive_top` | `0.0000` |
| `objective_bucket_non_preferred_graph` | `-0.4500` |
| `objective_prediction_differs_from_baseline` | `-0.1500` |
| `baseline_direct_votes_split` | `0.0000` |
| `objective_top_score` | `-0.5500` |
| `num_prompt_nodes` | `0.1500` |
| `num_prompt_node_edges` | `-0.2500` |
| `has_promptnode_specs` | `0.0500` |
| `has_promptnode_edge_permissions` | `0.0500` |
| `role_count_PN_Memory` | `0.0500` |
| `role_count_PN_Verifier` | `0.0500` |
| `role_count_PN_Router` | `0.0500` |

## Interpretation

R168 provides the fallback boundary that R167 needs before broad API evaluation. The selector is trained only on label-free graph/objective features and R166 positive/fallback targets. It should be used as a deployment gate, not as an answer selector.
