# R197 Baseline-Wrong Diagnostic Analysis

**Claim boundary**: mechanism analysis only. The slice is conditioned on R162 baseline errors and cannot be used as an unbiased accuracy claim.

## Result

- Tasks: `4`
- R162 baseline: `0/4`
- Projected PromptEdge: `2/4`
- Fixes: `2`
- Harms: `0`
- Raw contract-ready graphs: `0/4`
- Projected contract-ready graphs: `4/4`
- Cost: `$0.389555`

## Fixed

- `MMLU-abstract_algebra_test-53`: baseline `A`, projected `C`, true `C`
- `MMLU-college_mathematics_test-26`: baseline `C`, projected `D`, true `D`

## Still Failed

- `MMLU-high_school_statistics_test-32`: baseline `B`, projected `B`, true `D`
- `MMLU-high_school_physics_test-67`: baseline `C`, projected `C`, true `A`

## Interpretation

This is a positive mechanism signal: projected PromptEdge can change wrong ARG outcomes on some hard rows. It is not an unbiased accuracy result because rows were selected from known baseline failures.

The next scientifically valid step is a small random transfer protocol or full held-out evaluation after R200 audit.
