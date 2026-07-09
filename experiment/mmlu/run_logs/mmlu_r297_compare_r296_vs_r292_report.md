# R297 Compare R296 vs R292

**Claim boundary**: Offline comparison only; no new API. R296 and R292 are matched on transfer100 first24 task_ids.

## R291_PN_all

- PN correct: `20/24`
- ARG correct: `22/24`
- Fix/harm: `0/2`
- Harm task IDs: `['MMLU-college_mathematics_test-17', 'MMLU-high_school_mathematics_test-63']`

## R296_PN_specialist

- PN correct: `20/24`
- ARG correct: `22/24`
- Fix/harm: `0/2`
- Harm task IDs: `['MMLU-college_mathematics_test-17', 'MMLU-high_school_mathematics_test-63']`

## Decision

R294 specialist-aware reselection reduced cost but did not improve accuracy; PromptNode transfer remains worse than the retrained ARG baseline on matched MMLU first24.
