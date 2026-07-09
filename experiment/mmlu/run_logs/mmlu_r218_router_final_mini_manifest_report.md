# R218 Router-Final Mini-Manifest

**Claim boundary**: Manifest materialization only; no API and no accuracy claim.

## Result

- Source records: `234`
- Mini records: `67`
- Train switch records: `11`
- Train abstain records selected: `22`
- Frozen eval records: `34`
- Frozen eval switch records: `2`
- Router actions: `{'abstain': 54, 'switch_to_objective': 13}`
- Split roles: `{'frozen_eval': 34, 'train': 33}`

## Verification

| Test | Result |
|---|---:|
| `tests.test_r218_router_mini_manifest` | `2/2` |
| `tests.test_r217_non_abstain_router_targets` | `4/4` |

## Boundary

The mini-manifest keeps all non-abstain train targets, caps train abstain controls, and preserves all frozen-eval rows. It is not an API result.

## Interpretation

R218 materializes the first small non-abstain router-final training/evaluation artifact. It is still data preparation only. Frozen-eval rows remain separate and must not be mixed into training.
