# PN-ARGDesigner Train-Time Prompt Node Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add train-time virtual Prompt Nodes to ARG-Designer so AQuA graphs can include learned `PN_Memory`, `PN_Verifier`, and `PN_Router` nodes and execute them as lightweight graph-organization nodes.

**Architecture:** Keep ARG-Designer architecture unchanged for v1. Add PN roles to AQuA role vocabularies, add a lightweight `PromptNode` executor, dispatch `PN_*` roles to that executor in `TestGraph`, and add graph augmentation utilities that insert PN nodes before execution / training data saving.

**Tech Stack:** Python 3.12, standard-library `unittest`, NetworkX, PyTorch Geometric `Data`, existing ARG-Designer modules.

## Global Constraints

- Same LLM environment as ARG-Designer: `gpt-4o-2024-08-06` remains the target runtime model.
- Do not use `true_answer` inside prompts or graph augmentation logic.
- Do not branch on AQuA `task_id`, row index, or known wrong examples.
- Do not add deterministic arithmetic solvers or AQuA-specific answer patches.
- Prompt Nodes are virtual graph-organization nodes, not extra normal `MathSolver` agents.
- Version 1 uses existing directed binary edges; labeled READ/WRITE/FORWARD edges are deferred.
- Tests use standard-library `unittest` because this repo has no pytest dependency.
- This workspace is not a git repository; skip commit steps and report changed files instead.

---

### Task 1: PN Role Vocabulary and Graph Augmentation Tests

**Files:**
- Create: `tests/test_prompt_node_roles.py`
- Create: `experiment/aqua/prompt_node_graph.py`
- Modify: `experiment/aqua/aqua_prompt_set.py`
- Modify: `mas_framework/prompt/AQuA_prompt_set.py`

**Interfaces:**
- Produces: `PN_ROLE_DESCRIPTIONS: dict[str, str]`
- Produces: `PN_ROLES: tuple[str, ...]`
- Produces: `is_prompt_node_role(role: str) -> bool`
- Produces: `augment_graph_with_prompt_nodes(nx_graph, policy="memory_verifier_router") -> nx.DiGraph`

- [ ] **Step 1: Write the failing test**

Create `tests/test_prompt_node_roles.py` with tests that import both AQuA role tables, check PN roles exist, and verify graph augmentation appends PN nodes and directed edges.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m unittest tests.test_prompt_node_roles -v`
Expected: FAIL or ERROR because `experiment.aqua.prompt_node_graph` does not exist and PN roles are absent.

- [ ] **Step 3: Write minimal implementation**

Create `experiment/aqua/prompt_node_graph.py` with PN role constants and deterministic graph augmentation that never reads labels. Add PN descriptions to both AQuA role tables.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m unittest tests.test_prompt_node_roles -v`
Expected: PASS.

### Task 2: PromptNode Executor and TestGraph Dispatch

**Files:**
- Create: `tests/test_prompt_node_execution.py`
- Create: `mas_framework/agents/prompt_node.py`
- Modify: `mas_framework/agents/__init__.py`
- Modify: `mas_framework/graph/graph.py`

**Interfaces:**
- Consumes: `is_prompt_node_role(role: str) -> bool`
- Produces: `PromptNode(Node)`
- Produces: `PromptNode.trace: dict[str, object]`
- Modifies: `TestGraph._build_from_pyg` dispatch so `PN_*` roles instantiate `PromptNode`, normal AQuA roles instantiate `MathSolver`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_prompt_node_execution.py` with one test for `PromptNode` output on fake predecessor evidence and one test that a PyG graph containing `PN_Memory` is dispatched to `PromptNode`.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m unittest tests.test_prompt_node_execution -v`
Expected: FAIL or ERROR because `PromptNode` does not exist and `TestGraph` dispatches all AQuA nodes as `MathSolver`.

- [ ] **Step 3: Write minimal implementation**

Implement `PromptNode` as a lightweight `Node` subclass. Its first version formats predecessor evidence and task text into structured text; it does not call the LLM for unit tests. Register it as `PromptNode`, import it in `mas_framework/agents/__init__.py`, and dispatch `PN_*` roles in `TestGraph._build_from_pyg`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m unittest tests.test_prompt_node_execution -v`
Expected: PASS.

### Task 3: PyG Preservation and Manual PN Smoke Entry

**Files:**
- Create: `tests/test_prompt_node_pyg_pipeline.py`
- Modify: `experiment/utils.py`
- Modify: `experiment/aqua/evaluate_aqua.py`

**Interfaces:**
- Consumes: `augment_graph_with_prompt_nodes(nx_graph, policy=...) -> nx.DiGraph`
- Modifies: evaluation path to optionally augment generated graphs before `convert_to_pyg_graph`.
- Produces CLI flag: `--prompt_node_policy` with choices `none`, `memory_verifier`, `memory_verifier_router`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_prompt_node_pyg_pipeline.py` with a small NetworkX graph, augment it, convert it to PyG, and assert PN roles and PN edges survive.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m unittest tests.test_prompt_node_pyg_pipeline -v`
Expected: FAIL until augmentation and conversion preserve PN roles.

- [ ] **Step 3: Write minimal implementation**

Ensure `convert_to_pyg_graph` carries all PN roles and constraints. Add an optional `--prompt_node_policy` flag to `evaluate_aqua.py` and apply augmentation before conversion when the policy is not `none`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m unittest tests.test_prompt_node_pyg_pipeline -v`
Expected: PASS.

### Task 4: Train-Time PN Data Generation Hook

**Files:**
- Create: `tests/test_prompt_node_finetune_hook.py`
- Modify: `experiment/aqua/finetune_aqua.py`

**Interfaces:**
- Consumes: `augment_graph_with_prompt_nodes(nx_graph, policy=...) -> nx.DiGraph`
- Produces CLI flag: `--prompt_node_policy` with choices `none`, `memory_verifier`, `memory_verifier_router`.
- Produces metadata: saved PN `.pt` files preserve `prompt_node_policy`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_prompt_node_finetune_hook.py` that imports a small helper from `finetune_aqua.py` and verifies it applies PN augmentation before `convert_to_pyg_graph`.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m unittest tests.test_prompt_node_finetune_hook -v`
Expected: FAIL because the helper / flag does not exist.

- [ ] **Step 3: Write minimal implementation**

Add a helper `prepare_efficient_graph_for_execution(nx_graph, task_text, prompt_node_policy)` in `finetune_aqua.py`, use it in `generate_pruned_data`, and add the CLI flag. The default is `none` to preserve existing baseline behavior.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m unittest tests.test_prompt_node_finetune_hook -v`
Expected: PASS.

### Task 5: Verification and Experiment Tracker Update

**Files:**
- Modify: `refine-logs/EXPERIMENT_TRACKER.md`
- Modify: `refine-logs/MANIFEST.md`

**Interfaces:**
- Consumes: test results from Tasks 1-4.
- Produces: updated tracker status for R004-R006 and implementation notes for R007-R011.

- [ ] **Step 1: Run all unit tests**

Run: `.venv/bin/python -m unittest discover -s tests -v`
Expected: PASS.

- [ ] **Step 2: Run import smoke tests**

Run: `.venv/bin/python - <<'PY'\nimport mas_framework.agents\nfrom experiment.aqua.prompt_node_graph import PN_ROLES\nprint(PN_ROLES)\nPY`
Expected: prints PN role tuple without import errors.

- [ ] **Step 3: Update tracker**

Mark R004-R006 as DONE if the tests pass. Keep R007+ TODO until actual AQuA API runs are executed.

- [ ] **Step 4: Report exact next commands**

Report the manual PN smoke command and the train-time PN data-generation command, using the existing model path and same `gpt-4o-2024-08-06` setting.
