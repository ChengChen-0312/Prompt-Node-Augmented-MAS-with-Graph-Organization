# R450 Submission Gap Backlog

**Claim boundary**: R450 converts the current manuscript blockers into an execution backlog. It does not transmit unpublished material, execute external audits, or certify SCI-Q2 readiness.

- Target journals: `JAIR, KAIS`
- External transmission allowed now: `False`
- Requires user confirmation for external transmission: `True`

## Backlog

### B450-001 (P0): external experiment-integrity audit pending

- Evidence: R443/R444/R445 prepared audit packages but no independent review has been executed.
- Required action: Run or import a fresh external review of result provenance before authorizing claims.
- Next run: `R451_or_external_review_import`
- Status: `open`

### B450-002 (P0): external paper-claim audit pending

- Evidence: R440 is only a static local number audit; zero-context claim audit remains pending.
- Required action: Check every manuscript number and comparison against raw/result files using a fresh reviewer.
- Next run: `R451_or_external_review_import`
- Status: `open`

### B450-003 (P0): external citation-context audit pending

- Evidence: R436/R438 built citation metadata and contexts, but no external citation audit is recorded.
- Required action: Verify that each cited paper exists and each citation context is supported.
- Next run: `R451_or_external_review_import`
- Status: `open`

### B450-004 (P1): journal scope matrix missing

- Evidence: R449 selected target journals (JAIR, KAIS) but did not map claims to their scopes.
- Required action: Build a JAIR/KAIS scope-gap matrix and decide the primary framing.
- Next run: `R451_journal_scope_gap_matrix`
- Status: `open`

### B450-005 (P1): latex compile unavailable

- Evidence: R439 found no local latexmk or pdflatex, so PDF compile has not been verified.
- Required action: Install or locate a TeX engine, then compile and inspect the PDF.
- Next run: `R452_compile_probe_or_environment_note`
- Status: `open`

### B450-006 (P1): audit-clean appendix needs finalization

- Evidence: AQuA and MMLU label-noise decisions are recorded in result logs, but the appendix needs final wording.
- Required action: Finalize appendix language for task_59/task_139/task_228/task_114 and MMLU audited items.
- Next run: `R453_appendix_noise_audit_pack`
- Status: `open`

### B450-007 (P2): caption and contribution polish pending

- Evidence: R448 records final caption polish as pending after table integration.
- Required action: Polish captions only after external audits decide which claims survive.
- Next run: `R454_caption_polish_after_audit`
- Status: `blocked_by_external_audits`

### B450-008 (P2): reproducibility artifact packaging pending

- Evidence: Experiment code and ledgers exist, but a reader-facing reproduction README is not yet packaged.
- Required action: Prepare a concise artifact checklist with commands, splits, costs, and audit-clean protocol.
- Next run: `R455_reproducibility_artifact_index`
- Status: `open`

- Paper claim authorized: `False`
- SCI-Q2 ready: `False`
- Next required run: `R451_journal_scope_gap_matrix`
