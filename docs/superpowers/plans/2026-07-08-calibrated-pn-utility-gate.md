# Calibrated PN Utility Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement and evaluate `CalibratedPNUtilityFinalRefer` for R027.

**Architecture:** Add small feature-extraction helpers to `mas_framework/agents/final_decision.py`, then register a final decision node that can return deterministic evidence-gated answers or fall back to `ConservativeRouterContractFinalRefer`. Keep evaluation code unchanged by using the existing `--decision_method` flag.

**Tech Stack:** Python, existing `AgentRegistry`, existing AQuA parser, `unittest`, existing `evaluate_aqua.py`.

## Global Constraints

- Do not use test labels, task ids, gold answers, or hard-coded AQuA rows inside runtime decision code.
- Keep model and LLM consistent with ARG-Designer: `gpt-4o-2024-08-06`.
- PromptNodes remain virtual graph nodes and evidence routers; do not implement post-hoc noisy-label patches.
- Use TDD: write failing tests before production code.

---

### Task 1: Feature Extraction Tests

**Files:**
- Modify: `/Users/chencheng/Downloads/论文/ARG-Designer-main/tests/test_router_contract_final.py`
- Modify: `/Users/chencheng/Downloads/论文/ARG-Designer-main/mas_framework/agents/final_decision.py`

**Interfaces:**
- Produces: `extract_direct_option_votes(spatial_info: Dict[str, Any]) -> List[str]`
- Produces: `summarize_pn_utility_features(spatial_info: Dict[str, Any]) -> Dict[str, Any]`

- [ ] **Step 1: Write failing tests**

Add tests that import `extract_direct_option_votes` and `summarize_pn_utility_features`, pass mixed ordinary and `PN_*` spatial inputs, and assert that only ordinary votes contribute to the direct majority while router contracts contribute strong/weak PN fields.

- [ ] **Step 2: Verify RED**

Run:

```bash
.venv/bin/python -m unittest tests.test_router_contract_final -v
```

Expected: FAIL because the new helper functions do not exist.

- [ ] **Step 3: Implement helpers**

Add the helper functions to `final_decision.py`. Use local regex extraction compatible with AQuA's `The answer is X` pattern and keep dependencies minimal.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
.venv/bin/python -m unittest tests.test_router_contract_final -v
```

Expected: all router-contract tests pass.

---

### Task 2: Calibrated Gate Tests

**Files:**
- Modify: `/Users/chencheng/Downloads/论文/ARG-Designer-main/tests/test_router_contract_final.py`
- Modify: `/Users/chencheng/Downloads/论文/ARG-Designer-main/mas_framework/agents/final_decision.py`

**Interfaces:**
- Produces: `select_calibrated_pn_utility_answer(spatial_info: Dict[str, Any]) -> Optional[str]`
- Produces registered agent `CalibratedPNUtilityFinalRefer`

- [ ] **Step 1: Write failing tests**

Add tests for weak PN + direct majority, strong conflicting PN + direct majority, strong PN with no direct majority, and uncertain fallback. Tests should instantiate the registered agent with `llm_name="mock"` and inspect `_process_inputs` or `_execute`.

- [ ] **Step 2: Verify RED**

Run:

```bash
.venv/bin/python -m unittest tests.test_router_contract_final -v
```

Expected: FAIL because the selector and agent are not implemented.

- [ ] **Step 3: Implement selector and registered agent**

Add deterministic selection for clear utility cases. In uncertain cases, call the conservative parent behavior.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
.venv/bin/python -m unittest tests.test_router_contract_final -v
```

Expected: all router-contract tests pass.

---

### Task 3: Evaluate R027

**Files:**
- Read: `/Users/chencheng/Downloads/论文/ARG-Designer-main/experiment/aqua/evaluate_aqua.py`
- Output: `/Users/chencheng/Downloads/论文/ARG-Designer-main/experiment/aqua/aqua_100_pn_calibrated_utility_results.jsonl`
- Output: `/Users/chencheng/Downloads/论文/ARG-Designer-main/experiment/aqua/run_logs/aqua_100_pn_calibrated_utility_eval.log`

- [ ] **Step 1: Run AQuA 100 evaluation**

Run from `experiment/aqua`:

```bash
set -a
source /Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env
set +a
../../.venv/bin/python evaluate_aqua.py \
  --model_path output/aqua_pn_router_contract_model_20260708-030015 \
  --llm_name gpt-4o-2024-08-06 \
  --decision_method CalibratedPNUtilityFinalRefer \
  --prompt_node_policy none \
  --prompt_node_topology_policy canonicalize_generated \
  --decision_exposure_policy auto \
  --num_candidate_graphs 1 \
  --limit 100 \
  --eval_batch_size 4 \
  --output_file aqua_100_pn_calibrated_utility_results.jsonl \
  --summary_log_file ./res_logs/aqua_100_pn_calibrated_utility_summary.jsonl \
  2>&1 | tee run_logs/aqua_100_pn_calibrated_utility_eval.log
```

- [ ] **Step 2: Analyze fix/harm and clean/noisy split**

Use `aqua_100_option_binding_audit.jsonl`, `aqua_100_arg_baseline_results.jsonl`, and the R027 result file to compute total, clean, noisy, fixes, harms, clean fixes, and clean harms.

---

### Task 4: Documentation And Verification

**Files:**
- Create: `/Users/chencheng/Downloads/论文/ARG-Designer-main/experiment/aqua/run_logs/aqua_100_pn_calibrated_utility_breakdown.md`
- Create: `/Users/chencheng/Downloads/论文/ARG-Designer-main/refine-logs/RESULT_TO_CLAIM_CALIBRATED_PN_UTILITY_AQUA_20260708.md`
- Modify: `/Users/chencheng/Downloads/论文/ARG-Designer-main/refine-logs/EXPERIMENT_TRACKER.md`
- Modify: `/Users/chencheng/Downloads/论文/ARG-Designer-main/refine-logs/MANIFEST.md`
- Modify: `/Users/chencheng/Downloads/论文/ARG-Designer-main/.aris/claims.json`

- [ ] **Step 1: Record results**

Write the R027 run log and result-to-claim verdict. If it fails to exceed ARG-Designer, say so directly.

- [ ] **Step 2: Verify**

Run:

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall experiment/aqua/audit_option_binding.py experiment/aqua/evaluate_aqua.py experiment/aqua/prompt_node_graph.py experiment/utils.py mas_framework/agents/final_decision.py tests
```

Expected: all tests pass and compileall exits 0.

