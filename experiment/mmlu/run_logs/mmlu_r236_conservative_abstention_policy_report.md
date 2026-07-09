# R236 Conservative Abstention Policy

**Claim boundary**: Offline policy derivation only; no API, no superiority claim, and no SCI-Q2 readiness claim.

## Candidate Results

| Policy | Acc | Fix/Harm | Clean Fix/Harm | Switches |
|---|---:|---:|---:|---:|
| `current_top3` | `169/200` | `5/1` | `1/1` | `10` |
| `high_confidence_top10` | `168/200` | `3/0` | `0/0` | `4` |
| `high_confidence_top11` | `166/200` | `1/0` | `0/0` | `1` |
| `baseline_invalid_top10` | `166/200` | `1/0` | `0/0` | `1` |
| `baseline_consensus_guard_top3` | `170/200` | `5/0` | `1/0` | `9` |
| `baseline_consensus_guard_top10` | `168/200` | `3/0` | `0/0` | `4` |

## Selected Policy

- Policy: `baseline_consensus_guard_top3`
- Accuracy: `170/200`
- Fix/harm: `5/0`
- Clean fix/harm: `1/0`
- Switch rate: `0.0450`

## Verification

| Test | Result |
|---|---:|
| `tests.test_r236_conservative_abstention_policy` | `5/5` |
| `tests.test_r234_tiny_diagnostic_failure_analysis` | `4/4` |

## Interpretation

The selected policy keeps the R233 lesson explicit: switch only when objective evidence differs from ARG and the ARG direct majority is not strong. This removes the clean harm seen in the prompt-only router while preserving a small number of fixes in the offline first200 slice.
