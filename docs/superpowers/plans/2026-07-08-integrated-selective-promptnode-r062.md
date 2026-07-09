# R062 Integrated Selective PromptNode Evaluator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a fresh online evaluator that conditionally runs PromptNodes only after an ARG direct-vote conflict prefilter.

**Architecture:** Add one standalone AQuA script that reuses `evaluate_aqua.py` helpers and the R061 gate. The script runs a baseline graph first, then optionally runs a PromptNode graph, and writes selected records plus a summary/report.

**Tech Stack:** Python 3, `unittest`, ARG-Designer AQuA utilities, existing `TestGraph`, existing `selective_promptnode_activation` gate helpers.

## Global Constraints

- Match R059/R060 model setting: `gpt-4o-2024-08-06`.
- Baseline checkpoint: `experiment/aqua/output/aqua_sync20_model_20260707-230509`.
- PromptNode checkpoint: `experiment/aqua/output/aqua_pn_graph_policy_r055_full`.
- Gate features must exclude `true_answer`, `is_solved`, task ids, and audit labels.
- R062 is a fresh integrated run; do not use precomputed R058 outputs for selection.

---

### Task 1: Failing Control-Flow Tests

**Files:**
- Create: `tests/test_integrated_selective_promptnode_eval.py`

**Interfaces:**
- Consumes future module `experiment.aqua.evaluate_selective_promptnode`.
- Produces tests for `baseline_prefilter_passes`, `build_selected_record`, `run_task_selective`, and CLI importability.

- [ ] **Step 1: Write failing tests**

Use fake runner functions that return synthetic baseline and PromptNode records.
Assert that the PromptNode runner is not called when direct votes have a
majority, and is called when the conflict prefilter passes.

- [ ] **Step 2: Run RED**

```bash
.venv/bin/python -m unittest tests.test_integrated_selective_promptnode_eval -v
```

Expected: fail because `experiment.aqua.evaluate_selective_promptnode` does not exist.

### Task 2: Implement The Online Evaluator

**Files:**
- Create: `experiment/aqua/evaluate_selective_promptnode.py`

**Interfaces:**
- Produces `baseline_prefilter_passes(record: dict) -> tuple[bool, dict]`.
- Produces `build_selected_record(...) -> dict`.
- Produces `run_task_selective(...) -> dict`.
- Produces CLI args for baseline model, PromptNode model, split, output, summary, report, and limit.

- [ ] **Step 1: Implement minimal code**

Reuse model loading, graph generation, topology canonicalization, `TestGraph`,
and JSON record formatting from `evaluate_aqua.py`.

- [ ] **Step 2: Run GREEN**

```bash
.venv/bin/python -m unittest tests.test_integrated_selective_promptnode_eval -v
```

Expected: `OK`.

### Task 3: Fresh Smoke And Tail34 Run

**Files:**
- Output: `experiment/aqua/aqua_tail34_r062_integrated_selective_results.jsonl`
- Output: `experiment/aqua/res_logs/aqua_tail34_r062_integrated_selective_summary.json`
- Output: `experiment/aqua/run_logs/aqua_tail34_r062_integrated_selective_report.md`

- [ ] **Step 1: Run a small smoke**

Use `--limit 3` or `--limit 5` first, with API key loaded from the existing
benchmark `.env`.

- [ ] **Step 2: Run tail34 if smoke is valid**

Run all 34 tail tasks only after the smoke has at least one valid LLM response
and no infrastructure failure.

### Task 4: Research Ledger And Verification

**Files:**
- Modify: `refine-logs/EXPERIMENT_TRACKER.md`
- Modify: `refine-logs/MANIFEST.md`
- Modify: `.aris/claims.json`
- Modify: `refine-logs/PAPER_PLAN.md`

- [ ] **Step 1: Update ledgers**

Record whether R062 confirms or rejects the R061 replay hypothesis.

- [ ] **Step 2: Verify**

```bash
.venv/bin/python -m unittest tests.test_integrated_selective_promptnode_eval tests.test_selective_promptnode_activation tests.test_prompt_node_pyg_pipeline -v
.venv/bin/python -m unittest discover -s tests -v
```
