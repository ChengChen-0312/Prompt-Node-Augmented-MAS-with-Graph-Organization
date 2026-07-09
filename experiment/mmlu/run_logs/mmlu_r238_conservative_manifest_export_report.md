# R238 Conservative Router-Final Manifest Export

**Claim boundary**: Manifest export only; no API, no accuracy claim, and no SCI-Q2 readiness claim.

- Policy: `baseline_consensus_guard_top3`
- Records: `335`
- Proposed rows: `67`
- Proposed switches: `10`
- Control rows: `268`
- Switch counts by variant: `{'always_switch_to_objective': 67, 'node_only_no_promptedge_text': 10, 'proposed_conservative_router': 10, 'random_switch_labels_same_rate': 10}`
- Output dir: `experiment/mmlu/promptedge_targets/r238_conservative`

## Verification

| Test | Result |
|---|---:|
| `tests.test_r238_conservative_manifest_export` | `4/4` |
| `tests.test_r237_apply_conservative_policy` | `3/3` |

## Boundary

These manifests encode the conservative abstention policy and controls. They do not call a model or prove accuracy.
