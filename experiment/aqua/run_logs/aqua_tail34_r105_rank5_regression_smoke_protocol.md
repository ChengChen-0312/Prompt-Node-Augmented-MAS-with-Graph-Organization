# R105 Rank5 Regression Smoke Protocol

**Claim boundary**: pre-registered four-task rank5 regression smoke for consensus check; no held-out accuracy claim

- Selected rank: `5`
- Comparison rank: `2`
- Split: `experiment/aqua/task_split_aqua_tail34_r105_rank5_regression_smoke.json` with indices `[8, 108, 188, 250]`
- Clean harm guards: `['task_8', 'task_188']`
- Clean recovery targets: `['task_250']`
- Model: `gpt-4o-2024-08-06`
- Full tail34: `False`

## Frozen Command

```bash
.venv/bin/python experiment/aqua/evaluate_aqua.py --dataset_path datasets/AQuA/AQuA.jsonl --task_split_path experiment/aqua/task_split_aqua_tail34_r105_rank5_regression_smoke.json --llm_name gpt-4o-2024-08-06 --decision_method RouterContractFinalRefer --output_file experiment/aqua/aqua_tail34_r106_rank5_regression_smoke_results.jsonl --summary_log_file experiment/aqua/res_logs/aqua_tail34_r106_rank5_regression_smoke_summary.jsonl --eval_batch_size 1 --forced_template_candidate_jsonl experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl --forced_template_candidate_rank 5
```

## Interpretation Rule

This smoke tests whether rank5 can provide a cleaner partner for rank2-style evidence. It cannot establish held-out accuracy.
