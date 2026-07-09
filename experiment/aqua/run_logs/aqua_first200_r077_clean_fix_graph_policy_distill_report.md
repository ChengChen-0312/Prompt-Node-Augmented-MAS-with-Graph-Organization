# R077 Clean-Fix-Preserving Graph-Policy Distillation

**Claim boundary**: R077 is a distillation-data artifact, not an answer-accuracy result. It uses R076 as schema guidance and first200 label-free graph-policy rows as trainable examples.

- Input rows: `experiment/aqua/aqua_first200_graph_policy_distill_rows.jsonl`
- Output rows: `experiment/aqua/aqua_first200_r077_clean_fix_graph_policy_distill_rows.jsonl`
- Source policy rows: `800`
- Distillation rows: `800`
- Clean-fix-preserve graph rows: `76`
- Ambiguous/low-margin suppress rows: `338`
- Negative suppress rows: `386`
- Clean-fix PromptNode spec rows: `76`
- Clean-fix edge-permission rows: `76`
- Selector-input violations: `0`
- Target-field violations: `0`
- Target class counts: `ambiguous_or_low_margin_suppress=338, clean_fix_preserve_graph=76, negative_graph_suppress=386`
- Teacher policy counts: `prefer_baseline_or_wait_for_more_evidence=386, preserve_high_margin_promptnode_graph=76, suppress_unstable_or_low_margin_switch=338`

## Interpretation

R077 converts the R076 clean-fix-preserving boundary into trainable graph-policy rows without using tail34 task labels as training examples. Tail34 evidence is used only to define the schema: preserve high-margin PromptNode graph channels, suppress ambiguous/low-margin switches, and do not treat noisy-only gains as clean positives.

The positive rows still carry update2 PromptNode identities, permissions, budgets, lifecycle actions, and edge permissions through the nested graph-policy target. The selector input is deliberately narrower: task text, candidate method, label-free objective components, and graph observations only.
