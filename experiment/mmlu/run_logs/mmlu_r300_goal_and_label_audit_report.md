# R300 MMLU Goal And Label Audit

**Claim boundary**: Goal audit plus label audit only. Clean overrides come from MMLU-Redux 2.0 or external answer explanations; no PromptNode accuracy claim is made by this run.

- ARG official: `88/100`
- ARG audit-clean: `90/100`
- ARG first24 official/audit-clean: `22/24` / `23/24`
- Wrong-groundtruth overrides: `{'MMLU-high_school_physics_test-67': 'C', 'MMLU-college_chemistry_test-62': 'A'}`
- R299 lesson: LLM self-confidence is not a safe no-harm gate; switch authority must be conservative and learnable.

## Audited Wrong Items

| Task | Official | ARG | Clean | Verdict | Source |
| --- | ---: | ---: | ---: | --- | --- |
| `MMLU-high_school_statistics_test-32` | `D` | `B` | `D` | label_correct_after_option_compression | external_answer_explanation |
| `MMLU-high_school_physics_test-67` | `A` | `C` | `C` | dataset_label_wrong_groundtruth | mmlu_redux_2_0_and_external_answer_explanation |
| `MMLU-abstract_algebra_test-53` | `C` | `A` | `C` | label_kept_expert_checked_no_override | mmlu_redux_2_0 |
| `MMLU-college_mathematics_test-26` | `D` | `C` | `D` | label_correct | mmlu_redux_2_0_expert |
| `MMLU-high_school_statistics_test-127` | `D` | `C` | `D` | label_correct | external_answer_explanation |
| `MMLU-machine_learning_test-81` | `C` | `A` | `C` | label_correct | mmlu_redux_2_0_and_cmu_exam_source |
| `MMLU-conceptual_physics_test-41` | `D` | `B` | `D` | label_correct_by_domain_evidence | open_textbook_concept_evidence |
| `MMLU-college_chemistry_test-62` | `B` | `A` | `A` | dataset_label_wrong_groundtruth | mmlu_redux_2_0 |
| `MMLU-college_mathematics_test-67` | `D` | `B` | `D` | label_correct | mmlu_redux_2_0_expert |
| `MMLU-college_chemistry_test-97` | `C` | `B` | `C` | label_correct | mmlu_redux_2_0_and_nmr_constant |
| `MMLU-elementary_mathematics_test-222` | `D` | `A` | `D` | label_correct | state_practice_test_question |
| `MMLU-college_mathematics_test-92` | `C` | `B` | `C` | label_correct | mmlu_redux_2_0_expert |

## Next

R301 should only allow a virtual node to override ARG when a label-free, dataset-agnostic trigger is present. The immediate safe target is the census-versus-inference statistics item; noisy physics and chemistry labels must not be optimized as errors.
