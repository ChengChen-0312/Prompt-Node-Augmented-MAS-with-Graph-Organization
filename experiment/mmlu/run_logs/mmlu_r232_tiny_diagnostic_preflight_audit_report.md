# R232 Tiny Diagnostic Preflight Audit

**Claim boundary**: Preflight audit only; no API, no accuracy claim, and no SCI-Q2 readiness claim.

## Result

- Preflight pass: `True`
- API status: `authorized_tiny_diagnostic`
- Records: `20`
- API-required records: `8`
- Estimated cost: `$0.018950` / cap `$0.450000`
- Source missing: `0`
- Model mismatches: `0`
- Leakage rows: `0`
- Prompt SHA mismatches: `0`
- Env has API key: `True`
- Env loaded key names: `['API_KEY', 'BASE_URL', 'DEFAULT_LLM_NAME', 'DEFAULT_PRIMARY_DATASETS', 'OPENAI_API_KEY', 'OPEN_GMAS_COMPLETION_USD_PER_1M_TOKENS', 'OPEN_GMAS_PREFLIGHT_COMPLETION_TOKENS_PER_CALL', 'OPEN_GMAS_PROMPT_USD_PER_1M_TOKENS']`
- Blockers: `[]`
- Warnings: `[]`

## Verification

| Test | Result |
|---|---:|
| `tests.test_r232_tiny_diagnostic_preflight_audit` | `6/6` |
| `tests.test_r231_tiny_diagnostic_runner` | `7/7` |

## Boundary

The audit records only environment key names and booleans. It does not print or store API key values, and it does not call any model.

## Decision

Preflight passes and authorizes only the R233 tiny diagnostic over the preflighted records. It does not authorize a broad API sweep or any superiority claim.
