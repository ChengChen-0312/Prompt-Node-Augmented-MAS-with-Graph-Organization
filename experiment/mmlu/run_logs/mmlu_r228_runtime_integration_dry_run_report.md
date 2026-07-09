# R228 Runtime Integration Dry-Run

**Claim boundary**: Integration dry-run only; no API and no accuracy claim.

## Result

- Input files: `5`
- Records: `335`
- Would switch: `106`
- Leakage violations: `0`
- Missing required fields: `0`
- Variants: `{'abstain_only_router': 67, 'always_switch_to_objective': 67, 'node_only_no_promptedge_text': 67, 'proposed_router_final': 67, 'random_switch_labels_same_rate': 67}`
- Fallback reasons: `{'router_abstain': 229, 'router_switch': 106}`

## Verification

| Test | Result |
|---|---:|
| `tests.test_r228_runtime_integration_dry_run` | `4/4` |

## Boundary

This dry-run validates local decision logging only. It does not run an LLM or compare correctness.

## Interpretation

R228 closes the local integration logging gap: proposed/control variants can produce uniform runtime-style decision logs with no missing required fields. Accuracy and cost-superiority remain untested.
