# R444 External Audit Execution Plan

**Claim boundary**: R444 orders the external audit execution and output capture paths. It does not execute external reviews.

## Execution Order

- `experiment_integrity_audit`: prompt=`experiment/mmlu/run_logs/mmlu_r441_experiment_integrity_audit_prompt.md`, output=`experiment/mmlu/run_logs/mmlu_r445_experiment_integrity_external_review.md`
- `paper_claim_audit`: prompt=`experiment/mmlu/run_logs/mmlu_r441_paper_claim_audit_prompt.md`, output=`experiment/mmlu/run_logs/mmlu_r445_paper_claim_external_review.md`
- `citation_context_audit`: prompt=`experiment/mmlu/run_logs/mmlu_r441_citation_context_audit_prompt.md`, output=`experiment/mmlu/run_logs/mmlu_r445_citation_context_external_review.md`

- Next required run: `R445_external_audit_execution_or_manual_import`
