# R194 Next-Step Decision

**Claim boundary**: decision memo only. No API evaluation and no accuracy claim.

## Current State

R192 first4 smoke:

- R162 ARG baseline: `4/4`
- Projected PromptEdge: `4/4`
- Fixes: `0`
- Harms: `0`
- Cost: `$0.401090`

This is a safety signal, not an improvement signal.

## Available Diagnostic Pool

R162 has `12` baseline-wrong transfer tasks. The first candidates are:

- `MMLU-high_school_statistics_test-32`
- `MMLU-high_school_physics_test-67`
- `MMLU-abstract_algebra_test-53`
- `MMLU-college_mathematics_test-26`

These are useful for mechanism debugging only. They cannot be used as a paper main result because selection is conditioned on baseline errors.

## Decision

Recommended next step after R195 audit: run a tiny baseline-wrong mechanism diagnostic, with explicit non-claim labeling, R162 baseline lookup, raw/projected graph audit, cost, and fix/harm.

For paper claims, the path remains random/full held-out transfer evaluation after the method is stable.
