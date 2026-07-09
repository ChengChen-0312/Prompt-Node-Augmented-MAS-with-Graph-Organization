# AQuA First200 Contract-Consensus Selector Analysis

**Date**: 2026-07-08
**Slices**: first100 + next100 from `task_split_aqua.json`
**Input systems**: ARG baseline, PN router-contract traces, PN result ensemble
**LLM/API use**: none; replay over existing `gpt-4o-2024-08-06` results

## Method

The selector uses PromptNode traces only when the virtual router has strong option-binding evidence:

1. Extract the first `PN_Router` contract whose `SUPPORTED_OPTION` is `A`-`E` and whose `BINDING_STATUS` is `EXACT_MATCH`, `EQUIVALENT_FORM`, or `EQUIVALENT`.
2. Extract the non-PN direct-agent majority vote from the same graph trace.
3. Override ARG baseline only if the router option equals that direct majority and `direct_majority_count >= 2`.
4. In the full selector, if ARG baseline emits an invalid option, fall back to the PN result ensemble. This fallback is reported separately from the router-contract switch.

The selector does not use task IDs, gold labels, clean/noisy audit labels, or official rationales at inference time.

## Raw Data Table

| Variant | Overall | Clean | Noisy/Ambiguous | Delta vs ARG | Fix/Harm | Switches | Router Switches | Invalid Fallback |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ARG baseline | `165/200` | `152/167` | `13/33` | reference | n/a | n/a | n/a | n/a |
| PN result ensemble | `170/200` | `154/167` | `16/33` | `+5` | `9/4` | result aggregation | n/a | n/a |
| Contract-only selector | `167/200` | `154/167` | `13/33` | `+2` | `2/0` | `2` | `2` | `0` |
| Contract + invalid fallback | `173/200` | `155/167` | `18/33` | `+8` | `8/0` | `13` | `2` | `11` |

## Split Results

| Variant | first100 | next100 |
| --- | ---: | ---: |
| Contract-only selector | `83/100` | `84/100` |
| Contract + invalid fallback | `86/100` | `87/100` |

## Switched Rows

### Contract-Only

| Task | Slice | Audit Label | Source | Gold | ARG | Selected |
| --- | --- | --- | --- | --- | --- | --- |
| `task_197` | `aqua_next100` | clean | router contract | `C` | `A` | `C` |
| `task_67` | `aqua_next100` | clean | router contract | `B` | `A` | `B` |

### Full Selector

The full selector adds invalid-baseline fallback rows:

| Source | Fixes | Harms |
| --- | ---: | ---: |
| Router contract | `2` | `0` |
| Invalid fallback | `6` | `0` |

Fixes: `task_135`, `task_146`, `task_106`, `task_197`, `task_162`, `task_232`, `task_67`, `task_207`.

## Paired Check

Against ARG baseline on first200:

- Contract-only selector: `2` fixes and `0` harms. Two-sided exact binomial/McNemar-style p-value: `0.5`.
- Contract + invalid fallback: `8` fixes and `0` harms. Two-sided exact binomial/McNemar-style p-value: `0.0078125`.
- Clean rows for the full selector: `3` fixes and `0` harms. Two-sided exact binomial/McNemar-style p-value: `0.25`.

## Key Findings

1. **Observation**: Contract-only switching improves clean accuracy from `152/167` to `154/167` with no observed harm.
   **Interpretation**: PN virtual nodes can provide a useful option-binding verifier when router evidence agrees with direct-agent majority.
   **Implication**: This is a real PromptNode mechanism signal, but it is sparse.
   **Next step**: Train or calibrate graph generation so more rows produce reliable router-direct agreement without increasing harms.

2. **Observation**: The full selector reaches `173/200`, improving over ARG baseline by `+8` and over the PN ensemble by `+3`.
   **Interpretation**: Combining contract consensus with invalid-answer fallback is a stronger operational system.
   **Implication**: This is promising as an engineering result, but only `2/8` fixes come from router-contract switching.
   **Next step**: Report the full selector as a system variant and the contract-only selector as the mechanism isolation.

3. **Observation**: Clean-row gain for the full selector is `+3/167`, while noisy/ambiguous gain is `+5/33`.
   **Interpretation**: Official-score improvement still partly relies on noisy/ambiguous rows.
   **Implication**: A SCI Q2 paper should not use official AQuA first200 alone as the main evidence.
   **Next step**: Run pre-registered tail34 or a new multiple-choice math benchmark once the same-model API quota is available.

## Result-To-Claim Verdict

- **claim_supported**: partial
- **what_results_support**: PromptNode virtual nodes can safely correct some ARG-Designer clean mistakes when a strong router contract agrees with direct-agent majority. Contract-only switching improves clean first200 accuracy from `152/167` to `154/167` with `2/0` fix/harm.
- **what_results_do_not_support**: The evidence still does not prove a final SCI Q2-level claim that PromptNode generally improves clean mathematical reasoning. The mechanism is sparse and needs held-out validation.
- **recommended_claim_revision**: "PromptNode virtual nodes act as option-binding validators that can safely override ARG-Designer when router contracts and direct evidence agree; broader gains require increasing the coverage of such validated consensus."
