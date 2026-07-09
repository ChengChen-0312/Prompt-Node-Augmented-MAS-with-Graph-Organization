# R138 Router Repair-Forwarding Prompt Hardening

**Claim boundary**: prompt-hardening protocol only; no API, accuracy, clean-recovery, transfer, robustness, or SCI-readiness claim

- Prompt hardening only: `True`
- No API run: `True`
- Prompt as first-class edge: `True`
- Node-only PromptNode sufficient: `False`
- R137 forwarding gap confirmed: `True`
- PN_Verifier repair status values hardened: `True`
- PN_Verifier forbids exact/equivalent as repair status: `True`
- PN_Router repair forwarding required: `True`
- SUPPORTED_OPTION NONE can coexist with REPAIR_OPTION: `True`
- PN_Router does not reset repair fields to NONE: `True`
- No task-id routing: `True`
- Multi-dataset transfer still required: `True`
- Decision method: `EdgePromptRepairContractFinalRefer`
- Switch tasks: `['task_108', 'task_250']`
- Fallback tasks: `['task_8', 'task_188']`
- Same two-switch-task smoke allowed next: `True`
- Broad API allowed next: `False`

## Evaluate Command

```bash
.venv/bin/python experiment/aqua/evaluate_aqua.py --dataset_path datasets/AQuA/AQuA.jsonl --task_split_path experiment/aqua/task_split_aqua_tail34_r136_edge_prompt_repair_switches.json --llm_name gpt-4o-2024-08-06 --decision_method EdgePromptRepairContractFinalRefer --output_file experiment/aqua/aqua_tail34_r139_edge_prompt_repair_forwarding_switch_results.jsonl --summary_log_file experiment/aqua/res_logs/aqua_tail34_r139_edge_prompt_repair_forwarding_switch_summary.jsonl --eval_batch_size 1 --forced_template_candidate_jsonl experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl --forced_template_candidate_rank 5
```

## Interpretation

R138 treats the repair prompt as an edge policy between PN_Verifier and PN_Router. It fixes the R137 interface gap by requiring the router to forward explicit verifier repair candidates even when the supported exact option remains NONE. This is not a result claim; it only permits one more bounded two-switch-task smoke before any broader evaluation.
