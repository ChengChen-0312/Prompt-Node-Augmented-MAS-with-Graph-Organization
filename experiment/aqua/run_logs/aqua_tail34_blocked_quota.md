# AQuA Tail34 Remainder Validation Blocked By API Quota

**Date**: 2026-07-08
**Dataset slice**: `task_split_aqua.json` test indices `[200:]`
**Split file**: `experiment/aqua/task_split_aqua_tail34.json`
**LLM target**: `gpt-4o-2024-08-06`
**Status**: blocked before valid evaluation

## Rationale

After R030, the remaining pre-registered AQuA test slice contains 34 rows. This is a better immediate validation target than forcing GSM8K or MMLU because:

1. GSM8K/MultiArith/SVAMP are numeric-answer tasks, while the current PromptNode final gates are calibrated for A-E multiple-choice outputs.
2. At the time of R031, MMLU was multiple-choice but this workspace did not yet have a fixed local MMLU transfer split ready for the same ARG-Designer/PromptNode comparison protocol.
3. AQuA tail34 keeps the same dataset family, checkpoint family, LLM, option parser, and clean/noisy audit tooling as the first200 evidence.

R045 update: the local MMLU data-path issue has been reduced by generating `experiment/mmlu/mmlu_stem_transfer100.jsonl` and `experiment/mmlu/task_split_mmlu_stem_transfer100.json`, covering `100` A-D multiple-choice STEM tasks from `15` subjects. This is data preparation only; it does not replace the blocked same-model tail34 validation and does not provide any transfer accuracy claim until ARG/PromptNode traces are run.

## Pre-Registered Tail34 Indices

`task_split_aqua_tail34.json` contains exactly `task_split_aqua.json["test_indices"][200:]`, verified by a direct JSON equality check:

```text
tail34 verified 34 [114, 56, 107] [6, 28, 163]
```

## Failed Baseline Attempt

The first baseline command was launched without a loaded API environment, so every task failed with `RetryError` and zero token/cost accounting. Those invalid files were renamed to:

- `invalid_no_api_key_aqua_tail34_arg_baseline_results.jsonl`
- `res_logs/invalid_no_api_key_aqua_tail34_arg_baseline_summary.jsonl`
- `run_logs/invalid_no_api_key_aqua_tail34_arg_baseline_eval.log`

These files must not be used as experimental results.

## API Preflight

After loading the adjacent OpenAI `.env` from:

```text
/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env
```

a one-message `gpt-4o-2024-08-06` preflight call failed with:

```text
openai.RateLimitError: Error code: 429
code: insufficient_quota
message: You exceeded your current quota, please check your plan and billing details.
```

Therefore no valid `gpt-4o-2024-08-06` tail34 evaluation can be run in the current environment.

Fresh R034-era check after loading the same `.env` also failed with `429 insufficient_quota`, so the pre-registered tail34 validation remains unrun as of 2026-07-08.

Fresh R036-era check after updating the R035 multi-contract validation protocol also failed with the same `429 insufficient_quota` error on a one-message `gpt-4o-2024-08-06` preflight. No tail34 accuracy can be claimed until quota is restored.

Fresh R044-era check after generating the R043 paper figures also failed with the same `429 insufficient_quota` error on the one-message `gpt-4o-2024-08-06` preflight. The traceback terminates in `openai.RateLimitError` wrapped by `tenacity.RetryError`, so no tail34 ARG/PromptNode trace was launched and no tail34 accuracy can be claimed.

Fresh R048-era check after generating the R047 graph-objective training export also failed with the same `429 insufficient_quota` error on the one-message `gpt-4o-2024-08-06` preflight. The traceback again terminates in `openai.RateLimitError` wrapped by `tenacity.RetryError`. No tail34 ARG/PromptNode trace was launched, and no tail34 accuracy can be claimed.

## Evaluation Guard Added

`evaluate_aqua.py` now has two integrity checks:

1. Before model loading, GPT evaluations require `API_KEY` or `OPENAI_API_KEY`.
2. Before final summary logging, a run is rejected when all result records are infrastructure failures and both prompt/completion token counts are zero.

Together these checks prevent a missing-key or quota failure from being recorded as an apparent `0/N` accuracy result.

## Resume Conditions

To resume R031, provide one of:

1. A funded `OPENAI_API_KEY`/`API_KEY` with access to `gpt-4o-2024-08-06`.
2. A compatible `BASE_URL` endpoint serving the same model name and behavior.

After that, first run this preflight from the repository root:

```bash
cd /Users/chencheng/Downloads/论文/ARG-Designer-main
set -a
source /Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env
set +a
.venv/bin/python - <<'PY'
import asyncio
from mas_framework.llm.llm_registry import LLMRegistry

async def main():
    llm = LLMRegistry.get("gpt-4o-2024-08-06")
    response = await llm.agen(
        [{"role": "user", "content": "Reply with only OK."}],
        max_tokens=5,
        temperature=0.0,
    )
    print(response)

asyncio.run(main())
PY
```

Only if the preflight succeeds, rerun the fixed tail34 protocol:

```bash
cd /Users/chencheng/Downloads/论文/ARG-Designer-main/experiment/aqua
set -a
source /Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env
set +a
../../.venv/bin/python evaluate_aqua.py \
  --model_path output/aqua_sync20_model_20260707-230509 \
  --task_split_path task_split_aqua_tail34.json \
  --llm_name gpt-4o-2024-08-06 \
  --decision_method FinalRefer \
  --output_file aqua_tail34_arg_baseline_results.jsonl \
  --summary_log_file res_logs/aqua_tail34_arg_baseline_summary.jsonl \
  --eval_batch_size 4 \
  2>&1 | tee run_logs/aqua_tail34_arg_baseline_eval.log
```

```bash
../../.venv/bin/python evaluate_aqua.py \
  --model_path output/aqua_pn_router_contract_model_20260708-030015 \
  --task_split_path task_split_aqua_tail34.json \
  --llm_name gpt-4o-2024-08-06 \
  --decision_method RouterContractFinalRefer \
  --prompt_node_policy none \
  --prompt_node_topology_policy canonicalize_generated \
  --num_candidate_graphs 1 \
  --eval_batch_size 4 \
  --output_file aqua_tail34_pn_router_contract_results.jsonl \
  --summary_log_file res_logs/aqua_tail34_pn_router_contract_summary.jsonl \
  2>&1 | tee run_logs/aqua_tail34_pn_router_contract_eval.log
```

```bash
../../.venv/bin/python evaluate_aqua.py \
  --model_path output/aqua_pn_router_contract_model_20260708-030015 \
  --task_split_path task_split_aqua_tail34.json \
  --llm_name gpt-4o-2024-08-06 \
  --decision_method RouterContractFinalRefer \
  --prompt_node_policy none \
  --prompt_node_topology_policy canonicalize_generated \
  --num_candidate_graphs 4 \
  --eval_batch_size 4 \
  --output_file aqua_tail34_pn_candidate_select_results.jsonl \
  --summary_log_file res_logs/aqua_tail34_pn_candidate_select_summary.jsonl \
  2>&1 | tee run_logs/aqua_tail34_pn_candidate_select_eval.log
```

```bash
../../.venv/bin/python evaluate_aqua.py \
  --model_path output/aqua_pn_router_contract_model_20260708-030015 \
  --task_split_path task_split_aqua_tail34.json \
  --llm_name gpt-4o-2024-08-06 \
  --decision_method ConservativeRouterContractFinalRefer \
  --prompt_node_policy none \
  --prompt_node_topology_policy canonicalize_generated \
  --num_candidate_graphs 1 \
  --eval_batch_size 4 \
  --output_file aqua_tail34_pn_conservative_router_results.jsonl \
  --summary_log_file res_logs/aqua_tail34_pn_conservative_router_summary.jsonl \
  2>&1 | tee run_logs/aqua_tail34_pn_conservative_router_eval.log
```

```bash
../../.venv/bin/python evaluate_aqua.py \
  --model_path output/aqua_pn_router_contract_model_20260708-030015 \
  --task_split_path task_split_aqua_tail34.json \
  --llm_name gpt-4o-2024-08-06 \
  --decision_method CalibratedPNUtilityFinalRefer \
  --prompt_node_policy none \
  --prompt_node_topology_policy canonicalize_generated \
  --num_candidate_graphs 1 \
  --eval_batch_size 4 \
  --output_file aqua_tail34_pn_calibrated_utility_results.jsonl \
  --summary_log_file res_logs/aqua_tail34_pn_calibrated_utility_summary.jsonl \
  2>&1 | tee run_logs/aqua_tail34_pn_calibrated_utility_eval.log
```

Then build the tail34 ensemble:

```bash
../../.venv/bin/python ensemble_results.py \
  --method_file baseline=aqua_tail34_arg_baseline_results.jsonl \
  --method_file router=aqua_tail34_pn_router_contract_results.jsonl \
  --method_file candidate=aqua_tail34_pn_candidate_select_results.jsonl \
  --method_file conservative=aqua_tail34_pn_conservative_router_results.jsonl \
  --method_file calibrated=aqua_tail34_pn_calibrated_utility_results.jsonl \
  --tie_breaker baseline \
  --output_file aqua_tail34_pn_result_ensemble_results.jsonl \
  --summary_file res_logs/aqua_tail34_pn_result_ensemble_summary.json
```

Then replay the R035 multi-contract PromptNode selectors over the same fixed slice. These steps do not call the LLM; they only consume the tail34 result files above.

```bash
../../.venv/bin/python offline_utility_selector.py \
  --selector multi_contract_union \
  --test-prefix aqua_tail34 \
  --no-invalid-fallback \
  --output-file aqua_tail34_multi_contract_union_only_selector_results.jsonl \
  --summary-file res_logs/aqua_tail34_multi_contract_union_only_selector_summary.json
```

```bash
../../.venv/bin/python offline_utility_selector.py \
  --selector multi_contract_union \
  --test-prefix aqua_tail34 \
  --output-file aqua_tail34_multi_contract_union_selector_results.jsonl \
  --summary-file res_logs/aqua_tail34_multi_contract_union_selector_summary.json
```

Then replay the R038/R039/R040 contract-coverage graph objective selectors. These are also offline and consume the same tail34 method result files:

```bash
../../.venv/bin/python contract_graph_objective.py \
  --prefix aqua_tail34 \
  --output-md run_logs/aqua_tail34_contract_graph_objective_report.md \
  --summary-json res_logs/aqua_tail34_contract_graph_objective_summary.json \
  --selector-output-jsonl aqua_tail34_objective_guided_selector_results.jsonl \
  --selector-summary-json res_logs/aqua_tail34_objective_guided_selector_summary.json \
  --selector-report-md run_logs/aqua_tail34_objective_guided_selector_report.md
```

```bash
../../.venv/bin/python contract_graph_objective.py \
  --prefix aqua_tail34 \
  --output-md run_logs/aqua_tail34_contract_graph_objective_report.md \
  --summary-json res_logs/aqua_tail34_contract_graph_objective_summary.json \
  --selector-output-jsonl aqua_tail34_margin3_objective_guided_selector_results.jsonl \
  --selector-summary-json res_logs/aqua_tail34_margin3_objective_guided_selector_summary.json \
  --selector-report-md run_logs/aqua_tail34_margin3_objective_guided_selector_report.md \
  --min-score-margin 3
```

Finally, run the option-binding audit over the same fixed slice before making any tail34 claim. The audit must include the pure multi-contract mechanism, the full selector, the ungated objective selector, and the margin-gated objective selector so the paper can separate virtual-node mechanism gains from system-level fallback and graph-objective gains:

```bash
../../.venv/bin/python audit_option_binding.py \
  --task_split_path task_split_aqua_tail34.json \
  --llm_name gpt-4o-2024-08-06 \
  --limit 34 \
  --output_file aqua_tail34_option_binding_audit.jsonl \
  --summary_file res_logs/aqua_tail34_option_binding_audit_summary.json \
  --result_file aqua_tail34_arg_baseline_results.jsonl \
  --result_file aqua_tail34_pn_calibrated_utility_results.jsonl \
  --result_file aqua_tail34_pn_result_ensemble_results.jsonl \
  --result_file aqua_tail34_multi_contract_union_only_selector_results.jsonl \
  --result_file aqua_tail34_multi_contract_union_selector_results.jsonl \
  --result_file aqua_tail34_objective_guided_selector_results.jsonl \
  --result_file aqua_tail34_margin3_objective_guided_selector_results.jsonl \
  2>&1 | tee run_logs/aqua_tail34_option_binding_audit.log
```

After the audit file exists, rerun the two `contract_graph_objective.py` commands above so their selector summaries include the post-hoc clean/noisy split from `aqua_tail34_option_binding_audit.jsonl`.
