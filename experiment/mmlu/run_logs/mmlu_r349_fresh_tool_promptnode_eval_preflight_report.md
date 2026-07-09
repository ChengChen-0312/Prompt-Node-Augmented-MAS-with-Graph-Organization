# R349 Fresh Tool PromptNode Eval Preflight

**Claim boundary**: R349 builds a fresh 48-task MMLU manifest for the policy frozen at R347. It performs local tool preflight only; API execution is deferred to the next non-audit run.

- Tasks: `48`
- Family counts: `{'mmlu_nonstem': 24, 'mmlu_stem': 24}`
- API calls planned: `48`
- Local tool forwarded candidates: `0`
- Leakage pass: `True`
- Overlap with excluded tasks: `0`
- Next required run: `R350_goal_audit_after_tool_promptnode_fresh_preflight`
