# Prompt-Node-Augmented MAS with Graph Organization

This repository contains the local research code, experiment ledgers, and manuscript artifacts for a PromptNode-Augmented multi-agent system study built on top of ARG-Designer.

The current paper direction is:

> PromptNode as first-class graph-organization virtual nodes for multi-agent LLM reasoning, with typed PromptEdges, read/write/forward permissions, lifecycle actions, and conservative audit-clean evaluation.

## Current Evidence Snapshot

- AQuA audit-clean: PromptNode `31/31` vs ARG `28/31`.
- AQuA conservative remove-task114: PromptNode `30/30` vs ARG `28/30`.
- MMLU STEM transfer: PromptNode `95/97` vs ARG `88/97`, fix/harm `7/0`.
- Mixed non-STEM transfer: `41/48` vs `41/48`; this supports no-harm only, not broad non-math improvement.
- DefinitionChallenge: `22/24` vs `21/24`, fix/harm/wrong-forward `1/0/0`.

See `paper/artifacts/current_status_digest.md` for the latest compact status.

## Important Boundaries

- Do not claim the manuscript is submission-ready yet.
- External experiment, paper-claim, and citation audits are still pending.
- PDF compilation is blocked until a local TeX engine is available.
- Official SCI/JCR quartile verification for JAIR/KAIS is still pending.
- API keys and `.env` files must never be committed.

## Repository Layout

- `experiment/`: ARG-Designer baseline code, PromptNode experiment scripts, result summaries, and run ledgers.
- `paper/`: manuscript draft, tables, appendix, and artifact planning files.
- `tests/`: local regression tests for experiment accounting, manuscript integrity, and packaging checks.
- `datasets/`, `mas_framework/`: baseline framework support code inherited from ARG-Designer.
- `figures/`: generated figure/table artifacts used by the manuscript draft.

## Local Verification

The latest upload preparation ran:

```bash
python -m unittest tests.test_r449_next_local_improvement_or_external_audit tests.test_r450_submission_gap_backlog tests.test_r451_journal_scope_gap_matrix tests.test_r452_five_run_goal_audit_and_compile_probe tests.test_r453_appendix_noise_audit_pack tests.test_r454_reproducibility_artifact_index tests.test_r455_full_local_smoke_after_appendix_artifact tests.test_r456_next_goal_audit_or_external_review_decision tests.test_r457_static_manuscript_audit_after_appendix tests.test_r458_caption_table_reference_polish tests.test_r459_updated_full_local_smoke_after_polish tests.test_r460_manuscript_status_snapshot_after_polish tests.test_r461_five_run_goal_audit_after_polish tests.test_r462_journal_template_probe tests.test_r463_source_package_manifest tests.test_r464_external_audit_authorization_checklist tests.test_r465_local_smoke_after_source_and_audit_checklists tests.test_r466_five_run_goal_audit_after_package_checklists tests.test_r467_jcr_quartile_verification_plan tests.test_r468_submission_readiness_matrix tests.test_r469_local_smoke_after_jcr_readiness tests.test_r470_current_status_digest tests.test_r471_five_run_goal_audit_after_readiness_planning tests.test_r472_latex_environment_options tests.test_r473_compile_command_harness tests.test_r474_local_smoke_after_latex_harness
```

Expected result: `26 tests OK`.

## Baseline Attribution

This work uses ARG-Designer as the main baseline and code foundation:

```bibtex
@inproceedings{li2026assemble,
  title={Assemble your crew: Automatic multi-agent communication topology design via autoregressive graph generation},
  author={Li, Shiyuan and Liu, Yixin and Wen, Qingsong and Zhang, Chengqi and Pan, Shirui},
  booktitle={Proceedings of the AAAI Conference on Artificial Intelligence},
  volume={40},
  number={28},
  pages={23142--23150},
  year={2026}
}
```
