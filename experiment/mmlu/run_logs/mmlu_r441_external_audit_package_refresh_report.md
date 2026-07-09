# R441 External Audit Package Refresh

**Claim boundary**: R441 refreshes external audit prompts and performs the five-run goal checkpoint. It does not execute external reviewer audits.

## Packages

- `experiment_integrity_audit`: `experiment/mmlu/run_logs/mmlu_r441_experiment_integrity_audit_prompt.md`; executed=`False`
- `citation_context_audit`: `experiment/mmlu/run_logs/mmlu_r441_citation_context_audit_prompt.md`; executed=`False`
- `paper_claim_audit`: `experiment/mmlu/run_logs/mmlu_r441_paper_claim_audit_prompt.md`; executed=`False`

## Goal Check

- `still_aligned_with_sci_q2_goal`: `True`
- `complete_initial_paper_draft_now_exists`: `True`
- `arg_designer_remains_main_baseline`: `True`
- `promptnode_virtual_node_not_answer_patch`: `True`
- `audits_not_faked`: `True`
- `submission_blockers_explicit`: `True`

- Next required run: `R442_local_smoke_test_suite`
