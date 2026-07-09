# AQuA First200 Pairwise Graph Preference Ranker

**Claim boundary**: Offline graph-ranker fit to label-free PromptNode graph-objective pairwise preferences. Accuracy here is preference agreement with the objective, not task-answer accuracy.

- Source pairs: `228`
- Train slice: `aqua_100` with `123` pairs
- Eval slice: `aqua_next100` with `105` pairs
- Train preference agreement: `1.000`
- Eval preference agreement: `0.990`
- Outcome-field violations: `0`

## Learned Feature Weights

| Feature | Weight |
| --- | ---: |
| `strong_contract` | `0.4000` |
| `direct_agreement` | `0.3000` |
| `direct_vote_support` | `0.0000` |
| `prompt_node_graph` | `0.0000` |
| `conflict_penalty` | `0.0000` |
| `weak_contract_penalty` | `0.2000` |
| `strong_router_contract_count` | `0.1000` |
| `router_matches_direct_majority` | `0.1000` |
| `has_prompt_node_graph` | `0.0000` |

## Interpretation

This ranker is a proof-of-interface for training PromptNode graph selection before final answer aggregation. It learns from pairwise graph preferences derived from contract evidence, not from gold answers or clean/noisy labels. The reported agreement is only agreement with the label-free graph objective; it is not AQuA answer accuracy.
