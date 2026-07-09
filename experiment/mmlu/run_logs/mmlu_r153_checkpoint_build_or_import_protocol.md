# R153 MMLU Checkpoint Build or Import Protocol

**Claim boundary**: checkpoint build/import protocol only; no API run, no checkpoint produced, no transfer result, and no SCI-Q2 readiness claim

## Current Checkpoint State

- Compatible checkpoint present: `False`
- Compatible checkpoint dirs: `[]`
- Finetune script exists: `True`
- Cold-start script exists: `True`
- Evaluator exists: `True`
- Hardcoded path markers: `['/root/ARG-Designer', '../ColdStartData_mmlu', './task_split_mmlu.json']`
- Local task split exists: `False`

## Build or Import Route

- Import route supported: `True`
- Required import files: `['configuration.txt', 'ef_best_model.pth or best_model.pth']`
- Build route: `patch_local_paths_then_coldstart_pretrain_finetune`

## Required Steps

- replace hardcoded /root paths with CLI-configurable local paths
- generate or provide task_split_mmlu.json for dev base/finetune split
- run cold_start_mmlu.py with gpt-4o-2024-08-06 only after API budget is approved
- run finetune_mmlu.py with local data dirs and model output dir
- verify configuration.txt plus ef_best_model.pth before transfer evaluation

## Next Gate

- Transfer API allowed next: `False`
- Broad API allowed next: `False`
- Next protocol: `r154_local_mmlu_checkpoint_path_patch_or_import_stub`
- Next goal audit due: `R155`

## Interpretation

R153 keeps transfer validation blocked until a compatible MMLU ARG checkpoint exists. The existing MMLU scripts are useful, but the finetune/cold-start path still needs local path configurability and a task split manifest before a checkpoint can be built in this workspace.
