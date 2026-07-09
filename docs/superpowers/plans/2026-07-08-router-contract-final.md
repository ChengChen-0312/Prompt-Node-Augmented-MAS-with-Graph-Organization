# Router Contract Final Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `PN_Router` expose a machine-readable answer contract and add a final decision node that consumes terminal router contracts as graph evidence instead of bypassing the router.

**Architecture:** Keep ARGDesigner unchanged and keep all new behavior opt-in. `PromptNode(role="PN_Router")` is prompted to emit `SUPPORTED_OPTION`, `BINDING_STATUS`, and `FINAL_EVIDENCE_SUMMARY`. A new `RouterContractFinalRefer` final node parses router contracts and asks the same LLM to make a concise final decision from the contract, with fallback to ordinary evidence when no contract exists.

**Tech Stack:** Python 3.12, standard-library `unittest`, existing `mas_framework` agent registry, existing AQuA evaluation script.

## Global Constraints

- Do not use `true_answer`, task ids, row indices, or known wrong-case branches.
- Do not add deterministic arithmetic solvers or answer-label patches.
- Default `FinalRefer` behavior must remain unchanged.
- Use `gpt-4o-2024-08-06` for runtime experiments.
- This workspace is not a git repository; skip commit steps and report changed files.

---

### Task 1: Router Contract Prompt

**Files:**
- Modify: `mas_framework/agents/prompt_node.py`
- Modify: `tests/test_prompt_node_execution.py`

**Interfaces:**
- Consumes: `PromptNode(role="PN_Router", llm_name="mock").execute({"task": ...})`
- Produces: prompt text containing `SUPPORTED_OPTION`, `BINDING_STATUS`, `FINAL_EVIDENCE_SUMMARY`, and `SUPPRESS_UNSUPPORTED_LABELS`.

- [ ] **Step 1: Write failing test**

Add a test asserting the mock router prompt contains the contract fields.

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
.venv/bin/python -m unittest tests.test_prompt_node_execution.PromptNodeExecutionTests.test_router_prompt_contains_machine_readable_contract -v
```

Expected: FAIL until router prompt includes the fields.

- [ ] **Step 3: Implement minimal prompt contract**

Extend the existing `PN_Router` role contract to require:

```text
SUPPORTED_OPTION: A/B/C/D/E/NONE
BINDING_STATUS: EXACT_MATCH/EQUIVALENT_FORM/NO_EXACT_OPTION/UNSUPPORTED_LABEL/CONFLICT
FINAL_EVIDENCE_SUMMARY: ...
SUPPRESS_UNSUPPORTED_LABELS: ...
```

- [ ] **Step 4: Run test to verify GREEN**

Run:

```bash
.venv/bin/python -m unittest tests.test_prompt_node_execution -v
```

Expected: PASS.

### Task 2: RouterContractFinalRefer

**Files:**
- Modify: `mas_framework/agents/final_decision.py`
- Modify: `mas_framework/agents/__init__.py`
- Create: `tests/test_router_contract_final.py`

**Interfaces:**
- Produces: `extract_router_contracts(spatial_info: dict) -> list[dict[str, str]]`
- Produces registered final node: `RouterContractFinalRefer`

- [ ] **Step 1: Write failing parser/final tests**

Test that contract extraction parses router output fields and that `RouterContractFinalRefer` is registered.

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
.venv/bin/python -m unittest tests.test_router_contract_final -v
```

Expected: ERROR until parser/final node exist.

- [ ] **Step 3: Implement minimal final node**

Add a parser and final node:

- If router contracts exist, include only router contract summaries and task choices in the final prompt.
- If no contract exists, fall back to `FinalRefer._process_inputs`.
- The final node is opt-in through `--decision_method RouterContractFinalRefer`.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
.venv/bin/python -m unittest tests.test_router_contract_final -v
```

Expected: PASS.

### Task 3: Smoke Evaluation

**Files:**
- Modify: `refine-logs/EXPERIMENT_TRACKER.md`
- Modify: `refine-logs/MANIFEST.md`
- Add run log under `experiment/aqua/run_logs/`

**Interfaces:**
- Uses model: `experiment/aqua/output/aqua_pn_mvr_clean_model_20260708-015036`
- Uses runtime LLM: `gpt-4o-2024-08-06`

- [ ] **Step 1: Run terminal router-contract evaluation**

Run from `experiment/aqua`:

```bash
set -a
source /Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env
set +a
../../.venv/bin/python evaluate_aqua.py \
  --model_path output/aqua_pn_mvr_clean_model_20260708-015036 \
  --llm_name gpt-4o-2024-08-06 \
  --decision_method RouterContractFinalRefer \
  --output_file aqua_sync20_pn_router_contract_results.jsonl \
  --summary_log_file ./res_logs/aqua_sync20_pn_router_contract_summary.jsonl \
  --limit 20 \
  --eval_batch_size 4 \
  --prompt_node_policy none \
  --prompt_node_topology_policy canonicalize_generated
```

- [ ] **Step 2: Analyze result**

Compare to:

- `aqua_sync20_eval20_results.jsonl`
- `aqua_sync20_pn_argdesigner_clean_results.jsonl`
- `aqua_sync20_pn_constrained_terminal_results.jsonl`

- [ ] **Step 3: Record outcome**

If score is below `18/20`, mark the iteration as negative and continue to train-time router supervision.

