# R393 Replay Mixed Nonmath With Retrained Gate

**Claim boundary**: R393 replays R389 outputs with the R392 weighted gate. It is not a fresh API result, but verifies that the updated gate removes known wrong-forwards without losing the positive delta.

- ARG/original/retrained: `19/20/20`
- Retrained forward/fix/harm/wrong-forward: `11/1/0/0`
- Blocked original wrong-forwards: `['MMLU-nonstem-sociology_test-18', 'MMLU-nonstem-world_religions_test-18']`
- Next required run: `R394_larger_mixed_nonmath_fresh_preflight`
