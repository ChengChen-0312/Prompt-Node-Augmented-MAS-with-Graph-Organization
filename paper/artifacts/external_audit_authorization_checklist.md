# External Audit Authorization Checklist

These payloads contain unpublished manuscript and result material. Do not transmit them to a browser, API, or external reviewer without explicit user confirmation.

- Transmission performed: `False`
- Requires confirmation before transmission: `True`

## Payloads

### experiment_integrity_audit

- Payload: `experiment/mmlu/run_logs/mmlu_r445_experiment_integrity_external_payload.md`
- Expected review output: `experiment/mmlu/run_logs/mmlu_r445_experiment_integrity_external_review.md`
- Purpose: Check result provenance, no fake ground truth, no phantom results, and claim scope.

### paper_claim_audit

- Payload: `experiment/mmlu/run_logs/mmlu_r445_paper_claim_external_payload.md`
- Expected review output: `experiment/mmlu/run_logs/mmlu_r445_paper_claim_external_review.md`
- Purpose: Check every number/comparison in the manuscript against raw/result files.

### citation_context_audit

- Payload: `experiment/mmlu/run_logs/mmlu_r445_citation_context_external_payload.md`
- Expected review output: `experiment/mmlu/run_logs/mmlu_r445_citation_context_external_review.md`
- Purpose: Check citation metadata and whether citation contexts are supported.

## Confirmation Boundary

- A future turn must explicitly authorize sending these payload files to an external reviewer/backend.
- Authorization to continue local work is not authorization to transmit unpublished manuscript or result payloads.
- After review, imported outputs must be saved to the expected_review_md paths and audited before claims are authorized.
