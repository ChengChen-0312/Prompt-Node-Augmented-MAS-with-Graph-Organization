# R233 Tiny API Diagnostic

**Claim boundary**: Tiny pre-registered diagnostic only; not a paper-level accuracy or SCI-Q2 readiness claim.

## Result

- Records: `20`
- Evaluated records: `20`
- API required/executed/errors: `8/8/0`
- Correct: `4`
- Accuracy: `0.2`
- Fixes/harms: `3/4`
- Cost: `$0.018950`
- Prompt/completion tokens: `2638/384`

## By Variant

| Variant | Records | Correct | Accuracy | Fix/Harm | API required |
|---|---:|---:|---:|---:|---:|
| `abstain_only_router` | `4` | `1` | `0.25` | `0/0` | `0` |
| `always_switch_to_objective` | `4` | `1` | `0.25` | `1/1` | `0` |
| `node_only_no_promptedge_text` | `4` | `1` | `0.25` | `1/1` | `4` |
| `proposed_router_final` | `4` | `1` | `0.25` | `1/1` | `4` |
| `random_switch_labels_same_rate` | `4` | `0` | `0.0` | `0/1` | `0` |

## Verification

| Test | Result |
|---|---:|
| `tests.test_r233_tiny_api_diagnostic_executor` | `6/6` |
| `tests.test_r232_tiny_diagnostic_preflight_audit` | `6/6` |

## Boundary

This is a tiny diagnostic over the R232-authorized records only. It is not a broad held-out result.

## Interpretation

The proposed router-final prompt does not beat controls in this diagnostic. `proposed_router_final`, `node_only_no_promptedge_text`, `always_switch_to_objective`, and `abstain_only_router` each score `1/4`, while random-switch scores `0/4`. The proposed variant has `fix/harm=1/1`, so it is not robust enough to expand as-is.
