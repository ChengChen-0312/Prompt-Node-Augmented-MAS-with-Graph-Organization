# R350 Goal Audit After Fresh Tool PromptNode Preflight

**Claim boundary**: R350 is the five-iteration audit after R345-R349. R347 replay is positive, but R349 shows zero fresh tool coverage, so API execution is paused until the PromptNode library covers fresh tasks.

## Alignment

- `still_aligned_with_sci_q2_goal`: `True`
- `arg_baseline_preserved`: `True`
- `r347_replay_positive`: `True`
- `r348_policy_frozen`: `True`
- `r349_fresh_split_ready`: `True`
- `fresh_tool_coverage_gap_detected`: `True`
- `overclaiming_blocked`: `True`

## Claim Permissions

- `r347_replay_mechanism_evidence_allowed`: `True`
- `fresh_api_execution_allowed_now`: `False`
- `fresh_coverage_expansion_allowed`: `True`
- `main_paper_claim_allowed`: `False`
- `sci_q2_ready`: `False`

## Course Correction

- Do not run fresh API while the frozen tool policy forwards zero candidates.
- Expand PromptNode coverage with general nonmath and broader STEM nodes before API execution.
- Keep R347 as positive mechanism replay, not a submission-level main result.
- Require a fresh preflight with nonzero coverage and no leakage before spending API.

- Next required run: `R351_fresh_coverage_promptnode_expansion_design`
