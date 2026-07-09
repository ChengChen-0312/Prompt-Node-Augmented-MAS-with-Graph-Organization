# AQuA sync20 PN Candidate Graph Selection Breakdown

Date: 2026-07-08

## Purpose

Test R023: move PromptNode control earlier than final prompting by generating
multiple ARG-Designer graph candidates and using virtual-node graph-organization
scores to select one candidate before execution.

This is intended to match the `update2.docx` claim that Prompt Nodes should
participate in graph organization and lifecycle control, not merely rewrite the
final answer.

## Implementation

New interfaces:

- `generate_graph(..., num_samples=K, batch_size=1)`
- `score_prompt_node_candidate_graph(nx_graph)`
- `select_prompt_node_candidate_graph(graphs)`
- `evaluate_aqua.py --num_candidate_graphs`

Scoring uses only graph-organization features:

- real role coverage
- PN lifecycle role coverage
- weak connectivity
- density balance
- redundancy penalty
- node/edge cost proxy

It does not use task IDs, gold labels, predicted answers, or correctness.

## Main Run

Command:

```bash
../../.venv/bin/python evaluate_aqua.py \
  --model_path output/aqua_pn_router_contract_model_20260708-030015 \
  --llm_name gpt-4o-2024-08-06 \
  --decision_method RouterContractFinalRefer \
  --output_file aqua_sync20_pn_candidate_select_results.jsonl \
  --summary_log_file ./res_logs/aqua_sync20_pn_candidate_select_summary.jsonl \
  --limit 20 \
  --eval_batch_size 4 \
  --num_candidate_graphs 4 \
  --prompt_node_policy none \
  --prompt_node_topology_policy canonicalize_generated
```

Result:

- Accuracy: `17/20 = 85.00%`
- Cost: `$0.801090`
- Prompt tokens: `63933`
- Completion tokens: `32095`
- Candidate count: `4` per task
- At least one PN candidate: `18/20`
- Selected PN candidate: `18/20`
- Selected candidate index counts: `{0: 10, 1: 4, 2: 5, 3: 1}`
- Average score spread across candidates: `1.21695235`

Wrong rows:

| Task | Gold | Baseline Pred | Candidate-Select Pred | Status |
| --- | --- | --- | --- | --- |
| `task_152` | `C` | `E` | `E` | unchanged |
| `task_199` | `A` | `C` | `C` | unchanged |
| `task_172` | `E` | `C` | `D` | still wrong |

## Ablation: Candidate Selection + Full-Evidence FinalRefer

Command change:

- `--decision_method FinalRefer`
- `--decision_exposure_policy all`

Result:

- Accuracy: `16/20 = 80.00%`
- Cost: `$1.004035`
- Selected PN candidate: `18/20`

Wrong rows:

| Task | Gold | Baseline Pred | Candidate-All Pred | Status |
| --- | --- | --- | --- | --- |
| `task_61` | `D` | `D` | `N` | new harm / invalid answer |
| `task_152` | `C` | `E` | `E` | unchanged |
| `task_199` | `A` | `C` | `C` | unchanged |
| `task_172` | `E` | `C` | `A` | still wrong |

## Verdict

- `claim_supported`: no
- Candidate graph selection changes graph organization and selects PN graphs, but
  it does not exceed ARG-Designer on sync20.
- Full-evidence final aggregation is worse than router-contract aggregation.

## Interpretation

Deterministic graph-organization scoring is not enough. It selects structurally
rich PN graphs, but the selected structure still cannot repair the label/option
noise bottleneck in `task_152`, `task_199`, and `task_172`.

Next viable direction:

1. Run a clean/noisy option-binding audit on a larger AQuA subset.
2. Evaluate graph selection separately on clean rows and noisy rows.
3. If clean-row gains exist, train a learned selector from graph features and PN
   contract diagnostics; if no clean-row gains exist, pivot to a cleaner transfer
   benchmark before paper writing.
