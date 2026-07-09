# AQuA First200 PromptNode Contract Ablation Table

| Variant | Overall | Clean | Noisy/Ambiguous | Delta vs ARG | Fix/Harm | Clean Fix/Harm | Switches | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| ARG baseline | `165/200` | `152/167` | `13/33` | `+0` | `0/0` | `0/0` | `0` | reference |
| PN result ensemble | `170/200` | `154/167` | `16/33` | `+5` | `9/4` | `3/1` | `22` | label-free result majority |
| R034 single-router contract | `167/200` | `154/167` | `13/33` | `+2` | `2/0` | `2/0` | `2` | single PN trace |
| Single-candidate contract | `165/200` | `152/167` | `13/33` | `+0` | `0/0` | `0/0` | `1` | single PN graph-selection trace |
| Single-conservative contract | `165/200` | `152/167` | `13/33` | `+0` | `0/0` | `0/0` | `0` | single abstention trace |
| Single-calibrated contract | `167/200` | `154/167` | `13/33` | `+2` | `2/0` | `2/0` | `2` | single utility-gated trace |
| R035 direct-consensus only | `167/200` | `154/167` | `13/33` | `+2` | `2/0` | `2/0` | `2` | router agrees with direct agents in >=2 PN variants |
| R035 strong-contract only | `166/200` | `153/167` | `13/33` | `+1` | `1/0` | `1/0` | `1` | same strong router option in >=3 PN variants |
| R035 multi-contract only | `168/200` | `155/167` | `13/33` | `+3` | `3/0` | `3/0` | `3` | pure virtual-node mechanism |
| R035 multi-contract + invalid fallback | `174/200` | `156/167` | `18/33` | `+9` | `9/0` | `4/0` | `14` | mechanism plus invalid-answer fallback |
| Sensitivity: strong>=2 | `167/200` | `154/167` | `13/33` | `+2` | `3/1` | `3/1` | `5` | lower strong-contract threshold |
| Sensitivity: strict direct>=3 strong>=4 | `165/200` | `152/167` | `13/33` | `+0` | `0/0` | `0/0` | `0` | stricter agreement threshold |

## Key Findings

1. **Observation**: R035 multi-contract only reaches `168/200`, clean `155/167`, and clean fix/harm `3/0`.
   **Interpretation**: Multi-view PromptNode contracts recover one additional clean ARG-Designer error beyond the best single-trace contract variants.
   **Implication**: The defensible virtual-node mechanism is cross-view contract agreement, not naive PromptNode insertion.
   **Next step**: Validate the same rule on pre-registered tail34 when same-model quota returns.

2. **Observation**: Single-router and single-calibrated contracts each reach `167/200`, while single-candidate and single-conservative contracts do not improve over ARG.
   **Interpretation**: Individual PromptNode traces are sparse and variant-sensitive.
   **Implication**: A paper claim should avoid saying any single virtual node is enough; it should emphasize multi-view agreement across PromptNode graph variants.
   **Next step**: Add a graph-selection objective that maximizes validated contract agreement before final answer selection.

3. **Observation**: Lowering the strong-contract threshold to `>=2` increases switches from `3` to `5` but introduces clean harm (`3/1`).
   **Interpretation**: More aggressive virtual-node coverage is not automatically better.
   **Implication**: The R035 thresholds are not arbitrary optimism; they trade coverage for zero observed clean harm on first200.
   **Next step**: Treat `strong>=2` as a rejected sensitivity control in the paper.

4. **Observation**: The full selector reaches `174/200`, but `11/14` switches are invalid-answer fallback rather than pure PromptNode contract switches.
   **Interpretation**: Full-system accuracy is promising, but the mechanism and fallback contributions must be reported separately.
   **Implication**: SCI-style claims should center on clean virtual-node fixes, with invalid fallback presented as a system component, not the core novelty.
   **Next step**: Keep pure/full result columns separate in every main table.
