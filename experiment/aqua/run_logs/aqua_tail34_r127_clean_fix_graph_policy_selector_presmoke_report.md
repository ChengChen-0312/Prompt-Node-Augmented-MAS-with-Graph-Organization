# R127 Clean-Fix Graph-Policy Selector Pre-Smoke

**Claim boundary**: pre-smoke selector plan only; no API, accuracy, cost, or prospective result

- Pre-smoke only: `True`
- No API run: `True`
- Learned action rule: `diff_and_top_score_ge_3_or_split`
- Action rule train source: `experiment/aqua/aqua_first200_r112_objective_safety_feature_targets.jsonl`
- Uses tail34 training source: `False`
- Uses tail34 outputs for rank selection: `False`
- Switch tasks: `['task_108', 'task_250']`
- Fallback tasks: `['task_8', 'task_188']`
- Selected template ranks: `{'task_108': 5, 'task_250': 5}`
- Switches with update2 metadata: `2`
- Switches with high-fanin Memory bridge: `2`
- Selector input field violations: `0`
- Broad API before smoke: `False`
- Same-four-task smoke allowed next: `True`

| Task | Planned action | Proxy action | Template rank | Memory writes | Update2 metadata | Rank reason |
| --- | --- | --- | ---: | ---: | --- | --- |
| `task_8` | `fallback_to_arg` | `fallback_to_arg` | `None` | `0` | `False` | `proxy_rule_fallback` |
| `task_108` | `switch_to_promptnode_template` | `switch_to_objective` | `5` | `3` | `True` | `max_memory_write_fanin_then_edge_count` |
| `task_188` | `fallback_to_arg` | `fallback_to_arg` | `None` | `0` | `False` | `proxy_rule_fallback` |
| `task_250` | `switch_to_promptnode_template` | `switch_to_objective` | `5` | `3` | `True` | `max_memory_write_fanin_then_edge_count` |

## Interpretation

R127 joins the R113 first200-trained action rule with R083 explicit PromptNode template candidates. When the action rule switches, the rank policy selects the template with the largest write fan-in into PN_Memory, then the largest graph edge count. This is a structural PromptNode graph-policy choice, not a tail34 answer-output lookup.

The artifact is still pre-smoke only. It permits the same four-task API smoke, but not broad tail34 or transfer evaluation.
