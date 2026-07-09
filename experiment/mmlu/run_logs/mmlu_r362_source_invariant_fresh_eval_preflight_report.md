# R362 Source-Invariant Fresh Eval Preflight

**Claim boundary**: R362 builds a fresh MMLU manifest for ARG baseline and PromptNode candidate API calls. It does not execute API; the R360 source-invariant gate will be applied after candidate responses are collected.

- Tasks: `48`
- API records: `96`
- Variants: `{'arg_baseline_direct_api': 48, 'promptnode_candidate_api': 48}`
- Leakage pass: `True`
- API execution authorized next: `True`
- Next required run: `R363_source_invariant_fresh_eval_api_execution`
