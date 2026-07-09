# R303 MMLU Audit-Excluded Protocol

**Claim boundary**: Protocol freeze only. The three audited tasks are excluded from future training/distillation and main-result aggregation; they remain available for appendix sensitivity analysis.

- Full ARG official/audit-clean: `88/100` / `90/100`
- Main ARG official/audit-clean: `88/97` / `88/97`
- Appendix records: `3`

## Excluded Tasks

| Task | Reason |
| --- | --- |
| `MMLU-college_chemistry_test-62` | MMLU-Redux 2.0 marks wrong_groundtruth; keep in appendix sensitivity analysis only. |
| `MMLU-high_school_physics_test-67` | MMLU-Redux 2.0 marks wrong_groundtruth; keep in appendix sensitivity analysis only. |
| `MMLU-high_school_statistics_test-32` | Known ARG failure already used for R301/R302 gate discovery; exclude from further training/distillation to avoid tuning to a single audited item. |

## Policy

The main MMLU transfer result should be computed on the remaining 97 tasks. The excluded tasks should be discussed in an appendix label-audit section, mirroring the AQuA noisy-item treatment.
