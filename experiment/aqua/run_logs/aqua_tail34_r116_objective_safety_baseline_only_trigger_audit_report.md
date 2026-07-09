# R116 Objective-Safety Baseline-Only Trigger Audit

**Claim boundary**: baseline-only trigger audit; no accuracy, cost-reduction, or deployment claim

- Candidate rules: `6`
- Best train rule: `always_fallback`
- Best train agreement: `189/200`
- Best train frozen switch recall: `0/2`
- Baseline-split frozen switch recall: `1/2`
- Baseline-split false switches: `['task_6']`
- Baseline-split missed switches: `['task_250']`
- Best recall rule: `baseline_direct_valid_ge2`
- Best recall frozen switch precision: `2/26`
- Baseline-only proxy sufficient: `False`
- Input-field violations: `0`

| Rule | Train agreement | Frozen tail34 agreement | Frozen switch recall | Frozen switch precision |
| --- | ---: | ---: | ---: | ---: |
| `always_fallback` | `189/200` | `32/34` | `0/2` | `0/0` |
| `baseline_direct_votes_split` | `188/200` | `32/34` | `1/2` | `1/2` |
| `baseline_direct_valid_ge2` | `127/200` | `10/34` | `2/2` | `2/26` |
| `baseline_direct_majority_le1` | `72/200` | `24/34` | `1/2` | `1/10` |
| `baseline_direct_split_or_valid_ge2` | `127/200` | `10/34` | `2/2` | `2/26` |
| `baseline_direct_split_or_majority_le1` | `72/200` | `24/34` | `1/2` | `1/10` |

## Interpretation

R116 shows that baseline-only trigger rules cannot replace the objective-guided trace. The most conservative train-selected rule misses both frozen switch targets; the direct-split rule misses clean `task_250`; and the high-recall rule covers both switch targets only by triggering many false switches. Cost reduction therefore needs a lightweight objective trace or graph-policy signal, not a baseline-only shortcut.
