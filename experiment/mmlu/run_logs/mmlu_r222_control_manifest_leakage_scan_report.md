# R222 Control Manifest Leakage Scan

**Claim boundary**: leakage scan only. No API evaluation and no accuracy claim.

## Result

- Input dir: `experiment/mmlu/promptedge_targets/r221_controls`
- Files: `4`
- Records: `268`
- Leakage violations: `0`
- Leakage pass: `True`

| File | Records | Violations | Pass |
|---|---:|---:|---|
| `mmlu_r221_abstain_only_router.jsonl` | `67` | `0` | `True` |
| `mmlu_r221_always_switch_to_objective.jsonl` | `67` | `0` | `True` |
| `mmlu_r221_node_only_no_promptedge_text.jsonl` | `67` | `0` | `True` |
| `mmlu_r221_random_switch_labels_same_rate.jsonl` | `67` | `0` | `True` |

## Verification

| Test | Result |
|---|---:|
| `tests.test_r222_control_manifest_leakage_scan` | `3/3` |
| `tests.test_r221_router_control_manifests` | `5/5` |

## Boundary

The scan checks model-visible control inputs and schema-visible fields for forbidden answer, correctness, task-id, and audit fields. It does not run any model.

## Interpretation

R222 clears the manifest-level leakage gate for all four controls. This does not authorize API; it only means the control artifacts are safe enough for local adapter dry-runs.
