# R198 Random Slice Protocol

**Claim boundary**: protocol only. No API evaluation and no accuracy claim.

## Selection

- Seed: `20260709`
- Sample size: `12`
- Population: MMLU transfer100 excluding R192 first4 and R196 diagnostic tasks
- Answer-based selection: `false`

## Selected Tasks

- `MMLU-college_computer_science_test-53`
- `MMLU-conceptual_physics_test-103`
- `MMLU-elementary_mathematics_test-222`
- `MMLU-college_chemistry_test-64`
- `MMLU-high_school_physics_test-72`
- `MMLU-machine_learning_test-77`
- `MMLU-electrical_engineering_test-44`
- `MMLU-astronomy_test-109`
- `MMLU-elementary_mathematics_test-102`
- `MMLU-conceptual_physics_test-108`
- `MMLU-elementary_mathematics_test-221`
- `MMLU-high_school_chemistry_test-137`

After selection, R162 baseline is `11/12` on this slice. That means the slice mostly estimates harm-rate, with only one possible fix.

## Estimated Cost

Using R192/R196 averages:

- Mean cost per task: about `$0.09883`
- Estimated 12-task cost: about `$1.186`

## Success Criteria

- No more than 1 harm among the 11 baseline-correct tasks.
- Fix the one baseline-wrong task or show no harm with clear graph/cost evidence.
- Report raw vs projected graph contract readiness for every task.
- Do not treat this as the final paper result without a later protocol audit.
