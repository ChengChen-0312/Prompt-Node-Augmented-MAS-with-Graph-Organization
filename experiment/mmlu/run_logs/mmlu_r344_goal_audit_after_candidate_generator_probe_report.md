# R344 Goal Audit After Candidate Generator Probe

**Claim boundary**: R344 is the five-iteration audit after R339-R343. It keeps the work aligned with the SCI-Q2 goal by blocking same-design prompt-only verifier expansion and redirecting to general, tool-backed PromptNodes.

## Alignment

- `still_aligned_with_sci_q2_goal`: `True`
- `arg_baseline_preserved`: `True`
- `candidate_design_preflight_done`: `True`
- `bounded_probe_executed`: `True`
- `same_prompt_only_path_blocked`: `True`
- `promptnode_not_dataset_patch`: `True`
- `overclaiming_blocked`: `True`

## Claim Permissions

- `tool_backed_promptnode_design_allowed`: `True`
- `symbolic_promptedge_design_allowed`: `True`
- `more_api_same_prompt_design_allowed`: `False`
- `answer_bearing_generator_improvement_claim_allowed`: `False`
- `broad_general_promptnode_claim_allowed`: `False`
- `sci_q2_ready`: `False`

## Course Correction

- Replace prompt-only answer-bearing verifier expansion with tool-backed or symbolic PromptNodes.
- Keep virtual nodes general: verifier families must be selected by task features, not task IDs or known labels.
- Treat PromptEdge as executable contracts: required evidence, option-by-option check, and reject-if-unverified.
- Run a no-API design/preflight before spending more API on prospective transfer.

- Next required run: `R345_tool_backed_promptnode_verifier_design`
