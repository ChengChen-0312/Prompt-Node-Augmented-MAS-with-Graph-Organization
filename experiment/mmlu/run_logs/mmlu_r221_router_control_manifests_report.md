# R221 Router-Final Control Manifests

**Claim boundary**: Control manifest materialization only; no API and no accuracy claim.

## Result

- Variants: `4`
- Total rows: `268`
- Seed: `20260709`

| Variant | Rows | Switch labels |
|---|---:|---:|
| `abstain_only_router` | `67` | `0` |
| `always_switch_to_objective` | `67` | `67` |
| `node_only_no_promptedge_text` | `67` | `13` |
| `random_switch_labels_same_rate` | `67` | `13` |

## Verification

| Test | Result |
|---|---:|
| `tests.test_r221_router_control_manifests` | `5/5` |
| `tests.test_r218_router_mini_manifest` | `2/2` |
| `tests.test_r217_non_abstain_router_targets` | `4/4` |

## Boundary

These are control manifests only. They do not run the model and do not support accuracy claims.

## Interpretation

R221 makes the negative controls executable as data artifacts. The next step is to run a manifest-level leakage scan before any adapter or API work.
