# R392 Retrain After Mixed Nonmath Hard Negatives

**Claim boundary**: R392 retrains the source-invariant graph-policy gate with weighted R389 hard negatives. It is offline only.

- Train/dev/test records: `244/37/65`
- Hard-negative weight: `3.0`
- Dev/test FP: `0/0`
- R389 wrong max probability: `0.429324`
- R389 positive min probability: `0.929738`
- Next required run: `R393_replay_mixed_nonmath_with_retrained_gate`
