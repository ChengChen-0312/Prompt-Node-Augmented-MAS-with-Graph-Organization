# Multi-Contract Union Selector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement R035, a multi-PromptNode-trace selector that increases clean-row virtual-node contract coverage without using gold labels or noisy-label metadata at inference.

**Architecture:** Extend `experiment/aqua/offline_utility_selector.py` with multi-method trace aggregation. Reuse existing per-trace contract parsing, aggregate strong contract counts and direct-consensus counts across PN variants, then replay first100/next100/first200.

**Tech Stack:** Python standard library, existing `mas_framework.agents.final_decision` contract parsers, existing AQuA JSONL logs, `unittest`.

## Global Constraints

- Do not use task IDs, gold answers, clean/noisy labels, or rationales as selector inference features.
- Do not call any LLM/API.
- Separate pure contract switches from invalid-answer fallback in all reports.
- Treat first200 results as exploratory until pre-registered validation is available.

---

### Task 1: Multi-Contract Feature Aggregation

**Files:**
- Modify: `experiment/aqua/offline_utility_selector.py`
- Modify: `tests/test_offline_utility_selector.py`

**Interfaces:**
- Produces: `extract_multi_contract_features(task_id, result_sets, method_keys) -> dict`

- [ ] **Step 1: Write failing test**

Test that strong option counts and direct-consensus counts aggregate across two PN methods.

- [ ] **Step 2: Verify RED**

Run: `.venv/bin/python -m unittest tests.test_offline_utility_selector -v`

- [ ] **Step 3: Implement feature aggregation**

Reuse `extract_contract_consensus_features()` for each method record.

- [ ] **Step 4: Verify GREEN**

Run: `.venv/bin/python -m unittest tests.test_offline_utility_selector -v`

### Task 2: Union Rule

**Files:**
- Modify: `experiment/aqua/offline_utility_selector.py`
- Modify: `tests/test_offline_utility_selector.py`

**Interfaces:**
- Produces: `apply_multi_contract_union_rule(baseline_prediction, ensemble_prediction, features, min_direct_methods=2, min_strong_methods=3, use_invalid_fallback=True) -> tuple[prediction, source]`

- [ ] **Step 1: Write failing tests**

Test direct-consensus union, strong-contract majority, tie abstention, and invalid fallback.

- [ ] **Step 2: Verify RED**

Run: `.venv/bin/python -m unittest tests.test_offline_utility_selector -v`

- [ ] **Step 3: Implement deterministic rule**

Use a unique top candidate only. If candidates tie or equal baseline, keep baseline.

- [ ] **Step 4: Verify GREEN and full suite**

Run targeted and full tests.

### Task 3: Replay and Report

**Files:**
- Modify: `experiment/aqua/offline_utility_selector.py`
- Create: `experiment/aqua/aqua_first200_multi_contract_union_selector_results.jsonl`
- Create: `experiment/aqua/aqua_first200_multi_contract_union_only_selector_results.jsonl`
- Create: `experiment/aqua/run_logs/aqua_first200_multi_contract_union_selector_analysis.md`
- Modify: `refine-logs/EXPERIMENT_TRACKER.md`
- Modify: `refine-logs/MANIFEST.md`
- Modify: `.aris/claims.json`

**Interfaces:**
- Adds CLI selector: `--selector multi_contract_union`

- [ ] **Step 1: Add CLI branch**

Build records from all PN method files in `PREFIX_FILES`.

- [ ] **Step 2: Run pure and full first200 replay**

Pure replay uses `--no-invalid-fallback`; full replay enables fallback.

- [ ] **Step 3: Write report**

Report official, clean, noisy, switch source counts, fix/harm, and selected task IDs.

- [ ] **Step 4: Final verification**

Run JSON validation, evidence recomputation, targeted tests, and full tests.
