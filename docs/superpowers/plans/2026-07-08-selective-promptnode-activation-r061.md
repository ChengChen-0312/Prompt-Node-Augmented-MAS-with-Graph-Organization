# R061 Selective PromptNode Activation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a label-free replay tool that selectively chooses between ARG baseline traces and R058 PromptNode traces.

**Architecture:** Create one focused script under `experiment/aqua/` that imports existing JSONL and router-contract helpers, plus one focused unittest module. The script writes replay JSONL, summary JSON, and a Markdown report; docs and claims are updated only after replay verification.

**Tech Stack:** Python 3, `unittest`, existing ARG-Designer AQuA JSONL outputs, existing `experiment.aqua.offline_utility_selector` helpers.

## Global Constraints

- Use existing `gpt-4o-2024-08-06` traces; do not call a different model for R061 replay.
- Do not use task IDs, hidden labels, `true_answer`, `is_solved`, clean/noisy labels, or outcome-derived fields in the activation gate.
- Treat R061 as replay over existing traces, not as a fresh integrated evaluator.
- Preserve ARG-Designer as the baseline in all reports.
- Run focused and full verification before claiming completion.

---

### Task 1: Failing Tests For The Activation Gate

**Files:**
- Create: `tests/test_selective_promptnode_activation.py`

**Interfaces:**
- Consumes expected future module `experiment.aqua.selective_promptnode_activation`.
- Produces tests for `extract_direct_votes`, `should_activate_promptnode`, `build_selective_records`, `summarize_selected_records`, and CLI importability.

- [ ] **Step 1: Write the failing test**

Use synthetic records with direct agent outputs and PN router contracts:

```python
def test_gate_activates_on_direct_conflict_and_strong_router_option(self):
    base_record = {
        "task_id": "task_fix",
        "true_answer": "D",
        "predicted_answer": "B",
        "agent_outputs": [
            {"node": 0, "role": "Math Solver", "outputs": ["The answer is B"]},
            {"node": 1, "role": "Inspector", "outputs": ["The answer is D"]},
        ],
    }
    pn_record = {
        "task_id": "task_fix",
        "predicted_answer": "D",
        "agent_outputs": [
            {"node": 0, "role": "Math Solver", "outputs": ["The answer is D"]},
            {"node": 1, "role": "PN_Router", "outputs": [
                "SUPPORTED_OPTION: D\nBINDING_STATUS: EXACT_MATCH\nFINAL_EVIDENCE_SUMMARY: verified"
            ]},
        ],
    }
    activate, features = should_activate_promptnode(base_record, pn_record)
    self.assertTrue(activate)
    self.assertNotIn("true_answer", features)
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
.venv/bin/python -m unittest tests.test_selective_promptnode_activation -v
```

Expected: fail because `experiment.aqua.selective_promptnode_activation` does not exist.

### Task 2: Minimal Replay Implementation

**Files:**
- Create: `experiment/aqua/selective_promptnode_activation.py`

**Interfaces:**
- Produces `extract_direct_votes(record: dict) -> list[str]`.
- Produces `should_activate_promptnode(base_record: dict, pn_record: dict) -> tuple[bool, dict]`.
- Produces `build_selective_records(base_records: dict, pn_records: dict) -> list[dict]`.
- Produces `summarize_selected_records(records: list[dict]) -> dict`.
- Produces CLI args `--baseline-file`, `--promptnode-file`, `--output-file`, `--summary-json`, `--report-md`, and `--split-name`.

- [ ] **Step 1: Implement minimal code**

Reuse `load_jsonl_by_task`, `normalize_option`, `extract_contract_consensus_features`, and `write_jsonl` style from existing AQuA utilities. Keep the nested `gate_features` dict outcome-free.

- [ ] **Step 2: Run focused tests**

Run:

```bash
.venv/bin/python -m unittest tests.test_selective_promptnode_activation -v
```

Expected: `OK`.

### Task 3: R061 Replay Runs

**Files:**
- Output: `experiment/aqua/aqua_sync20_r061_selective_promptnode_results.jsonl`
- Output: `experiment/aqua/res_logs/aqua_sync20_r061_selective_promptnode_summary.json`
- Output: `experiment/aqua/run_logs/aqua_sync20_r061_selective_promptnode_report.md`
- Output: `experiment/aqua/aqua_tail34_r061_selective_promptnode_results.jsonl`
- Output: `experiment/aqua/res_logs/aqua_tail34_r061_selective_promptnode_summary.json`
- Output: `experiment/aqua/run_logs/aqua_tail34_r061_selective_promptnode_report.md`

- [ ] **Step 1: Run sync20 replay**

```bash
.venv/bin/python experiment/aqua/selective_promptnode_activation.py \
  --split-name sync20 \
  --baseline-file experiment/aqua/aqua_sync20_eval20_results.jsonl \
  --promptnode-file experiment/aqua/aqua_sync20_r055_graph_policy_router_contract_terminal_results.jsonl \
  --output-file experiment/aqua/aqua_sync20_r061_selective_promptnode_results.jsonl \
  --summary-json experiment/aqua/res_logs/aqua_sync20_r061_selective_promptnode_summary.json \
  --report-md experiment/aqua/run_logs/aqua_sync20_r061_selective_promptnode_report.md
```

- [ ] **Step 2: Run tail34 replay**

```bash
.venv/bin/python experiment/aqua/selective_promptnode_activation.py \
  --split-name tail34 \
  --baseline-file experiment/aqua/aqua_tail34_arg_baseline_results.jsonl \
  --promptnode-file experiment/aqua/aqua_tail34_r058_router_contract_terminal_results.jsonl \
  --output-file experiment/aqua/aqua_tail34_r061_selective_promptnode_results.jsonl \
  --summary-json experiment/aqua/res_logs/aqua_tail34_r061_selective_promptnode_summary.json \
  --report-md experiment/aqua/run_logs/aqua_tail34_r061_selective_promptnode_report.md
```

### Task 4: Research Ledger And Verification

**Files:**
- Modify: `refine-logs/EXPERIMENT_TRACKER.md`
- Modify: `refine-logs/MANIFEST.md`
- Modify: `.aris/claims.json`
- Modify: `refine-logs/PAPER_PLAN.md`
- Create: `refine-logs/PAPER_PLAN_R061_PROMPTNODE_SCI_20260708.md`

- [ ] **Step 1: Update ledgers**

Record sync20 and tail34 replay results, the no-leakage gate boundary, and the next required fresh integrated evaluator.

- [ ] **Step 2: Verify**

Run:

```bash
.venv/bin/python -m unittest tests.test_selective_promptnode_activation tests.test_offline_utility_selector tests.test_router_contract_final -v
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m json.tool .aris/claims.json >/tmp/claims_r061.json
```

Expected: tests pass and claims JSON parses.
