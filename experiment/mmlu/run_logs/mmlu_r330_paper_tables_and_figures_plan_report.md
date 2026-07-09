# R330 Paper Tables And Figures Plan

**Claim boundary**: R330 plans paper artifacts from existing evidence. It does not add new claims or mark the paper submission-ready.

## Tables

| ID | Placement | Source | Purpose |
|---|---|---|---|
| `main_results` | `main` | `experiment/mmlu/res_logs/mmlu_r321_paper_evidence_table_and_training_gate_summary.json` | Show AQuA audit-clean and MMLU STEM gains, plus non-STEM no-harm boundary. |
| `ablation_controls` | `main` | `experiment/mmlu/res_logs/mmlu_r319_ablation_table_update_summary.json` | Answer reviewer questions about SafetyGate, lifecycle, PromptEdge text, symbolic/nonmath families, and cost-matched requery. |
| `selector_training_gate` | `main_or_appendix` | `experiment/mmlu/res_logs/mmlu_r328_selector_policy_claim_update_summary.json` | Support train-time graph-policy feasibility without overclaiming external accuracy. |
| `case_studies` | `main_and_appendix` | `experiment/mmlu/res_logs/mmlu_r329_case_study_extraction_summary.json` | Explain verifier repair, MemoryBridge pruning, PromptEdge false-forward block, and lifecycle cost control. |
| `label_audit_appendix` | `appendix` | `experiment/mmlu/res_logs/mmlu_r313_claim_matrix_summary.json` | Document noisy-label exclusions for AQuA and MMLU without hiding the official-score boundary. |

## Figures

| ID | Placement | Source | Purpose |
|---|---|---|---|
| `promptnode_augmented_graph_workflow` | `main` | `/Users/chencheng/Downloads/论文/update2.docx plus R329 cases` | Show PromptNode insertion, read/write/forward edges, lifecycle update/compress/prune/merge/upgrade, and final aggregation. |
| `selector_training_pipeline` | `main` | `R322-R328` | Show manifest construction, hard-negative augmentation, transparent selector, and claim gate. |
| `accuracy_cost_tradeoff` | `main_or_appendix` | `R309/R315/R319` | Show why always-forward/no-lifecycle is not a good substitute for routed PromptNodes. |
| `case_study_graphs` | `appendix` | `R329` | Visualize verifier repair, MemoryBridge prune, and PromptEdge block. |

## Missing Before SCI-Q2 Submission

- prospective selector evaluation
- larger held-out transfer or a second non-AQuA dataset with positive/no-harm result
- complete related-work synthesis
- paper claim audit against raw logs
- citation audit

- Next required run: `R331_paper_outline_scaffold`
