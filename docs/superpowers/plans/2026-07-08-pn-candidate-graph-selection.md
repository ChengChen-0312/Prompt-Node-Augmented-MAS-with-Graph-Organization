# PN Candidate Graph Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Evaluate multiple ARG-Designer graph candidates and use virtual PromptNode graph-organization scores to select one before execution.

**Architecture:** `experiment/utils.py` exposes multi-sample graph generation. `experiment/aqua/prompt_node_graph.py` scores and selects candidates. `experiment/aqua/evaluate_aqua.py` wires `--num_candidate_graphs` into the eval loop and records candidate metadata.

**Tech Stack:** Python, unittest, NetworkX, existing ARG-Designer model/evaluation stack.

## Global Constraints

- Do not use gold labels, task IDs, or answer correctness for graph selection.
- Keep candidate scoring deterministic and based only on graph organization.
- Preserve existing default behavior when `--num_candidate_graphs 1`.
- Run unit tests before experiments.

---

### Task 1: Multi-Sample Graph Generation

**Files:**
- Modify: `experiment/utils.py`
- Test: `tests/test_prompt_node_candidate_selection.py`

**Interfaces:**
- `generate_graph(model, task_embedding, role_constraints_dict, question_id=None, num_samples=1, batch_size=1)`

Steps:

1. Write a failing test with a fake model whose `sample()` records `num_samples`.
2. Run the test and confirm failure because `generate_graph()` lacks the arguments.
3. Add `num_samples` and `batch_size` arguments and forward them to `model.sample()`.
4. Run the targeted test.

### Task 2: Deterministic PN Candidate Scoring

**Files:**
- Modify: `experiment/aqua/prompt_node_graph.py`
- Test: `tests/test_prompt_node_candidate_selection.py`

**Interfaces:**
- `score_prompt_node_candidate_graph(nx_graph) -> dict`
- `select_prompt_node_candidate_graph(graphs) -> tuple`

Steps:

1. Write tests that a balanced graph with PN lifecycle roles scores above a redundant single-role graph.
2. Run the tests and confirm missing function failure.
3. Implement scoring from role coverage, PN coverage, connectivity, density, redundancy, and cost proxy.
4. Run targeted tests.

### Task 3: Evaluation Wiring

**Files:**
- Modify: `experiment/aqua/evaluate_aqua.py`
- Test: `tests/test_prompt_node_candidate_selection.py`

**Interfaces:**
- CLI arg: `--num_candidate_graphs`
- Result fields: `candidate_graphs`, `selected_candidate_index`

Steps:

1. Write tests for CLI parsing and candidate metadata shape.
2. Run tests and confirm failure.
3. Wire multi-candidate generation, policy normalization, selector call, and result metadata.
4. Run targeted tests and full tests.

### Task 4: AQuA sync20 R023 Experiment

Command:

```bash
cd experiment/aqua
set -a
source /Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env
set +a
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

Success gate: `>=18/20`.
