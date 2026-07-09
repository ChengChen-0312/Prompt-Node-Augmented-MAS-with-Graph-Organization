# R144 Calibrated Repair Final-Gate Implementation Pre-Smoke

**Claim boundary**: implementation pre-smoke only; no API, accuracy, broad evaluation, transfer, robustness, or SCI-readiness claim

- Pre-smoke only: `True`
- No API run: `True`
- Decision method: `CalibratedEdgePromptRepairContractFinalRefer`
- Decision method registered: `True`
- Close forwarded repair accepted: `True`
- Direct contradiction rejected: `True`
- Large distance rejected: `True`
- R143 offline gate passed: `True`
- Same two-switch-task smoke allowed next: `True`
- R145 goal audit required before API: `True`
- Broad API allowed next: `False`
- Next protocol: `r145_goal_audit_before_calibrated_api_smoke`

## Evaluate Command After R145 Audit

```bash
.venv/bin/python experiment/aqua/evaluate_aqua.py --dataset_path datasets/AQuA/AQuA.jsonl --task_split_path experiment/aqua/task_split_aqua_tail34_r136_edge_prompt_repair_switches.json --llm_name gpt-4o-2024-08-06 --decision_method CalibratedEdgePromptRepairContractFinalRefer --output_file experiment/aqua/aqua_tail34_r146_calibrated_repair_switch_results.jsonl --summary_log_file experiment/aqua/res_logs/aqua_tail34_r146_calibrated_repair_switch_summary.jsonl --eval_batch_size 1 --forced_template_candidate_jsonl experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl --forced_template_candidate_rank 5
```

## Interpretation

R144 registers the calibrated repair final decision method and verifies its local accept/reject behavior. Because the user's five-run audit rule is active, the R145 goal audit must run before launching the bounded API smoke.
