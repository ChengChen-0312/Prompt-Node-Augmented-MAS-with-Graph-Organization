# R353 Fresh Eval After Coverage Expansion Design

**Claim boundary**: R353 freezes the expanded R352 PromptNode policy and designs a new fresh MMLU eval. R349/R352 are excluded because they were used for coverage development.

- Policy frozen after: `R352`
- Fresh task plan: `{'mmlu_stem': 24, 'mmlu_nonstem': 24}`
- Planned variants: `['arg_baseline_direct_api', 'expanded_tool_promptnode_local', 'hybrid_arg_plus_expanded_tool']`
- API calls planned: `48`
- Next required run: `R354_fresh_eval_after_coverage_expansion_preflight`
