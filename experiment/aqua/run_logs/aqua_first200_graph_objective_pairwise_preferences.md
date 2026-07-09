# AQuA First200 Graph-Objective Pairwise Preferences

**Claim boundary**: Label-free pairwise graph preferences only. These pairs are for training or selecting PromptNode graph organization before final aggregation and do not provide an accuracy claim.

- Input graph-objective rows: `experiment/aqua/aqua_first200_graph_objective_training_rows.jsonl`
- Output pairwise preferences: `experiment/aqua/aqua_first200_graph_objective_pairwise_preferences.jsonl`
- Source rows: `800`
- Total tasks: `200`
- Tasks with preferences: `76`
- Skipped tasks without preferred graph: `124`
- Pairwise rows: `228`
- Outcome-field violations: `0`
- Method-pair counts: `candidate>calibrated=72, candidate>conservative=72, candidate>router=72, conservative>calibrated=3, conservative>candidate=3, conservative>router=3, router>calibrated=1, router>candidate=1, router>conservative=1`

## How This Supports Training

Each pair compares graph variants for the same task. The positive side is the unique margin-separated `preferred_graph` from the label-free contract objective; the negative side is another graph variant for that task. Tasks with only ties, low-margin tops, or non-positive tops are skipped instead of being forced into brittle supervision.

These pairs can feed a pairwise ranking loss for a graph generator or a prospective graph selector. They are closer to the intended PromptNode-as-virtual-node design than answer-level fallback rules, because they supervise graph organization before final answer aggregation.
