# R136 Edge-Prompt Repair-Field Prompting Pre-Smoke

**Claim boundary**: pre-smoke protocol only; prompt-field update, no API, accuracy, cost, transfer, or robustness result

- Pre-smoke only: `True`
- No API run: `True`
- PN_Verifier repair audit prompted: `True`
- PN_Router repair fields prompted: `True`
- Repair field names: `['REPAIR_OPTION', 'REPAIR_BINDING_STATUS', 'REPAIR_CONFIDENCE', 'REPAIR_DISTANCE_RATIO']`
- R134 repair gate ready: `True`
- R135 status: `aligned_continue_without_broad_api`
- R135 clean gate still not met: `True`
- Decision method: `EdgePromptRepairContractFinalRefer`
- Switch tasks: `['task_108', 'task_250']`
- Fallback tasks: `['task_8', 'task_188']`
- Task split path: `experiment/aqua/task_split_aqua_tail34_r136_edge_prompt_repair_switches.json`
- Same-four-task smoke allowed next: `True`
- Broad API allowed next: `False`

## Evaluate Command

```bash
.venv/bin/python experiment/aqua/evaluate_aqua.py --dataset_path datasets/AQuA/AQuA.jsonl --task_split_path experiment/aqua/task_split_aqua_tail34_r136_edge_prompt_repair_switches.json --llm_name gpt-4o-2024-08-06 --decision_method EdgePromptRepairContractFinalRefer --output_file experiment/aqua/aqua_tail34_r136_edge_prompt_repair_switch_results.jsonl --summary_log_file experiment/aqua/res_logs/aqua_tail34_r136_edge_prompt_repair_switch_summary.jsonl --eval_batch_size 1 --forced_template_candidate_jsonl experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl --forced_template_candidate_rank 5
```

## Interpretation

R136 updates the PromptNode prompt path so PN_Verifier can produce a repair-candidate audit and PN_Router can emit the machine-readable repair fields consumed by R134. This is still pre-smoke only. The next API step is bounded to the two switch tasks with ARG fallback guards on task_8 and task_188.
