# R217 Non-Abstain Router-Final Targets

**Claim boundary**: Target extraction only; no API and no accuracy claim.

## Result

- Train source rows: `200`
- Frozen eval source rows: `34`
- Output records: `234`
- Router actions: `{'abstain': 221, 'switch_to_objective': 13}`
- Split roles: `{'frozen_eval': 34, 'train': 200}`
- Leakage violations: `0`
- Leakage pass: `True`

## Split Breakdown

| Split | Abstain | Switch |
|---|---:|---:|
| train | `189` | `11` |
| frozen_eval | `32` | `2` |

Frozen-eval switch tasks: `task_108`, `task_250`.

## Verification

| Test | Result |
|---|---:|
| `tests.test_r217_non_abstain_router_targets` | `4/4` |
| `tests.test_r212_router_final_leakage_scan` | `3/3` |
| `tests.test_r211_mmlu_router_final_schema` | `2/2` |

## Boundary

These targets create non-abstain router labels from label-free objective-safety rows. They are not answer-accuracy results, and frozen tail34 rows must not be used for training.

## Interpretation

R217 closes the R215 blocker that no non-abstain router-final target existed. It does not authorize API. These labels come from AQuA objective-safety traces and must next be materialized into a small manifest with explicit train/frozen-eval separation before any runtime use.
