# R092 Forced-Template Tail34 Validation Protocol

**Claim boundary**: pre-registered full tail34 forced-template validation protocol, not a result

- Status: `pre_registered_before_full_run`
- Split: `experiment/aqua/task_split_aqua_tail34.json` (`34` tasks)
- Model: `gpt-4o-2024-08-06`
- Forced-template candidate file: `experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl`
- Forced-template rank: `1`
- Frozen gate: `r088_bad_exact_contract_gate`
- ARG baseline reference: `28/34`
- Success gate: `{'minimum_gate_solved': '>=29/34', 'maximum_harm': 0, 'required_decision_field_violations': 0, 'required_same_model': 'gpt-4o-2024-08-06'}`
- Forbidden decision fields: `['audit_label', 'baseline_is_solved', 'clean_label', 'is_solved', 'run_group', 'task_id', 'true_answer']`

## Frozen Run Command

```bash
.venv/bin/python experiment/aqua/evaluate_aqua.py --dataset_path datasets/AQuA/AQuA.jsonl --task_split_path experiment/aqua/task_split_aqua_tail34.json --llm_name gpt-4o-2024-08-06 --decision_method RouterContractFinalRefer --output_file experiment/aqua/aqua_tail34_r092_forced_template_rank1_results.jsonl --summary_log_file experiment/aqua/res_logs/aqua_tail34_r092_forced_template_rank1_summary.jsonl --eval_batch_size 1 --forced_template_candidate_jsonl experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl --forced_template_candidate_rank 1
```

## Interpretation Rule

If the frozen gate does not beat ARG or introduces harm, forced rank-1 templates are not ready as a paper main result; move back to template selection or graph-policy training.
