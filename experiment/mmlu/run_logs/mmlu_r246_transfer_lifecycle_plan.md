# R246 Transfer And Lifecycle Evidence Plan

**Claim boundary**: planning only. No API, no new accuracy claim, and no SCI-Q2 readiness claim.

## Selected Artifacts

| Evidence need | Artifact | Why it matters |
|---|---|---|
| PromptNode lifecycle | `experiment/aqua/aqua_tail34_r081_promptnode_metadata_audit_rows.jsonl` | R081 shows positive accuracy and explicit PromptNode metadata are still separated |
| MMLU transfer | `experiment/mmlu/run_logs/mmlu_r162_transfer_eval_results.jsonl` | Same-model ARG transfer baseline is `88/100`, but PN/PE transfer gain is unsupported |
| AQuA abstention policy | `experiment/mmlu/run_logs/mmlu_r241_abstention_feature_table.jsonl` and R242/R243/R244 summaries | Provides the current train/frozen fitted-policy and control evidence |

## Plan

1. R247: annotate PromptNode lifecycle states: `update`, `compress`, `prune`, `merge`, and `upgrade`.
2. R248: prepare a MMLU transfer feature table or analog from existing ARG transfer and PN/PE contract artifacts.
3. R249: update the claim matrix with AQuA fitted-policy, control, lifecycle, and transfer evidence.
4. R250: goal audit before any API or paper-result claim.

## Claim Boundaries

- Lifecycle annotations can support mechanism and case-study discussion, not accuracy.
- MMLU transfer improvement remains unsupported until PN/PE transfer is evaluated.
- PromptEdge text-specific gain remains unsupported because R243 node-only equals proposed.
