# R273 MMLU Full24 Transfer Preflight

**Claim boundary**: Preflight only; no API execution, no transfer accuracy claim, and no SCI-Q2 readiness claim.

- Model: `gpt-4o-2024-08-06`
- Records/tasks: `120` / `24`
- Variant counts: `{'abstain_keep_arg': 24, 'arg_baseline_fixed': 24, 'node_only_no_promptedge_text': 24, 'plain_requery': 24, 'proposed_promptnode_promptedge': 24}`
- API-required records: `72`
- Leakage violations: `0`
- Estimated cost: `$0.164730` / cap `$0.250000`
- Variant balance pass: `True`
- Preflight pass: `True`
- Authorized API next: `True`

## Boundary

This run only materializes leakage-safe manifests and cost estimates. It does not call any model or support a transfer-improvement claim.
