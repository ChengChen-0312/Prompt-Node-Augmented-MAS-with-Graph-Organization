# MMLU Transfer Evaluation Adapter

**Date**: 2026-07-08
**Status**: adapter prepared; no accuracy claim

## What Changed

- Added `experiment/mmlu/transfer_dataset.py` so fixed JSONL transfer records can be evaluated through the same `record_to_input`, `record_to_target_answer`, and `postprocess_answer` contract used by ARG-Designer-style MMLU evaluation.
- Extended `experiment/mmlu/evaluate_mmlu.py` with:
  - `--transfer_jsonl`
  - `--task_split_path`
  - `--output_file`
- The evaluator can now write per-task JSONL detail records with task id, subject, question, gold answer, raw answer, parsed answer, correctness, decision method, and LLM name.

## Fixed Transfer Split

- Records: `experiment/mmlu/mmlu_stem_transfer100.jsonl`
- Split manifest: `experiment/mmlu/task_split_mmlu_stem_transfer100.json`
- Summary: `experiment/mmlu/res_logs/mmlu_stem_transfer_split_summary.json`

The split has `100` A-D multiple-choice STEM tasks from `15` subjects. This is still data and adapter preparation only.

## Reproduction Command Template

Run this only after the same-model API quota is restored and a compatible MMLU ARG-Designer checkpoint is available.

```bash
cd /Users/chencheng/Downloads/论文/ARG-Designer-main
set -a
source /Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env
set +a
.venv/bin/python experiment/mmlu/evaluate_mmlu.py \
  --transfer_jsonl experiment/mmlu/mmlu_stem_transfer100.jsonl \
  --task_split_path experiment/mmlu/task_split_mmlu_stem_transfer100.json \
  --llm_name gpt-4o-2024-08-06 \
  --decision_method FinalRefer \
  --model_path <MMLU_ARGDESIGNER_MODEL_PATH> \
  --limit_questions 100 \
  --eval_batch_size 4 \
  --output_file experiment/mmlu/mmlu_stem_transfer100_arg_baseline_results.jsonl \
  --summary_log_file experiment/mmlu/res_logs/mmlu_stem_transfer100_arg_baseline_summary.jsonl
```

## Current Blockers

1. The same `gpt-4o-2024-08-06` API quota blocker remains for valid same-model evaluation.
2. No MMLU-specific ARG-Designer checkpoint was found under the current ARG-Designer workspace during the R046 check; `experiment/aqua/output` exists, but it is AQuA-specific.
3. PromptNode transfer validation still needs matched ARG and PromptNode traces on this fixed split before any cross-dataset claim is defensible.

## Claim Boundary

R046 does not add any accuracy, robustness, or generalization claim. It only removes an engineering blocker by making the MMLU STEM100 transfer split loadable by the local MMLU evaluator.
