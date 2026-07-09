# R373 Retrain After R369 Hard Negatives

**Claim boundary**: R373 retrains the source-invariant graph-policy gate after adding R369 hard negatives and history positives. It is an offline step only.

- Train/dev/test records: `241/37/65`
- Dev/test FP: `0/0`
- R369 wrong max probability: `0.35769`
- R369 history positive min probability: `0.978505`
- Next required run: `R374_history_guarded_fresh_eval_preflight`
