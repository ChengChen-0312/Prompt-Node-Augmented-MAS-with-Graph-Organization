# R329 Case Study Extraction

**Claim boundary**: R329 extracts paper-facing mechanism cases from existing logs. The cases explain the method but do not change quantitative claims.

| Mechanism | Source | Outcome | Paper Use |
|---|---|---|---|
| `verifier_repair` | `R306` | `fix` | Main case study: semantic verifier forwards a concrete answer only when evidence count and confidence are high. |
| `memory_bridge_prune` | `R306` | `unresolved_signal_pruned` | Boundary case: MemoryBridge identifies missing/truncated context, writes and compresses the signal, then prunes answer override. |
| `promptedge_false_forward_block` | `R327` | `hard_negative_blocked` | Safety case: answer-bearing no-edge candidate is blocked after hard-negative augmentation. |
| `lifecycle_cost_control` | `R309` | `accuracy_ties_but_cost_worse_without_prune` | Efficiency case: lifecycle pruning preserves accuracy while avoiding always-forward cost. |

- Next required run: `R330_paper_tables_and_figures_plan`
