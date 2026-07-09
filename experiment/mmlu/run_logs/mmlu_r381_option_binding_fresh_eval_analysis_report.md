# R381 OptionBinding Fresh Eval Analysis

**Claim boundary**: R381 analyzes R380. The fresh result is positive no-harm on 24 new history items, but because the candidate path forwards every item, a plain-requery control is required before attributing the gain to PromptNode/PromptEdge graph structure.

- ARG: `21/24`
- Hybrid: `24/24`
- Delta correct: `3`
- Candidate labels / edge-applied: `24/2`
- Gate forward/fix/harm/wrong-forward: `24/3/0/0`
- Fix tasks: `['MMLU-nonstem-high_school_us_history_test-30', 'MMLU-nonstem-high_school_us_history_test-39', 'MMLU-nonstem-high_school_us_history_test-43']`
- Plain requery control required: `True`
- Next required run: `R382_plain_requery_control_preflight`
