# R242 Fit Train-Time Abstention Policy

**Claim boundary**: Offline train/frozen policy fit only; no API, no superiority claim, and no SCI-Q2 readiness claim.

- Fitted spec: `objective_top_score >= 3 and baseline_direct_majority_count < 3`
- Candidate specs: `60`

| Split | Policy Acc | Baseline Acc | Fix/Harm | Clean Harms | Switches |
|---|---:|---:|---:|---:|---:|
| train | `28/33` | `23/33` | `5/0` | `0` | `9` |
| frozen_eval | `29/34` | `28/34` | `1/0` | `0` | `1` |
| all | `57/67` | `51/67` | `6/0` | `0` | `10` |

## Verification

| Test | Result |
|---|---:|
| `tests.test_r242_fit_abstention_policy` | `3/3` |
| `tests.test_r241_abstention_feature_table` | `3/3` |

## Boundary

The fitted policy is selected only on train rows and evaluated on frozen rows. This is still offline evidence and does not authorize a paper-level superiority claim.
