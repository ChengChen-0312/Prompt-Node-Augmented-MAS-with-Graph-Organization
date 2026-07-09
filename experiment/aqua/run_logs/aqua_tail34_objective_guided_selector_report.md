# AQuA First200 Objective-Guided PromptNode Variant Selector

## Raw Summary

| Metric | Value |
| --- | ---: |
| Min score margin | `0` |
| Objective-guided selector | `31/34` |
| ARG baseline | `28/34` |
| Delta vs ARG | `+3` |
| Fix/Harm vs ARG | `3/0` |
| Switches | `4` |
| Source counts | `baseline=30, objective_top=4` |
| Clean split | `28/28` |
| Noisy/Ambiguous split | `3/6` |
| Clean Fix/Harm | `1/0` |
| Noisy/Ambiguous Fix/Harm | `2/0` |

## Interpretation

This is an exploratory replay of the R038 graph-quality objective as a conservative answer selector. The selector switches away from ARG only when the top objective score maps to a unique valid option; otherwise it keeps ARG's baseline prediction. The rule uses PromptNode contract evidence and direct-agent agreement, not gold labels or audit labels.

This result is not yet a prospective validation because it reuses first200 traces that informed method design. It should be treated as a candidate for tail34 or transfer validation once same-model API quota returns.

## Key Findings

1. **Observation**: Objective-guided selection reaches `31/34` versus ARG `28/34`, with fix/harm `3/0`. **Interpretation**: The contract-coverage objective can recover additional answer signal from PromptNode variants. **Implication**: R038 can be promoted from a graph-quality diagnostic to a candidate graph-selection rule. **Next step**: Validate prospectively on tail34 before using this as a main accuracy claim.

2. **Observation**: The clean split is `28/28` with clean fix/harm `1/0`. **Interpretation**: The objective-guided selector is less clean-safe than R035 pure multi-contract selection when it introduces clean harm. R035 remains the safer mechanism claim until a stricter prospective selector is validated. **Implication**: Treat this as a system-candidate ablation, not as the final SCI claim. **Next step**: Evaluate a margin-gated selector and compare clean fix/harm.

3. **Observation**: The selector switches only on unique top objective options. **Interpretation**: This reduces blind switching under R038 ties; the score margin adds an additional separation constraint when enabled. **Implication**: The next graph objective should optimize separation between top variants, not only raw contract score. **Next step**: Use the selected margin as a pre-registered tail34 setting rather than tuning on tail34.

## Suggested Next Experiments

- Tail34 prospective replay for R035 pure/full, R039 ungated, and R040 margin-gated selectors once quota returns.
- Transfer multiple-choice math validation with the same objective-gated selector.
