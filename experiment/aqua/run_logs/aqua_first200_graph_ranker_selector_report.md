# AQuA First200 Graph-Ranker-Guided Selector Replay

**Claim boundary**: Ranker-guided selector replay over existing first200 traces. The selection features exclude gold answers, audit labels, correctness fields, predicted options, router options, and objective_score. true_answer is used only after selection for post-hoc answer-accuracy accounting.

- Selector records: `experiment/aqua/aqua_first200_graph_ranker_selector_results.jsonl`
- Overall selector accuracy: `166/200`
- ARG baseline accuracy: `165/200`
- Delta vs ARG: `+1`
- Fix/Harm vs ARG: `2/1`
- Switches: `5`
- Outcome-field violations in selector features: `0`

## Slice Summary

| Slice | Selector | ARG baseline | Delta | Fix/Harm | Switches |
| --- | ---: | ---: | ---: | ---: | ---: |
| `aqua_100` | `83/100` | `83/100` | `+0` | `1/1` | `3` |
| `aqua_next100` | `83/100` | `82/100` | `+1` | `1/0` | `2` |

## Interpretation

This replay turns the R050 pairwise graph preference ranker into a prospective selector over already generated PromptNode graph variants. It is closer to the user's intended virtual-node setup than answer-level patching because the learned score ranks graph organizations before final answer aggregation.

The result is still an offline replay on first200 traces, not a new same-model API validation. It should be used as an ablation and bridge toward training-time graph selection; tail34 and transfer validation remain blocked until the same-model quota issue is resolved.
