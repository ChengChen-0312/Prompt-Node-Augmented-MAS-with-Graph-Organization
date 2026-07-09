# R203 Random12 Diagnostic Analysis

**Claim boundary**: diagnostic analysis only. The 12-task slice is small and cannot serve as a final paper result.

## Result

- Tasks: `12`
- R162 baseline: `11/12`
- Projected PromptEdge: `11/12`
- Accuracy delta: `0`
- Fixes: `0`
- Harms: `0`
- Raw contract-ready graphs: `0/12`
- Projected contract-ready graphs: `12/12`
- Cost: `$0.697925`
- Cost per task: about `$0.05816`

## Interpretation

The random slice shows no harm, but also no improvement. The only baseline-wrong task in this slice, `MMLU-elementary_mathematics_test-222`, remained wrong.

Graph projection is structurally necessary: raw generated graphs were `0/12` contract-ready, projected graphs were `12/12`.

## Recommendation

Do not scale MMLU API yet. Update the claim matrix and decide at R205 whether to redesign the method or run a larger random protocol.
