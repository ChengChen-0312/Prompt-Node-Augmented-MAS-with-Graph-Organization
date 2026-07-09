# R302 Learned SafetyGatePN Distillation

**Claim boundary**: Machine-learning gate over existing ARG outputs. Training uses generic synthetic no-harm rows, not MMLU task ids or labels. This is a prototype and needs a larger prospective train/eval split for a paper claim.

- Official: R302 `89/100` vs ARG `88/100`; delta `1`
- Audit-clean: R302 `91/100` vs ARG `90/100`; delta `1`
- Official fix/harm: `1/0`
- Audit-clean fix/harm: `1/0`
- Switches: `1`; tasks `['MMLU-high_school_statistics_test-32']`
- Synthetic training rows: `7`
- Feature names: `['bias', 'has_none_option', 'has_complete_group_counts', 'asks_mean_comparison', 'has_inferential_test_options', 'not_mentions_sample', 'arg_prediction_not_none_option', 'complete_mean_inference_interaction', 'safe_switch_interaction']`

## Interpretation

The learned gate reproduces R301's safe switch using a small, generic synthetic curriculum. This is now a machine-learning SafetyGatePN rather than a pure hand rule, but the paper still needs a larger held-out training protocol before this becomes a strong transfer claim.
