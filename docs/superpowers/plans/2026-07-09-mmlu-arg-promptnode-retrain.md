# MMLU ARG PromptNode Retrain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reproduce a fair MMLU train-time comparison between retrained ARG-Designer and retrained PromptNode-augmented graph policies.

**Architecture:** Add protocol-freeze, training launch, graph audit, and evaluation wrappers around the existing MMLU `finetune_mmlu.py`, R184/R186/R188 PN-capable training path, and R274/R279 transfer evaluators. Keep training and evaluation split-aware, label-leakage checked, and same-model comparable.

**Tech Stack:** Python 3.13, PyTorch 2.8, MPS/CPU local execution, ARG-Designer graph policy code, PyG `Data`, standard-library `unittest`.

## Global Constraints

- Target LLM for evaluation: `gpt-4o-2024-08-06`.
- Current machine: Apple Silicon with MPS available; CUDA unavailable.
- Do not use `true_answer`, `is_correct`, `arg_error`, or task id as model-visible training or prompt features.
- `MMLU-ARG-Retrain` and `MMLU-PromptNode-Retrain` must use the same held-out evaluation tasks.
- PromptNode roles must be present from training data materialization, not added after graph generation.
- Existing workspace is not a git repository; skip commit steps and report changed files.
- Next mandatory goal audit after this training block is R285.

---

### Task 1: R281 Training Protocol Freeze

**Files:**
- Create: `tests/test_r281_mmlu_training_protocol_freeze.py`
- Create: `experiment/mmlu/r281_training_protocol_freeze.py`

**Interfaces:**
- Produces: `build_r281_protocol_summary() -> dict`
- Produces: `run(...) -> dict`

- [ ] **Step 1: Write the failing test**

Create `tests/test_r281_mmlu_training_protocol_freeze.py` asserting that R281 detects the old ARG checkpoint, PN-capable checkpoint, role mapping sizes, MPS availability, transfer split files, and blocks broad claims.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_r281_mmlu_training_protocol_freeze -v`
Expected: ERROR because `experiment.mmlu.r281_training_protocol_freeze` does not exist.

- [ ] **Step 3: Implement the protocol summary**

Create `experiment/mmlu/r281_training_protocol_freeze.py` with filesystem checks and no API calls. The summary must state that training is authorized only after split/checkpoint audits pass.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_r281_mmlu_training_protocol_freeze -v`
Expected: PASS.

### Task 2: R282 ARG Retrain Launcher

**Files:**
- Create: `experiment/mmlu/r282_arg_retrain_launcher.py`
- Create: `tests/test_r282_arg_retrain_launcher.py`

**Interfaces:**
- Produces: `build_arg_retrain_command(output_dir: str, epochs: int, seed: int) -> list[str]`
- Produces: `run_dry_run(...) -> dict`

- [ ] **Step 1: Write command-construction tests**

Assert the command calls `experiment/mmlu/finetune_mmlu.py`, uses original MMLU cold-start data, excludes PN data dirs, sets `--pretrain`, and writes to `experiment/mmlu/output/mmlu_arg_retrain_r282`.

- [ ] **Step 2: Implement launcher**

Implement dry-run mode first. Do not start training until the command and output paths are audited.

- [ ] **Step 3: Run test**

Run: `python -m unittest tests.test_r282_arg_retrain_launcher -v`
Expected: PASS.

### Task 3: R283 PromptNode Retrain Launcher

**Files:**
- Create: `experiment/mmlu/r283_promptnode_retrain_launcher.py`
- Create: `tests/test_r283_promptnode_retrain_launcher.py`

**Interfaces:**
- Produces: `build_promptnode_retrain_command(output_dir: str, epochs: int, seed: int) -> list[str]`
- Produces: `run_dry_run(...) -> dict`

- [ ] **Step 1: Write command-construction tests**

Assert the command uses `experiment/PromptEdgeData_mmlu_r183`, writes to `experiment/mmlu/output/mmlu_promptnode_retrain_r283`, and the preflight requires PN roles in role mapping.

- [ ] **Step 2: Implement launcher**

Implement dry-run mode and role-mapping audit first. Training can start only after R281 passes.

- [ ] **Step 3: Run test**

Run: `python -m unittest tests.test_r283_promptnode_retrain_launcher -v`
Expected: PASS.

### Task 4: R284 Generated Graph Audit

**Files:**
- Create: `experiment/mmlu/r284_retrained_graph_audit.py`
- Create: `tests/test_r284_retrained_graph_audit.py`

**Interfaces:**
- Produces: `audit_generated_graph_records(records: list[dict]) -> dict`

- [ ] **Step 1: Write audit tests**

Assert the audit reports PromptNode role rates, edge density, invalid graphs, and whether ARG/PN generated graphs use compatible role vocabularies.

- [ ] **Step 2: Implement audit**

Implement no-API graph audit over generated graph JSONL records.

- [ ] **Step 3: Run test**

Run: `python -m unittest tests.test_r284_retrained_graph_audit -v`
Expected: PASS.

### Task 5: R285 Evaluation Comparison and Goal Audit

**Files:**
- Create: `experiment/mmlu/r285_retrained_full24_eval_plan.py`
- Create: `tests/test_r285_retrained_full24_eval_plan.py`

**Interfaces:**
- Produces: `build_eval_plan(...) -> dict`

- [ ] **Step 1: Write plan tests**

Assert the plan compares retrained ARG, retrained PromptNode, plain requery, node-only, prior PN+PE, and v3 edge-gated PN+PE on the same full24 tasks.

- [ ] **Step 2: Implement plan**

Implement preflight only. API evaluation starts only after generated graph audit passes.

- [ ] **Step 3: Run tests**

Run: `python -m unittest tests.test_r281_mmlu_training_protocol_freeze tests.test_r282_arg_retrain_launcher tests.test_r283_promptnode_retrain_launcher tests.test_r284_retrained_graph_audit tests.test_r285_retrained_full24_eval_plan -v`
Expected: PASS.

## Self-Review

- Spec coverage: Tasks cover protocol freeze, ARG retrain launcher, PromptNode retrain launcher, graph audit, and evaluation plan.
- Placeholder scan: No TBD/TODO placeholders are present.
- Type consistency: All planned public functions return dictionaries or command lists with explicit names.

