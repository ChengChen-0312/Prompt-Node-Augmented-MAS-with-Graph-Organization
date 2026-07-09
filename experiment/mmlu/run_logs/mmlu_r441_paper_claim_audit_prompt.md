# R441 External Paper Claim Audit Prompt

Audit every number and comparison in the paper against the raw/result JSON files. Do not use executor summaries as evidence except as file lists.

## Files To Inspect

- `paper/main.tex`
- `paper/sections/0_abstract.tex`
- `paper/sections/1_introduction.tex`
- `paper/sections/2_related_work.tex`
- `paper/sections/3_method.tex`
- `paper/sections/4_experimental_setup.tex`
- `paper/sections/5_results.tex`
- `paper/sections/6_case_studies.tex`
- `paper/sections/7_limitations.tex`
- `paper/sections/8_conclusion.tex`
- `paper/references.bib`
- `experiment/aqua/res_logs/aqua_tail34_r271_final_claim_table_summary.json`
- `experiment/mmlu/res_logs/mmlu_r321_paper_evidence_table_and_training_gate_summary.json`
- `experiment/mmlu/res_logs/mmlu_r396_larger_mixed_nonmath_fresh_analysis_summary.json`
- `experiment/mmlu/res_logs/mmlu_r414_definition_challenge_gate_analysis_summary.json`
- `experiment/mmlu/res_logs/mmlu_r419_lifecycle_trace_replay_summary.json`
- `experiment/mmlu/res_logs/mmlu_r426_update_cost_table_with_stem_probe_and_goal_audit_summary.json`
- `experiment/mmlu/res_logs/mmlu_r440_paper_claim_number_static_audit_summary.json`

## Required Output

Return PASS/WARN/FAIL with file:line evidence and concrete fixes.