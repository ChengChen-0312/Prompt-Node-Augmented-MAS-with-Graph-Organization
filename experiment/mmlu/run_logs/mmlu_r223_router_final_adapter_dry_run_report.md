# R223 Router-Final Adapter Dry-Run

**Claim boundary**: Local adapter dry-run only; no API and no accuracy claim.

## Result

- Input files: `5`
- Records: `335`
- Would switch: `106`
- Leakage violations: `0`
- Leakage pass: `True`
- Variants: `{'abstain_only_router': 67, 'always_switch_to_objective': 67, 'node_only_no_promptedge_text': 67, 'proposed_router_final': 67, 'random_switch_labels_same_rate': 67}`

## Verification

| Test | Result |
|---|---:|
| `tests.test_r223_router_final_adapter_dry_run` | `4/4` |
| `tests.test_r222_control_manifest_leakage_scan` | `3/3` |
| `tests.test_r221_router_control_manifests` | `5/5` |

## Boundary

The adapter only maps manifest rows to local switch/abstain decisions. It does not call an LLM and does not evaluate answer accuracy.

## Interpretation

R223 validates the local router-final adapter surface for the proposed mini-manifest and four controls. It is still pre-API infrastructure: the adapter shows what would switch, not whether the answer would become correct.
