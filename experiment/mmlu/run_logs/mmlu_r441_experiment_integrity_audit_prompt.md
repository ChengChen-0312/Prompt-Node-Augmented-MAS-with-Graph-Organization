# R441 External Experiment Integrity Audit Prompt

Audit whether the reported PromptNode-Augmented MAS results are grounded in result files, use ARG-Designer as the baseline, and avoid broad nonmath/general claims.

## Files To Inspect

- `experiment/aqua/res_logs/aqua_tail34_r271_final_claim_table_summary.json`
- `experiment/mmlu/res_logs/mmlu_r321_paper_evidence_table_and_training_gate_summary.json`
- `experiment/mmlu/res_logs/mmlu_r396_larger_mixed_nonmath_fresh_analysis_summary.json`
- `experiment/mmlu/res_logs/mmlu_r414_definition_challenge_gate_analysis_summary.json`
- `experiment/mmlu/res_logs/mmlu_r419_lifecycle_trace_replay_summary.json`
- `experiment/mmlu/res_logs/mmlu_r426_update_cost_table_with_stem_probe_and_goal_audit_summary.json`
- `experiment/mmlu/res_logs/mmlu_r440_paper_claim_number_static_audit_summary.json`

## Required Output

Return PASS/WARN/FAIL with file:line evidence and concrete fixes.