# R243 R238 Control Comparison

**Claim boundary**: Offline control comparison only; no API, no superiority claim, and no SCI-Q2 readiness claim.

| Variant | Acc | Baseline | Switches | Fix/Harm |
|---|---:|---:|---:|---:|
| `abstain_only_router` | `51/67` | `51/67` | `0` | `0/0` |
| `always_switch_to_objective` | `57/67` | `51/67` | `67` | `8/2` |
| `node_only_no_promptedge_text` | `57/67` | `51/67` | `10` | `6/0` |
| `proposed_conservative_router` | `57/67` | `51/67` | `10` | `6/0` |
| `random_switch_labels_same_rate` | `47/67` | `51/67` | `10` | `0/4` |

## Claim Flags

- Beats abstain accuracy: `True`
- Beats random accuracy: `True`
- Beats always accuracy: `False`
- Lower harm than always: `True`
- Beats node-only accuracy: `False`
- Edge-text effect supported: `False`

## Verification

| Test | Result |
|---|---:|
| `tests.test_r243_control_comparison` | `1/1` |
| `tests.test_r242_fit_abstention_policy` | `3/3` |

## Interpretation

The conservative policy supports the abstention-boundary claim offline: it beats abstain and random, and matches always-switch accuracy with fewer harms. It does not support a PromptEdge-text-specific claim because node-only has the same decisions and score.
