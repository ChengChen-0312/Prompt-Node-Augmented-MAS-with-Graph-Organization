# AQuA First200 Graph-Objective Training Export

**Claim boundary**: Label-free graph-objective export only. Rows are targets for graph candidate selection or graph-generator training and contain no gold answer, audit label, or correctness field.

- Source objective summary: `experiment/aqua/res_logs/aqua_first200_contract_graph_objective_summary.json`
- Training rows: `experiment/aqua/aqua_first200_graph_objective_training_rows.jsonl`
- Total tasks: `200`
- Variant rows: `800`
- Positive top-score tasks: `196`
- Top-score ties: `99`
- Margin-top tasks: `76` with margin >= `3`
- Outcome-field violations: `0`
- Training target counts: `low_margin_top=24, multi_view_tie=313, non_positive_top=1, non_preferred_graph=386, preferred_graph=76`
- Candidate method counts: `calibrated=200, candidate=200, conservative=200, router=200`

## How This Supports The Method

This export turns PromptNode contract evidence into a graph-organization target. Each row corresponds to one PromptNode graph variant for one task. The preferred target is assigned only when the label-free contract objective has a unique positive top score separated by the configured margin. Tied top variants remain multi-view targets rather than forced single-graph labels.

The rows intentionally exclude gold answers, clean/noisy audit labels, and correctness fields. They can be used to train or select graph structures before final answer aggregation, which is closer to the PromptNode-as-virtual-node design than post-hoc answer patching.
