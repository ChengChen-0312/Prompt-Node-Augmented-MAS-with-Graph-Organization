# R063 Risk-Aware PromptNode Activation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a label-free risk-feature audit and exploratory replay for wider PromptNode activation.

**Architecture:** Add one focused script under `experiment/aqua/` that computes pre-PN baseline risk features, applies a deterministic R063 activation prefilter, then replays selection against existing dense PromptNode traces. Keep this separate from the fresh R062 evaluator.

**Tech Stack:** Python 3, `unittest`, existing JSONL traces, existing R061/R062 helper functions.

## Global Constraints

- Do not use `true_answer`, `is_solved`, task ids, clean/noisy labels, or outcome fields in R063 risk features or gate logic.
- Treat tail34 R063 replay as exploratory if the rule is adjusted after inspecting tail34 results.
- Do not run fresh API until replay shows no observed harm.
- Keep ARG-Designer as the baseline and R060 dense PromptNode as the negative control.

---

### Task 1: Failing Risk-Feature Tests

**Files:**
- Create: `tests/test_risk_aware_promptnode_activation.py`

**Interfaces:**
- Consumes future module `experiment.aqua.risk_aware_promptnode_activation`.
- Produces tests for `extract_baseline_risk_features`, `should_run_promptnode_r063`, `should_select_promptnode_r063`, and `build_r063_replay_records`.

- [ ] **Step 1: Write failing tests**

Use synthetic records where baseline final is unsupported by direct votes and
where direct votes have a majority.

- [ ] **Step 2: Run RED**

```bash
.venv/bin/python -m unittest tests.test_risk_aware_promptnode_activation -v
```

Expected: fail because the module does not exist.

### Task 2: Implement R063 Replay

**Files:**
- Create: `experiment/aqua/risk_aware_promptnode_activation.py`

**Interfaces:**
- Produces `extract_baseline_risk_features(record: dict) -> dict`.
- Produces `should_run_promptnode_r063(features: dict) -> bool`.
- Produces `should_select_promptnode_r063(base_record: dict, pn_record: dict, features: dict) -> tuple[bool, dict]`.
- Produces CLI args for baseline trace, dense PromptNode trace, outputs, summary, report, and split name.

- [ ] **Step 1: Implement minimal code**

Reuse option extraction and router-contract helpers from R061.

- [ ] **Step 2: Run GREEN**

```bash
.venv/bin/python -m unittest tests.test_risk_aware_promptnode_activation -v
```

Expected: `OK`.

### Task 3: Tail34 Exploratory Replay

**Files:**
- Output: `experiment/aqua/aqua_tail34_r063_risk_aware_replay_results.jsonl`
- Output: `experiment/aqua/res_logs/aqua_tail34_r063_risk_aware_replay_summary.json`
- Output: `experiment/aqua/run_logs/aqua_tail34_r063_risk_aware_replay_report.md`

- [ ] **Step 1: Replay**

Use R062 baseline records and R060 dense PromptNode traces:

```bash
.venv/bin/python experiment/aqua/risk_aware_promptnode_activation.py \
  --split-name tail34 \
  --baseline-file experiment/aqua/aqua_tail34_r062_integrated_selective_results.jsonl \
  --promptnode-file experiment/aqua/aqua_tail34_r058_router_contract_terminal_results.jsonl \
  --output-file experiment/aqua/aqua_tail34_r063_risk_aware_replay_results.jsonl \
  --summary-json experiment/aqua/res_logs/aqua_tail34_r063_risk_aware_replay_summary.json \
  --report-md experiment/aqua/run_logs/aqua_tail34_r063_risk_aware_replay_report.md
```

### Task 4: Decision And Verification

**Files:**
- Modify: `refine-logs/EXPERIMENT_TRACKER.md`
- Modify: `refine-logs/MANIFEST.md`
- Modify: `.aris/claims.json`
- Modify: `refine-logs/PAPER_PLAN.md`

- [ ] **Step 1: Decide whether to fresh-run R063**

Fresh run only if replay has no observed harm and meaningful coverage beyond
R062.

- [ ] **Step 2: Verify**

```bash
.venv/bin/python -m unittest tests.test_risk_aware_promptnode_activation tests.test_integrated_selective_promptnode_eval tests.test_selective_promptnode_activation -v
.venv/bin/python -m json.tool .aris/claims.json >/tmp/claims_r063.json
```
