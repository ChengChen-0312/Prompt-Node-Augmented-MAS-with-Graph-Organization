# R211 Router-Final PromptEdge Schema Dry-Run

**Claim boundary**: schema and dry-run only. No API evaluation, no accuracy claim, and no claim that router-final improves over ARG-Designer.

## Code Changes

- Added router-final schema generation to `experiment/mmlu/export_promptedge_targets.py`.
- Added `tests/test_r211_mmlu_router_final_schema.py`.

## What The Schema Adds

Each exported PromptEdge target now contains:

- `schema_version`: `r211_router_final_v1`
- `target_kind`: `router_final_or_abstain`
- `router_action`: `abstain`
- `target_option_label`: `NONE`
- dynamic `allowed_option_labels`, e.g. `A/B/C/D/NONE`
- `edge_permission_labels`: `read/write/forward`
- `promptedge_text_policy.edge_text_as_prompt`: `true`
- forbidden model-visible fields: answer/gold/correctness/task-id/audit fields

This matches the current evidence boundary: the target teaches preserve-safe router-final abstention, not answer-changing override.

## Dry-Run Result

Generated manifest:

`experiment/mmlu/promptedge_targets/mmlu_r211_router_final_targets.jsonl`

| Check | Result |
|---|---:|
| Exported rows | `403` |
| Missing router-final schema | `0` |
| Schema version `r211_router_final_v1` | `403/403` |
| Router action `abstain` | `403/403` |
| Allowed labels `A/B/C/D/NONE` | `403/403` |
| Leakage violations | `0` |

## Verification

| Test | Result |
|---|---:|
| `tests.test_r211_mmlu_router_final_schema` | `2/2` |
| `tests.test_r183_mmlu_promptedge_target_export` | `3/3` |
| `tests.test_r182_mmlu_promptedge_topology` | `3/3` |

## Interpretation

R211 closes a schema gap: PromptEdge-as-edge-text and router-final abstention are now represented in the training/export manifest. It does not yet solve the SCI-Q2 blocker because all labels are still preserve-safe abstain labels. The next method step must add a leakage-checked objective-safety or router-final activation target before any API evaluation.

## Next

R212 should run a leakage scan over router-final/objective-safety features and decide which fields can become model-visible training inputs.
