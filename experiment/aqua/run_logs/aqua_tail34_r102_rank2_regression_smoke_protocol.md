# R102 Rank2 Regression Smoke Protocol

**Claim boundary**: pre-registered four-task rank2 regression smoke; no held-out accuracy claim

- Selected rank: `2`
- Split: `experiment/aqua/task_split_aqua_tail34_r102_rank2_regression_smoke.json` with indices `[8, 108, 188, 250]`
- Clean harm guards: `['task_8', 'task_188']`
- Clean recovery targets: `['task_250']`
- Noisy optional targets: `['task_108']`
- Model: `gpt-4o-2024-08-06`
- Full tail34: `False`

## Frozen Command

```bash
.venv/bin/python experiment/aqua/evaluate_aqua.py --dataset_path datasets/AQuA/AQuA.jsonl --task_split_path experiment/aqua/task_split_aqua_tail34_r102_rank2_regression_smoke.json --llm_name gpt-4o-2024-08-06 --decision_method RouterContractFinalRefer --output_file experiment/aqua/aqua_tail34_r103_rank2_regression_smoke_results.jsonl --summary_log_file experiment/aqua/res_logs/aqua_tail34_r103_rank2_regression_smoke_summary.jsonl --eval_batch_size 1 --forced_template_candidate_jsonl experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl --forced_template_candidate_rank 2
```

## Interpretation Rule

This smoke can only decide whether the R101 rank2 hypothesis survives known regression cases. It cannot establish held-out accuracy or SCI-Q2 readiness.
