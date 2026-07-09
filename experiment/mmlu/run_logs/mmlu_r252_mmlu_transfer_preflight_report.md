# R252 MMLU Transfer Diagnostic Preflight

**Claim boundary**: Preflight only; no API execution, no transfer accuracy claim, and no SCI-Q2 readiness claim.

- Model: `gpt-4o-2024-08-06`
- Records/tasks: `80` / `16`
- Variant counts: `{'abstain_keep_arg': 16, 'arg_baseline_fixed': 16, 'node_only_no_promptedge_text': 16, 'plain_requery': 16, 'proposed_promptnode_promptedge': 16}`
- API-required records: `48`
- Leakage violations: `0`
- Estimated cost: `$0.109770` / cap `$0.450000`
- Variant balance pass: `True`
- Preflight pass: `True`
- Authorized API next: `True`

## Boundary

This run only materializes leakage-safe manifests and cost estimates. It does not call any model or support a transfer-improvement claim.
