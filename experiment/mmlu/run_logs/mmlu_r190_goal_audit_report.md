# R190 Five-Iteration SCI-Q2 Goal Audit

**Claim boundary**: audit only. No API evaluation, no new accuracy claim, and no claim that PromptNode/PromptEdge exceeds ARG-Designer.

## Audit Decision

Status: `aligned_authorize_tiny_diagnostic_api_smoke_only`

No goal drift was detected. The work still follows the SCI-Q2 objective: ARG-Designer remains the baseline, MMLU transfer is the robustness route, and PromptNode/PromptEdge is represented before execution rather than as an answer patch.

The claim boundary changed. R188 shows that raw learned edge generation is not reliable enough: only `2/50` generated graphs are contract-ready. R189 shows that a constrained decoder projection can make `50/50` graphs contract-ready, but this supports a hybrid method, not a fully learned edge-linking claim.

## Evidence Since R185

- R186 trained a 9-role PN-capable graph-policy checkpoint for 1 epoch; validation loss `19.0621`.
- R187 raw graph audit failed: contract-ready `1/50`.
- R188 trained for 5 epochs; validation loss improved to `11.5663`, but raw contract-ready stayed low at `2/50`.
- R189 projection audit passed: projected contract-ready `50/50`.

## Authorized Next

R191 may implement a projected-PromptEdge MMLU transfer smoke runner, and R192 may run at most 4 diagnostic API tasks with `gpt-4o-2024-08-06`, R162 baseline lookup, and cost accounting.

This smoke is diagnostic-only. It cannot become a paper main result.

## Forbidden

- Do not claim SCI-Q2 readiness.
- Do not claim learned edge-linking from R189 projection.
- Do not run broad MMLU API evaluation.
- Do not select a paper main result from diagnostic baseline-wrong tasks.
