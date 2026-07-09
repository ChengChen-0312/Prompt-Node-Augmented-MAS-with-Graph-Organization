# AQuA First200 Multi-Contract Union Selector Analysis

**Date**: 2026-07-08
**Slices**: first100 + next100 from `task_split_aqua.json`
**Input systems**: ARG baseline, four PN traces (`router`, `candidate`, `conservative`, `calibrated`), PN result ensemble
**LLM/API use**: none; replay over existing `gpt-4o-2024-08-06` results

## Method

The R035 selector expands R034 by treating each PN graph variant as a separate virtual verification view.

For each PN trace, it extracts:

- the first strong `PN_Router` contract: `SUPPORTED_OPTION` in `A`-`E` and `BINDING_STATUS` in `EXACT_MATCH`, `EQUIVALENT_FORM`, or `EQUIVALENT`;
- the non-PN direct-agent majority;
- a direct-consensus proposal when router option equals direct majority and the direct majority count is at least `2`.

The selector overrides ARG baseline when either condition holds:

1. the same option receives direct-consensus proposals from at least `2` PN variants; or
2. the same option receives strong router contracts from at least `3` PN variants.

The full selector also uses the existing invalid-baseline fallback to the PN ensemble. That fallback is counted separately from pure multi-contract switches.

## Raw Data Table

| Variant | Overall | Clean | Noisy/Ambiguous | Delta vs ARG | Fix/Harm | Switches | Multi-Contract Switches | Invalid Fallback |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ARG baseline | `165/200` | `152/167` | `13/33` | reference | n/a | n/a | n/a | n/a |
| PN result ensemble | `170/200` | `154/167` | `16/33` | `+5` | `9/4` | result aggregation | n/a | n/a |
| R034 contract-only | `167/200` | `154/167` | `13/33` | `+2` | `2/0` | `2` | `2` | `0` |
| R035 multi-contract only | `168/200` | `155/167` | `13/33` | `+3` | `3/0` | `3` | `3` | `0` |
| R035 multi-contract + invalid fallback | `174/200` | `156/167` | `18/33` | `+9` | `9/0` | `14` | `3` | `11` |

## Split Results

| Variant | first100 | next100 |
| --- | ---: | ---: |
| Multi-contract only | `84/100` | `84/100` |
| Multi-contract + invalid fallback | `87/100` | `87/100` |

## Pure Contract Switches

| Task | Slice | Audit Label | Rule Evidence | Gold | ARG | Selected |
| --- | --- | --- | --- | --- | --- | --- |
| `task_122` | `aqua_100` | clean | strong contract majority: `A=3`, `E=1` | `A` | `C` | `A` |
| `task_197` | `aqua_next100` | clean | direct-consensus contracts: `C=2`; strong contracts tie `C=2`, `A=2` | `C` | `A` | `C` |
| `task_67` | `aqua_next100` | clean | direct-consensus contracts: `B=2`; strong contracts `B=2` | `B` | `A` | `B` |

All pure multi-contract switches are clean-row fixes, with no observed harms on first200.

## Paired Check

Against ARG baseline on first200:

- Multi-contract only: `3` fixes and `0` harms. Two-sided exact binomial/McNemar-style p-value: `0.25`.
- Multi-contract + invalid fallback: `9` fixes and `0` harms. Two-sided exact binomial/McNemar-style p-value: `0.00390625`.
- Clean rows for the full selector: `4` fixes and `0` harms. Two-sided exact binomial/McNemar-style p-value: `0.125`.

## Key Findings

1. **Observation**: Multi-contract union improves pure virtual-node clean accuracy from R034's `154/167` to `155/167`.
   **Interpretation**: Different PromptNode graph variants carry complementary verification evidence; aggregating contracts across variants increases safe coverage.
   **Implication**: The method story should center on multi-view virtual-node verification, not on single-trace routing.
   **Next step**: Train graph generation or candidate selection to intentionally maximize validated multi-contract agreement.

2. **Observation**: The full selector reaches `174/200`, improving `+9` over ARG baseline and `+4` over the PN ensemble, with no observed baseline-correct harms.
   **Interpretation**: Combining validated virtual-node consensus with invalid-answer fallback yields the strongest operational system so far.
   **Implication**: This is promising, but `11/14` switches still come from fallback, so the paper must separate mechanism and system gains.
   **Next step**: Validate the full selector on tail34 once same-model quota returns.

3. **Observation**: Pure multi-contract switches are all clean fixes (`task_122`, `task_197`, `task_67`).
   **Interpretation**: This is the strongest current evidence that virtual nodes improve performance rather than exploiting noisy labels.
   **Implication**: The SCI Q2 route should frame PromptNode as a multi-view option-binding validator and show how coverage scales.
   **Next step**: Add a training objective or graph-selection score that rewards strong contract agreement across candidate PromptNode graphs.

## Result-To-Claim Verdict

- **claim_supported**: partial
- **what_results_support**: Multi-view PromptNode contract aggregation safely fixes three clean ARG-Designer mistakes on AQuA first200, improving clean accuracy from `152/167` to `155/167` without observed harm.
- **what_results_do_not_support**: This still does not prove a final SCI Q2-level claim. The clean mechanism signal is positive but small and needs pre-registered held-out validation.
- **recommended_claim_revision**: "PromptNode virtual nodes improve multi-agent reasoning when treated as multi-view option-binding validators; aggregating strong contracts across graph variants increases safe clean-row coverage beyond a single PromptNode trace."
