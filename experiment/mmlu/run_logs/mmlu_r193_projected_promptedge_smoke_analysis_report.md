# R193 Projected PromptEdge Smoke Analysis

**Claim boundary**: diagnostic analysis only. This first4 smoke is not a paper-level accuracy result and does not prove superiority over ARG-Designer.

## Result

- Selection: `first_n_no_answer_filter`
- Tasks: `4`
- R162 ARG baseline: `4/4`
- Projected PromptEdge: `4/4`
- Fixes: `0`
- Harms: `0`
- Raw contract-ready graphs: `0/4`
- Projected contract-ready graphs: `4/4`
- Cost: `$0.401090`
- Prompt/completion tokens: `41962/12752`

## Diagnosis

The safety smoke passed: projected PromptEdge did not harm the first four transfer tasks. It also did not provide an improvement signal, because all four tasks were already correct under R162.

The graph evidence matters: all four raw generated graphs were structurally incomplete for PromptEdge, while projection made all four execution-ready. This supports the hybrid constrained-decoder direction, not fully learned edge linking.

## Next

R194 should choose between:

1. A tiny baseline-wrong diagnostic slice for mechanism debugging only.
2. A small random slice for unbiased harm-rate estimation.
3. Returning to training/decoder design if the target is learned edge-linking rather than hybrid projection.
