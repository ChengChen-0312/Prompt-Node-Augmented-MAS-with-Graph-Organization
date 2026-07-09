# Reproducibility Artifact Index

This index records how to locate the current evidence package for the PromptNode-Augmented MAS paper draft.

## Model And Environment

- Main API model for fresh evidence runs: `gpt-4o-2024-08-06`.
- ARG-Designer is the primary baseline and should be run with matched settings wherever fresh API reproduction is needed.
- API environment file path: `/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env`.
- API key values are intentionally redacted and must not be committed, printed, or pasted into manuscripts.

## Primary Result Files

- `experiment/aqua/res_logs/aqua_tail34_r271_final_claim_table_summary.json`: AQuA official and audit-clean claim table.
- `experiment/mmlu/res_logs/mmlu_r321_paper_evidence_table_and_training_gate_summary.json`: MMLU STEM main97 evidence and training-gate status.
- `experiment/mmlu/res_logs/mmlu_r396_larger_mixed_nonmath_fresh_analysis_summary.json`: Mixed non-STEM no-harm boundary.
- `experiment/mmlu/res_logs/mmlu_r414_definition_challenge_gate_analysis_summary.json`: Targeted DefinitionChallenge positive transfer result.
- `experiment/mmlu/res_logs/mmlu_r426_update_cost_table_with_stem_probe_and_goal_audit_summary.json`: Cost table with MMLU STEM probe-estimate caveat.
- `experiment/mmlu/res_logs/mmlu_r453_appendix_noise_audit_pack_summary.json`: Audit-clean appendix manifest.

## Audit-Clean Policy

- Do not edit benchmark files silently.
- Report official and audit-clean columns side by side.
- Do not train or distill on corrected test labels.
- Keep AQuA task_59/task_139/task_228 and MMLU audited items in appendix-only handling.

## Local Verification Commands

- `python -m unittest tests.test_r440_paper_claim_number_static_audit`
- `python -m unittest tests.test_r447_local_smoke_after_tables`
- `python -m unittest tests.test_r452_five_run_goal_audit_and_compile_probe`
- `python -m unittest tests.test_r453_appendix_noise_audit_pack`
- `python -m unittest tests.test_r454_reproducibility_artifact_index`

## Pending External Checks

- External experiment-integrity audit.
- External paper-claim audit.
- External citation-context audit.
- PDF compile and visual inspection once a LaTeX engine is available.
