# Offline PN Utility Selector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an offline, label-free-at-inference selector that learns when to use PromptNode ensemble evidence instead of ARG baseline evidence.

**Architecture:** Add a standalone analysis script under `experiment/aqua/` that loads existing result JSONL files, extracts runtime-only features, trains a small rule selector on one slice, and evaluates on another slice. The selector only chooses between baseline and result-level PN ensemble predictions; gold labels are used only for training/evaluation, never as inference features.

**Tech Stack:** Python standard library, existing AQuA JSONL result files, `unittest`.

## Global Constraints

- Do not use task IDs, gold answers, noisy-label status, or official rationales as selector inference features.
- Do not call any LLM/API.
- Treat output as exploratory unless evaluated on a held-out/pre-registered slice.
- Preserve existing result files; write new selector artifacts separately.

---

### Task 1: Selector Core

**Files:**
- Create: `experiment/aqua/offline_utility_selector.py`
- Test: `tests/test_offline_utility_selector.py`

**Interfaces:**
- Produces: `extract_selector_features(task_id, result_sets) -> dict`
- Produces: `train_best_rule(training_records) -> dict`
- Produces: `apply_rule(rule, features) -> bool`
- Produces: `build_selected_records(result_sets, task_ids, rule) -> list[dict]`

- [ ] **Step 1: Write failing tests**

Test feature extraction, rule training, and rule application on synthetic result records.

- [ ] **Step 2: Run tests and verify failure**

Run: `.venv/bin/python -m unittest tests.test_offline_utility_selector -v`

- [ ] **Step 3: Implement selector core**

Use only runtime-visible features: prediction validity, baseline/ensemble disagreement, method-vote majority count, and PN-support count.

- [ ] **Step 4: Run targeted and full tests**

Run targeted selector tests and the full test suite.

### Task 2: Cross-Slice Replay

**Files:**
- Modify: `experiment/aqua/offline_utility_selector.py`
- Create: `experiment/aqua/run_logs/aqua_first200_offline_selector_analysis.md`

**Interfaces:**
- Produces CLI command:
  `python offline_utility_selector.py --train-prefix aqua_100 --test-prefix aqua_next100 ...`

- [ ] **Step 1: Add CLI**

Load first100/next100 result files, train on one slice, evaluate on the other, and write JSON summaries.

- [ ] **Step 2: Run first100→next100 and next100→first100**

Record both directions to detect overfitting.

- [ ] **Step 3: Document result-to-claim**

State whether the learned selector improves over baseline without using task IDs or gold labels at inference.
