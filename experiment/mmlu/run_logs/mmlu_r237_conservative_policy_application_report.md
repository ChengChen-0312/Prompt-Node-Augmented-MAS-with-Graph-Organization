# R237 Conservative Policy Application

**Claim boundary**: Offline policy replay only; no API, no superiority claim, and no SCI-Q2 readiness claim.

Policy: `baseline_consensus_guard_top3`

## Split Results

| Split | Metrics |
|---|---|
| `all` | `57/67` acc, `6/0` fix/harm, `10` switches, source missing `0` |
| `frozen_eval` | `29/34` acc, `1/0` fix/harm, `1` switches, source missing `0` |
| `train` | `28/33` acc, `5/0` fix/harm, `9` switches, source missing `0` |

## R233 Subset

`2/4` acc, `1/0` fix/harm, `3` switches, source missing `0`

## Verification

| Test | Result |
|---|---:|
| `tests.test_r237_apply_conservative_policy` | `3/3` |
| `tests.test_r236_conservative_abstention_policy` | `5/5` |

## Interpretation

The conservative policy should be judged as an offline replay, not a new model result. Its purpose is to verify that the abstention boundary learned from R234 eliminates the observed clean harm before any future API run.
