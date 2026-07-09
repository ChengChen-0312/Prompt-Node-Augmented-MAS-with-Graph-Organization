# R099 Task250 Template Rank Sweep Protocol

**Claim boundary**: pre-registered task250 rank2-5 template sweep; no result or accuracy claim

- Task: `task_250`
- Split: `experiment/aqua/task_split_aqua_tail34_task250_smoke.json` with indices `[250]`
- Model: `gpt-4o-2024-08-06`
- Candidate file: `experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl`
- Sweep ranks: `[2, 3, 4, 5]`
- Excluded ranks: `[1]`
- Desired prediction: `E`
- Full tail34: `False`

## Frozen Commands

### Rank 2

```bash
.venv/bin/python experiment/aqua/evaluate_aqua.py --dataset_path datasets/AQuA/AQuA.jsonl --task_split_path experiment/aqua/task_split_aqua_tail34_task250_smoke.json --llm_name gpt-4o-2024-08-06 --decision_method RouterContractFinalRefer --output_file experiment/aqua/aqua_tail34_r100_forced_template_rank2_task250_results.jsonl --summary_log_file experiment/aqua/res_logs/aqua_tail34_r100_forced_template_rank2_task250_summary.jsonl --eval_batch_size 1 --forced_template_candidate_jsonl experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl --forced_template_candidate_rank 2
```

### Rank 3

```bash
.venv/bin/python experiment/aqua/evaluate_aqua.py --dataset_path datasets/AQuA/AQuA.jsonl --task_split_path experiment/aqua/task_split_aqua_tail34_task250_smoke.json --llm_name gpt-4o-2024-08-06 --decision_method RouterContractFinalRefer --output_file experiment/aqua/aqua_tail34_r100_forced_template_rank3_task250_results.jsonl --summary_log_file experiment/aqua/res_logs/aqua_tail34_r100_forced_template_rank3_task250_summary.jsonl --eval_batch_size 1 --forced_template_candidate_jsonl experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl --forced_template_candidate_rank 3
```

### Rank 4

```bash
.venv/bin/python experiment/aqua/evaluate_aqua.py --dataset_path datasets/AQuA/AQuA.jsonl --task_split_path experiment/aqua/task_split_aqua_tail34_task250_smoke.json --llm_name gpt-4o-2024-08-06 --decision_method RouterContractFinalRefer --output_file experiment/aqua/aqua_tail34_r100_forced_template_rank4_task250_results.jsonl --summary_log_file experiment/aqua/res_logs/aqua_tail34_r100_forced_template_rank4_task250_summary.jsonl --eval_batch_size 1 --forced_template_candidate_jsonl experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl --forced_template_candidate_rank 4
```

### Rank 5

```bash
.venv/bin/python experiment/aqua/evaluate_aqua.py --dataset_path datasets/AQuA/AQuA.jsonl --task_split_path experiment/aqua/task_split_aqua_tail34_task250_smoke.json --llm_name gpt-4o-2024-08-06 --decision_method RouterContractFinalRefer --output_file experiment/aqua/aqua_tail34_r100_forced_template_rank5_task250_results.jsonl --summary_log_file experiment/aqua/res_logs/aqua_tail34_r100_forced_template_rank5_task250_summary.jsonl --eval_batch_size 1 --forced_template_candidate_jsonl experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl --forced_template_candidate_rank 5
```

## Interpretation Rule

This protocol is only allowed to test whether a non-rank1 explicit PromptNode template can recover the clean R095 `task_250` switch. It does not establish held-out accuracy.
