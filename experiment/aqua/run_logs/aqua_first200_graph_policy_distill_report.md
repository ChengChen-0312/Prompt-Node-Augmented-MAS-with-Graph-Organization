# AQuA First200 PromptNode Graph-Policy Distillation Export

**Claim boundary**: Node/edge graph-policy supervision only. These rows make PromptNode virtual nodes part of the graph-generation target before execution; they do not report answer accuracy.

- Input graph-objective rows: `experiment/aqua/aqua_first200_graph_objective_training_rows.jsonl`
- Output policy rows: `experiment/aqua/aqua_first200_graph_policy_distill_rows.jsonl`
- Source training rows: `800`
- Policy rows: `800`
- Positive policy rows: `76`
- Positive PromptNode policy rows: `76`
- Positive PromptNode spec rows: `76`
- Positive PromptNode edge-permission rows: `76`
- Missing graph rows: `0`
- Outcome-field violations: `0`
- Target counts: `low_margin_top=24, multi_view_tie=313, non_positive_top=1, non_preferred_graph=386, preferred_graph=76`
- Positive PromptNode role counts: `PN_Memory=76, PN_Router=76, PN_Verifier=76`
- Unique positive graph signatures: `17`

## Why This Matters

R052 converts the label-free graph objective into explicit node and edge supervision. Each row contains the task-visible input and a graph-policy target with roles, edges, PromptNode role counts, PromptNode edge role pairs, graph signature, candidate label, and objective reward. The export deliberately removes gold answers, predicted answers, router options, direct-majority options, audit labels, and correctness fields.

This is closer to the intended PromptNode design than R051's shallow graph-ranker replay: the virtual node is now a trainable graph-organization target before execution. It is still not an accuracy result; the next step is to train the ARG-Designer node/edge generator on these targets and validate on tail34 or transfer data.
