# R453 Appendix Noise Audit Pack

**Claim boundary**: R453 writes an appendix that documents existing label-audit and audit-clean policies. It does not edit benchmark data, add new exclusions, or authorize paper claims.

- Appendix TeX: `paper/appendices/label_audit.tex`
- Main TeX updated: `False`
- Silent benchmark rewrite: `False`

## AQuA Items

- `task_59`: `excluded_from_audit_clean` / `appendix_only`
- `task_139`: `excluded_from_audit_clean` / `appendix_only`
- `task_228`: `excluded_from_audit_clean` / `appendix_only`
- `task_114`: `sensitivity_boundary` / `sensitivity_only`

## MMLU Items

- `MMLU-college_chemistry_test-62`: `dataset_label_wrong_groundtruth` / `excluded_from_training_distillation_and_main97`
- `MMLU-high_school_physics_test-67`: `dataset_label_wrong_groundtruth` / `excluded_from_training_distillation_and_main97`
- `MMLU-high_school_statistics_test-32`: `label_correct_after_option_compression` / `excluded_from_training_distillation_and_main97`

- Paper claim authorized: `False`
- SCI-Q2 ready: `False`
- Next required run: `R454_reproducibility_artifact_index`
