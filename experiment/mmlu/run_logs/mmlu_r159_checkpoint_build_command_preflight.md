# R159 MMLU Checkpoint Build Command Preflight

**Claim boundary**: checkpoint build command preflight only; no API run, no checkpoint training, no transfer result, and no SCI-Q2 readiness claim

## Command

```bash
MMLU_DATA_ROOT=/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/datasets/MMLU .venv/bin/python experiment/mmlu/finetune_mmlu.py --pretrain --llm_name gpt-4o-2024-08-06 --num_iterations 10 --batch_size 4 --model_output_dir /Users/chencheng/Downloads/论文/ARG-Designer-main/experiment/mmlu/output/mmlu_arg_base_model_r159 --no_timestamp_output_dir --cold_start_dir /Users/chencheng/Downloads/论文/ARG-Designer-main/experiment/ColdStartData_mmlu --finetune_data_dir /Users/chencheng/Downloads/论文/ARG-Designer-main/experiment/FinetuneData_mmlu --task_split_file /Users/chencheng/Downloads/论文/ARG-Designer-main/experiment/mmlu/task_split_mmlu.json
```

## Bounded Run Settings

- No API run: `True`
- R158 finetune dry-run ready: `True`
- LLM name: `gpt-4o-2024-08-06`
- Num iterations: `10`
- Batch size: `4`
- Planned training sample count: `40`
- Uses local MMLU data root: `True`

## Expected Artifacts

- `/Users/chencheng/Downloads/论文/ARG-Designer-main/experiment/mmlu/output/mmlu_arg_base_model_r159/configuration.txt`
- `/Users/chencheng/Downloads/论文/ARG-Designer-main/experiment/mmlu/output/mmlu_arg_base_model_r159/best_model.pth`
- `/Users/chencheng/Downloads/论文/ARG-Designer-main/experiment/mmlu/output/mmlu_arg_base_model_r159/ef_best_model.pth`

## Stop Conditions

- API quota or authentication failure
- MMLU dev data root unavailable
- task split invalid
- pretrain or finetune loss becomes NaN
- expected checkpoint artifacts missing after run

## Next Gate

- Checkpoint training run: `False`
- Transfer API allowed next: `False`
- Broad API allowed next: `False`
- Next protocol: `r160_goal_audit_r156_r160`

## Interpretation

R159 defines the exact bounded command for building a compatible MMLU ARG checkpoint. It intentionally does not run the command. R160 must audit the R156-R160 window before any API-backed checkpoint build proceeds.
