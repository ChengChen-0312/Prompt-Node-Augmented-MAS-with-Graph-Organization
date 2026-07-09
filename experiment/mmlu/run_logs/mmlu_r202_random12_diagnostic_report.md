# R202 Projected PromptEdge MMLU Smoke

**Claim boundary**: Diagnostic smoke only. No paper-level accuracy claim; task selection is first-N and not answer-based.

## Result

- Dry run: `False`
- Tasks prepared: `12`
- Tasks evaluated: `12`
- Projected contract-ready: `12/12`
- Baseline correct: `11`
- Projected correct: `11`
- Fixes: `0`
- Harms: `0`
- Cost: `$0.697925`
- Prompt/completion tokens: `73498/22029`

## Boundary

The first-N selection is not answer-based. This smoke is diagnostic and cannot be used as a paper-level accuracy claim.

## Next

If dry_run=true, run the same command without --dry_run only if the user accepts the diagnostic cost. If dry_run=false, analyze fix/harm as diagnostic-only.
