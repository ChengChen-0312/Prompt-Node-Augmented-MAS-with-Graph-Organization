# Contract-Consensus Selector Design

## Problem Anchor

- Bottom-line problem: improve over ARG-Designer using train-time PromptNode virtual nodes, not noisy-label matching or fake math patches.
- Must-solve bottleneck: current PN variants contain useful verification evidence, but naive final aggregation either harms ARG-correct clean rows or mostly improves official score by recovering invalid `None.` outputs.
- Non-goals: do not use task IDs, gold answers, clean/noisy audit labels, official rationales, or nearest-option rescue at inference time.
- Success condition for this iteration: demonstrate a label-free-at-inference selector whose extra clean-row gains come from PN verifier/router contracts, with fix/harm explicitly reported.

## Candidate Approaches

1. **Keep R033 invalid fallback only**: stable official gain, but weak paper story because most improvement is noisy-label recovery.
2. **Trust any strong PN_Router contract**: uses virtual nodes directly, but first200 analysis shows it can harm ARG-correct rows.
3. **Contract-consensus selector**: use PN_Router only when its strong option-binding contract agrees with the non-PN direct-node majority. Keep invalid baseline fallback as a separate engineering fallback.

Recommended route: Approach 3. It is still simple, uses existing PromptNode traces, and directly tests whether virtual nodes can validate direct evidence before overriding ARG-Designer.

## Method

For each task, the selector receives:

- ARG baseline prediction.
- PN method trace from one PN variant, including `agent_outputs`.
- PN result ensemble prediction for invalid-baseline fallback.

It extracts:

- `router_option`: the first `PN_Router` `SUPPORTED_OPTION` whose `BINDING_STATUS` is `EXACT_MATCH`, `EQUIVALENT_FORM`, or `EQUIVALENT`.
- `direct_majority`: the majority A-E answer among non-PN nodes in that same graph.
- `direct_majority_count`.
- `baseline_valid`.

Decision:

1. If baseline is invalid and ensemble is valid, use ensemble.
2. Else, if `router_option` is valid, differs from baseline, equals `direct_majority`, and `direct_majority_count >= 2`, use `router_option`.
3. Otherwise keep ARG baseline.

## Evidence Boundary

This is still an offline replay over existing first200 results. It can support a mechanism claim if clean-row gains improve without harms, but it is not final SCI Q2 evidence until pre-registered tail34 or another held-out multiple-choice benchmark is run with the same model.
