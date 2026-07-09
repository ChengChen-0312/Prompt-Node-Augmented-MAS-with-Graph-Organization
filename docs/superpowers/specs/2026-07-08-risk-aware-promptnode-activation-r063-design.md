# R063 Risk-Aware PromptNode Activation Design

## Goal

Design a wider online PromptNode activation policy than R062 while preserving
the no-gold-label boundary. R062 is safe but too sparse: it runs PromptNodes on
only `1/34` tail34 tasks and ties ARG at `28/34`.

## Motivation

R060 shows dense PromptNode execution is harmful (`25/34`, fix/harm `1/4`).
R062 shows direct-vote conflict gating avoids those harms but misses most ARG
failure cases. R063 should activate PromptNodes when baseline evidence is risky,
not only when non-PromptNode agents explicitly disagree.

## Risk Features

R063 can use only fields visible before final correctness is known:

- `direct_conflict`: at least two distinct direct A-E votes and no majority.
- `final_direct_mismatch`: final baseline prediction is not supported by any
  direct agent vote.
- `weak_final_support`: final baseline prediction has fewer than two direct
  votes.
- `missing_direct_vote`: at least one non-PromptNode agent output lacks a valid
  A-E final answer.
- `invalid_baseline_prediction`: final parser fails to extract A-E.
- `low_direct_coverage`: fewer than two valid direct votes.

After PromptNodes are run, selection may use only PromptNode runtime evidence:

- Strong router contract: `EXACT_MATCH`, `EQUIVALENT_FORM`, or `EQUIVALENT`.
- Valid router option.
- Valid PromptNode final prediction.
- Router support compatible with direct evidence or explicitly resolving a
  baseline/direct mismatch.

## Leakage Boundary

R063 replay can be exploratory on tail34, but any thresholds or rules chosen
after inspecting tail34 correctness cannot be claimed as held-out evidence.
Fresh system claims require a later untouched split or transfer validation.

The pre-PN risk features and post-PN gate must not read `true_answer`,
`is_solved`, task ids, clean/noisy labels, or any outcome-derived field.

## Outputs

- Risk-feature audit for R062 baseline records.
- R063 replay over R062 baseline records plus existing dense R060 PromptNode
  traces.
- Summary comparing ARG, dense R058/R060, R061 replay, R062 fresh, and R063
  exploratory replay.

## Success Criteria

R063 is worth a fresh API run only if exploratory replay improves coverage over
R062 without adding observed harms. If it harms tail34 replay, it should be
recorded as another negative ablation and not run fresh.
