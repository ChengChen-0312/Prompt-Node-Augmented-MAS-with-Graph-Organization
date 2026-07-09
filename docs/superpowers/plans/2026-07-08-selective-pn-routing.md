# Selective PN Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a selective PromptNode final decision path that can compare direct agent evidence with PN router contracts and trigger an Agent-like audit only under conflict/risk.

**Architecture:** Add a new `SelectivePromptNodeFinalRefer` final node in `mas_framework/agents/final_decision.py`. Add a small `evaluate_aqua.py` CLI switch to override final-node exposure so the selective gate can see both real agents and PN nodes.

**Tech Stack:** Python, unittest, existing `AgentRegistry`, existing AQuA evaluation scripts.

## Global Constraints

- Use `gpt-4o-2024-08-06` for experiments.
- Do not use task IDs, hidden labels, memorized answers, or nearest-option rescue.
- Preserve mathematical truth and submission option as separate fields when choices are inconsistent.
- Run tests before claiming completion.

---

### Task 1: Selective Final Node

**Files:**
- Modify: `mas_framework/agents/final_decision.py`
- Test: `tests/test_selective_prompt_node_final.py`

**Interfaces:**
- Consumes: `extract_router_contracts(spatial_info)`
- Produces: registered decision method `SelectivePromptNodeFinalRefer`

- [ ] **Step 1: Write failing tests**

Tests should assert:

- registry can instantiate `SelectivePromptNodeFinalRefer`
- when router contracts exist, the prompt contains direct agent evidence, router contracts, `PN_ACTION`, and `Agent-like Prompt Node`
- when no router contract exists, it falls back to ordinary `FinalRefer`

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_selective_prompt_node_final.py' -v
```

Expected: fail because `SelectivePromptNodeFinalRefer` is not registered.

- [ ] **Step 3: Implement minimal code**

Add `SelectivePromptNodeFinalRefer(FinalRefer)` with prompt construction only.
Mock mode should return the generated prompt instead of calling an LLM.

- [ ] **Step 4: Run tests to verify GREEN**

Run the same command and expect `OK`.

### Task 2: Decision Exposure Override

**Files:**
- Modify: `experiment/aqua/evaluate_aqua.py`
- Test: `tests/test_prompt_node_pyg_pipeline.py`

**Interfaces:**
- Produces CLI arg: `--decision_exposure_policy auto|all|terminal`

- [ ] **Step 1: Write failing test**

Test that parsed args accept `--decision_exposure_policy all` and that helper
logic can override the default terminal exposure.

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_prompt_node_pyg_pipeline.py' -v
```

Expected: fail because the arg/helper does not exist.

- [ ] **Step 3: Implement minimal code**

Add the CLI argument and helper that resolves `auto` to current behavior.

- [ ] **Step 4: Run tests to verify GREEN**

Run targeted test and then full test suite.

### Task 3: Sync20 Experiment

**Files:**
- Output: `experiment/aqua/aqua_sync20_selective_pn_results.jsonl`
- Output: `experiment/aqua/run_logs/aqua_sync20_selective_pn_eval.log`
- Output: `experiment/aqua/run_logs/aqua_sync20_selective_pn_breakdown.md`

**Command:**

```bash
cd experiment/aqua
set -a
source /Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env
set +a
../../.venv/bin/python evaluate_aqua.py \
  --model_path output/aqua_pn_router_contract_model_20260708-030015 \
  --llm_name gpt-4o-2024-08-06 \
  --decision_method SelectivePromptNodeFinalRefer \
  --output_file aqua_sync20_selective_pn_results.jsonl \
  --summary_log_file ./res_logs/aqua_sync20_selective_pn_summary.jsonl \
  --limit 20 \
  --eval_batch_size 4 \
  --prompt_node_policy none \
  --prompt_node_topology_policy canonicalize_generated \
  --decision_exposure_policy all \
  2>&1 | tee run_logs/aqua_sync20_selective_pn_eval.log
```

Success requires `>=18/20`.
