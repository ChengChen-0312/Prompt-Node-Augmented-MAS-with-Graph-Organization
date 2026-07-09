# R376 History-Guarded Fresh Eval Analysis

**Claim boundary**: R376 analyzes R375. It supports no-harm on this fresh history subset, but no positive delta. The main bottleneck is candidate-to-edge option binding: the PromptNode often wrote a high-confidence rationale while leaving candidate_label empty.

- ARG: `6/12`
- Hybrid: `6/12`
- Delta correct: `0`
- Gate forward/fix/harm/wrong-forward: `1/0/0/1`
- Empty-label high-confidence rationales: `9`
- Option-binding bottleneck tasks: `['MMLU-nonstem-high_school_us_history_test-18', 'MMLU-nonstem-high_school_us_history_test-19', 'MMLU-nonstem-high_school_us_history_test-21', 'MMLU-nonstem-high_school_us_history_test-25']`
- Explicit true-option rationale tasks: `['MMLU-nonstem-high_school_us_history_test-21', 'MMLU-nonstem-high_school_us_history_test-26']`
- Next required run: `R377_option_binding_promptedge_replay`
