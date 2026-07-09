# R348 Fresh Tool PromptNode Eval Design

**Claim boundary**: R348 freezes the R345-R347 tool-backed PromptNode policy and designs a fresh MMLU eval that excludes previously used R334/R337 tasks. It is a protocol design only; no API is executed here.

- Policy frozen after: `R347`
- Fresh task plan: `{'mmlu_stem': 24, 'mmlu_nonstem': 24}`
- Planned variants: `['arg_baseline_direct_api', 'frozen_tool_promptnode_local', 'hybrid_arg_plus_tool']`
- API calls planned: `48`

## Frozen Components

- `PN_CoordinateTransformer`
- `PN_FiniteAbelianGroupEnumerator`
- `PN_FiniteFieldDerivativeAnalyzer`
- `PN_RedoxBalanceLinearSolver`
- `PromptEdge reject_if_unparsed_or_inconsistent`
- `PromptEdge forward_exact_single_option_match_only`

- Next required run: `R349_fresh_tool_promptnode_eval_preflight`
