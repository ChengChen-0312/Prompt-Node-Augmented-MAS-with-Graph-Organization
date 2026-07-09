# R241 Abstention Policy Feature Table

**Claim boundary**: Feature-table export only; no API, no trained-policy claim, and no SCI-Q2 readiness claim.

- Rows: `67`
- Train/frozen: `33/34`
- Beneficial switch labels: `8`
- Harmful switch labels: `2`
- Clean harm-if-switch labels: `1`
- Missing source: `0`

## Verification

| Test | Result |
|---|---:|
| `tests.test_r241_abstention_feature_table` | `3/3` |
| `tests.test_r238_conservative_manifest_export` | `4/4` |

## Boundary

Feature columns are label-free and model-visible. Labels, true answers, and clean/noisy audit tags are only for training/evaluation.
