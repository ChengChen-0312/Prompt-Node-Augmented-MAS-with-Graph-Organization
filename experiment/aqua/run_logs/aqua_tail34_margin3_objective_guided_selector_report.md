# AQuA First200 Margin-Gated Objective-Guided PromptNode Variant Selector

## Raw Summary

| Metric | Value |
| --- | ---: |
| Min score margin | `3` |
| Objective-guided selector | `28/34` |
| ARG baseline | `28/34` |
| Delta vs ARG | `+0` |
| Fix/Harm vs ARG | `0/0` |
| Switches | `0` |
| Source counts | `baseline=34` |
| Clean split | `27/28` |
| Noisy/Ambiguous split | `1/6` |
| Clean Fix/Harm | `0/0` |
| Noisy/Ambiguous Fix/Harm | `0/0` |

## Interpretation

This is an exploratory replay of the R038 graph-quality objective as a conservative answer selector. The selector switches away from ARG only when the top objective score maps to a unique valid option; otherwise it keeps ARG's baseline prediction. The rule uses PromptNode contract evidence and direct-agent agreement, not gold labels or audit labels.

This result is not yet a prospective validation because it reuses first200 traces that informed method design. It should be treated as a candidate for tail34 or transfer validation once same-model API quota returns.

## Key Findings

1. **Observation**: Objective-guided selection reaches `28/34` versus ARG `28/34`, with fix/harm `0/0`. **Interpretation**: The contract-coverage objective can recover additional answer signal from PromptNode variants. **Implication**: R038 can be promoted from a graph-quality diagnostic to a candidate graph-selection rule. **Next step**: Validate prospectively on tail34 before using this as a main accuracy claim.

2. **Observation**: The clean split is `27/28` with clean fix/harm `0/0`. **Interpretation**: The margin gate removes observed harms in this replay, making it safer than the ungated R039 selector. It still has lower clean coverage than R035 pure multi-contract selection, so R035 remains the stronger mechanism claim. **Implication**: Treat this as a system-candidate ablation, not as the final SCI claim. **Next step**: Validate the margin-gated selector prospectively on tail34 and compare it against R035 pure/full selectors.

3. **Observation**: The selector switches only on unique top objective options. **Interpretation**: This reduces blind switching under R038 ties; the score margin adds an additional separation constraint when enabled. **Implication**: The next graph objective should optimize separation between top variants, not only raw contract score. **Next step**: Use the selected margin as a pre-registered tail34 setting rather than tuning on tail34.

## Suggested Next Experiments

- Tail34 prospective replay for R035 pure/full, R039 ungated, and R040 margin-gated selectors once quota returns.
- Transfer multiple-choice math validation with the same objective-gated selector.
