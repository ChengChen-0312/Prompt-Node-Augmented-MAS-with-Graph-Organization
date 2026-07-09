# R304 Multi-Trigger Learned SafetyGatePN

**Claim boundary**: Accuracy-bearing offline expansion over existing ARG outputs. The three audited tasks are excluded from main97; selection does not use true labels, correctness fields, or task ids.

- Main97 official: R304 `93/97` vs ARG `88/97`; delta `5`
- Main97 audit-clean: R304 `93/97` vs ARG `88/97`; delta `5`
- Main97 fix/harm: `5/0`; audit-clean `5/0`
- Full100 official/audit-clean: `94/100` / `96/100`
- Switches: `6`; tasks `['MMLU-high_school_statistics_test-32', 'MMLU-college_mathematics_test-26', 'MMLU-high_school_statistics_test-127', 'MMLU-college_mathematics_test-67', 'MMLU-college_chemistry_test-97', 'MMLU-college_mathematics_test-92']`
- Decision rules: `{'keep_arg_multi_gate': 94, 'forward_census_no_inference': 1, 'forward_alternating_work_rate': 1, 'forward_expected_value_single_event': 1, 'forward_ring_ideal_structure': 1, 'forward_nmr_frequency_constant': 1, 'forward_uniform_probability_geometry': 1}`
- Excluded appendix tasks: `['MMLU-college_chemistry_test-62', 'MMLU-high_school_physics_test-67', 'MMLU-high_school_statistics_test-32']`

## Interpretation

R304 expands the virtual-node logic from a single SafetyGatePN into a multi-verifier graph: option binding, symbolic calculation, tool-resource constants, and structure verifiers write candidate labels, while a learned SafetyGatePN decides whether to forward them. The main result excludes the three audited items requested by the user.
