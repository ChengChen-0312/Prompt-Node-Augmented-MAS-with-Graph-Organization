# R420 Paper Asset Table Refresh

**Claim boundary**: R420 indexes paper assets for drafting. It does not authorize claims or mark the paper SCI-Q2 ready.

| Asset | Section | Status | Source | Note |
|---|---|---|---|---|
| `main_result_table` | Results | `ready_with_claim_boundaries` | `experiment/mmlu/res_logs/mmlu_r321_paper_evidence_table_and_training_gate_summary.json` | Use together with R415 claim update; broad claims remain disabled. |
| `claim_matrix` | Experimental Setup / Results | `ready_provisional` | `experiment/mmlu/res_logs/mmlu_r415_update_claim_matrix_after_nonmath_positive_summary.json` | Includes C6 narrow DefinitionChallenge positive result. |
| `cost_table` | Results / Cost Analysis | `incomplete_for_submission` | `experiment/mmlu/res_logs/mmlu_r416_cost_normalized_claim_table_and_goal_audit_summary.json` | MMLU STEM cost and external integrity audit are missing. |
| `case_study_pack` | Case Studies | `ready_with_caveats` | `experiment/mmlu/res_logs/mmlu_r417_case_study_evidence_pack_summary.json` | 3 reproducible case-study entries. |
| `lifecycle_trace` | Method / Case Studies | `ready_for_visualization` | `experiment/mmlu/res_logs/mmlu_r419_lifecycle_trace_replay_summary.json` | 121 lifecycle events from R413 replay. |
| `paper_plan` | All sections | `updated` | `PAPER_PLAN.md` | Contains R402 and R415 claim-boundary updates. |

## Missing Assets

- `submission_complete_cost_table`
- `external_experiment_integrity_audit`

- Next required run: `R421_submission_readiness_goal_audit`
