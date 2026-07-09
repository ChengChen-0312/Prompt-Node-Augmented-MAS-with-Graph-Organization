# AQuA First200 Contract-Coverage Graph Objective

## Raw Summary

| Metric | Value |
| --- | ---: |
| Total tasks | `34` |
| Positive top-score tasks | `34` (`100.0%`) |
| Mean top score | `2.147` |
| Top-score ties | `28` |
| Unique top method distribution | `calibrated=2, candidate=3, router=1` |
| Diagnostic selected-method answer accuracy | `30/34` (`88.2%`) |
| R035 pure switch tasks | `0` |
| R035 switch top-option agreement | `0/0` |
| R035 switch unique-top agreement | `0/0` |

## Interpretation

This report evaluates a label-free graph-quality objective, not a new answer selector. The score uses PromptNode router contracts, direct-agent agreement, PromptNode graph presence, and conflict/weak-contract penalties. Gold labels and clean/noisy audit labels are not objective inputs.

A high positive top score means at least one PromptNode graph variant produced reusable option-binding evidence. Top-score ties indicate that the objective cannot uniquely choose one variant and should either retain multiple views or ask a future graph generator to increase contract separation.

## Next Step

Use this objective as a training or candidate-selection reward: prefer generated PromptNode graphs that raise strong, directly supported router contracts while avoiding conflict penalties. Validate prospectively on tail34 or transfer data before making any accuracy claim.
