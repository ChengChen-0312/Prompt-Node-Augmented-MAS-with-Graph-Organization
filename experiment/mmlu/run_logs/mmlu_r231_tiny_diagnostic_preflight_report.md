# R231 Tiny Diagnostic Runner Preflight

**Claim boundary**: Runner preflight only; no API, no accuracy claim, and no SCI-Q2 readiness claim.

## Result

- Model: `gpt-4o-2024-08-06`
- Task ids: `['task_135', 'task_152', 'task_172', 'task_95']`
- Records: `20`
- API-required records: `8`
- Deterministic records: `12`
- Source missing: `0`
- Leakage violations: `0`
- Estimated cost: `$0.018950` / cap `$0.450000`
- Estimated cost within cap: `True`
- Variant counts: `{'abstain_only_router': 4, 'always_switch_to_objective': 4, 'node_only_no_promptedge_text': 4, 'proposed_router_final': 4, 'random_switch_labels_same_rate': 4}`

## Verification

| Test | Result |
|---|---:|
| `tests.test_r231_tiny_diagnostic_runner` | `7/7` |
| `tests.test_r228_runtime_integration_dry_run` | `4/4` |

## Boundary

This run only builds leakage-safe model-visible prompts and cost estimates. It does not call an LLM or score accuracy.

## Interpretation

R231 creates the missing API-runner preflight layer. It keeps `abstain`, `random`, and `always` controls deterministic, while `proposed_router_final` and `node_only_no_promptedge_text` are the only API-required router variants.
