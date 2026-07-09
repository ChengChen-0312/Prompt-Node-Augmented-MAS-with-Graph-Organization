# AQuA First200 Objective-Guided PromptNode Variant Selector

## Raw Summary

| Metric | Value |
| --- | ---: |
| Min score margin | `0` |
| Objective-guided selector | `172/200` |
| ARG baseline | `165/200` |
| Delta vs ARG | `+7` |
| Fix/Harm vs ARG | `9/2` |
| Switches | `16` |
| Source counts | `baseline=184, objective_top=16` |
| Clean split | `155/167` |
| Noisy/Ambiguous split | `17/33` |
| Clean Fix/Harm | `4/1` |
| Noisy/Ambiguous Fix/Harm | `5/1` |

## Interpretation

This is an exploratory replay of the R038 graph-quality objective as a conservative answer selector. The selector switches away from ARG only when the top objective score maps to a unique valid option; otherwise it keeps ARG's baseline prediction. The rule uses PromptNode contract evidence and direct-agent agreement, not gold labels or audit labels.

This result is not yet a prospective validation because it reuses first200 traces that informed method design. It should be treated as a candidate for tail34 or transfer validation once same-model API quota returns.

## Key Findings

1. **Observation**: Objective-guided selection reaches `172/200` versus ARG `165/200`, with fix/harm `9/2`. **Interpretation**: The contract-coverage objective can recover additional answer signal from PromptNode variants. **Implication**: R038 can be promoted from a graph-quality diagnostic to a candidate graph-selection rule. **Next step**: Validate prospectively on tail34 before using this as a main accuracy claim.

2. **Observation**: The clean split is `155/167` with clean fix/harm `4/1`. **Interpretation**: The objective-guided selector is less clean-safe than R035 pure multi-contract selection when it introduces clean harm. R035 remains the safer mechanism claim until a stricter prospective selector is validated. **Implication**: Treat this as a system-candidate ablation, not as the final SCI claim. **Next step**: Evaluate a margin-gated selector and compare clean fix/harm.

3. **Observation**: The selector switches only on unique top objective options. **Interpretation**: This reduces blind switching under R038 ties; the score margin adds an additional separation constraint when enabled. **Implication**: The next graph objective should optimize separation between top variants, not only raw contract score. **Next step**: Use the selected margin as a pre-registered tail34 setting rather than tuning on tail34.

## Suggested Next Experiments

- Tail34 prospective replay for R035 pure/full, R039 ungated, and R040 margin-gated selectors once quota returns.
- Transfer multiple-choice math validation with the same objective-gated selector.
