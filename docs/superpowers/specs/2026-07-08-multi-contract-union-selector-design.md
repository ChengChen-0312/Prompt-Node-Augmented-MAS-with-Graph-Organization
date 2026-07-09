# Multi-Contract Union Selector Design

## Problem Anchor

- Bottom-line problem: improve ARG-Designer with PromptNode virtual nodes, not with noisy-label matching or fake math patches.
- Must-solve bottleneck: R034 showed real but sparse clean-row gains from one PN router-contract view. The next bottleneck is coverage: a single PN trace misses cases where other PN graph variants contain valid virtual-node evidence.
- Non-goals: do not use task IDs, gold answers, clean/noisy audit labels, official rationales, or nearest-option rescue at inference time.
- Success condition for this iteration: increase contract-only clean fix coverage beyond R034 while preserving zero observed harm on first200 replay.

## Design

For each task, collect PromptNode contract evidence from four PN result traces:

- `router`: `*_pn_router_contract_results.jsonl`
- `candidate`: `*_pn_candidate_select_results.jsonl`
- `conservative`: `*_pn_conservative_router_results.jsonl`
- `calibrated`: `*_pn_calibrated_utility_results.jsonl`

For each trace:

1. Extract the first strong `PN_Router` contract: `SUPPORTED_OPTION` in `A`-`E`, `BINDING_STATUS` in `EXACT_MATCH`, `EQUIVALENT_FORM`, or `EQUIVALENT`.
2. Extract non-PN direct-agent majority.
3. Mark a direct-consensus proposal if router option equals direct majority and direct majority count is at least `2`.

The selector can override ARG baseline when either condition holds:

1. **Direct-consensus union**: the same option receives direct-consensus proposals from at least `2` PN variants.
2. **Strong-contract majority**: the same option receives strong router contracts from at least `3` PN variants.

If enabled, invalid-baseline fallback uses the existing PN result ensemble only when ARG baseline does not emit a valid `A`-`E` answer. Reports must separate this fallback from pure virtual-node contract switches.

## Expected Evidence Boundary

Offline first200 analysis suggests:

- Contract-only: `168/200`, clean `155/167`, fix/harm `3/0`.
- Contract + invalid fallback: `174/200`, clean `156/167`, fix/harm `9/0`.

This remains exploratory until tail34 or another held-out multiple-choice benchmark can be run with the same `gpt-4o-2024-08-06` setup.
