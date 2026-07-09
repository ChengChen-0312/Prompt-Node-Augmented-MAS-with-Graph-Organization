# Constrained Prompt Node Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add constrained Prompt Node topology normalization and structured PromptNode verifier behavior so virtual nodes are semantically valid during AQuA execution.

**Architecture:** Keep ARGDesigner unchanged. Add a NetworkX graph-normalization utility that canonicalizes generated PN subgraphs, wire it into AQuA evaluation and finetune-data generation behind explicit CLI flags, and make `PromptNode` prompts role-specific.

**Tech Stack:** Python 3.12, standard-library `unittest`, NetworkX, PyTorch Geometric `Data`, existing ARG-Designer modules.

## Global Constraints

- Default behavior must remain ARG-Designer compatible when new policies are `none`.
- Do not use `true_answer`, task ids, row indices, or known wrong-case branches.
- Do not add deterministic arithmetic solvers or answer-label patches.
- Use `gpt-4o-2024-08-06` for runtime experiments.
- This workspace is not a git repository; skip commit steps and report changed files.

---

### Task 1: Canonical PN Topology Utility

**Files:**
- Modify: `experiment/aqua/prompt_node_graph.py`
- Modify: `tests/test_prompt_node_roles.py`

**Interfaces:**
- Produces: `canonicalize_prompt_node_topology(nx_graph, policy="none") -> nx.DiGraph`
- Consumes: `augment_graph_with_prompt_nodes(nx_graph, policy="memory_verifier_router")`

- [ ] **Step 1: Write failing tests**

Add tests that:

```python
def test_canonicalize_generated_prompt_nodes_replaces_invalid_pn_subgraph(self):
    graph = nx.DiGraph()
    graph.add_node(0, role="Math Solver", label=0)
    graph.add_node(1, role="Programming Expert", label=1)
    graph.add_node(2, role="PN_Router", label=2)
    graph.add_node(3, role="PN_Router", label=3)
    graph.add_edge(0, 1, label=1)
    graph.add_edge(0, 3, label=1)
    graph.add_edge(1, 2, label=1)

    normalized = canonicalize_prompt_node_topology(
        graph, policy="canonicalize_generated"
    )

    roles = [normalized.nodes[n]["role"] for n in normalized.nodes()]
    self.assertEqual(roles.count("PN_Memory"), 1)
    self.assertEqual(roles.count("PN_Verifier"), 1)
    self.assertEqual(roles.count("PN_Router"), 1)
    self.assertTrue(nx.is_directed_acyclic_graph(normalized))
```

```python
def test_canonicalize_generated_leaves_no_pn_graph_unchanged(self):
    graph = nx.DiGraph()
    graph.add_node(0, role="Math Solver", label=0)
    graph.add_node(1, role="Inspector", label=1)
    graph.add_edge(0, 1, label=1)

    normalized = canonicalize_prompt_node_topology(
        graph, policy="canonicalize_generated"
    )

    self.assertEqual(
        [normalized.nodes[n]["role"] for n in normalized.nodes()],
        ["Math Solver", "Inspector"],
    )
    self.assertEqual(list(normalized.edges()), [(0, 1)])
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
.venv/bin/python -m unittest tests.test_prompt_node_roles.PromptNodeRoleTests.test_canonicalize_generated_prompt_nodes_replaces_invalid_pn_subgraph -v
.venv/bin/python -m unittest tests.test_prompt_node_roles.PromptNodeRoleTests.test_canonicalize_generated_leaves_no_pn_graph_unchanged -v
```

Expected: ERROR because `canonicalize_prompt_node_topology` is not defined.

- [ ] **Step 3: Implement minimal utility**

Add:

```python
def canonicalize_prompt_node_topology(nx_graph, policy="none") -> nx.DiGraph:
    ...
```

Policies:

- `none`: return a deep copy.
- `canonicalize_generated`: if no PN roles exist, return a deep copy; otherwise strip PN nodes and append the canonical `PN_Memory -> PN_Verifier -> PN_Router` chain.
- `canonicalize_or_insert`: strip any PN nodes and always append the canonical chain to real agents.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
.venv/bin/python -m unittest tests.test_prompt_node_roles -v
```

Expected: PASS.

### Task 2: Structured PromptNode Verifier

**Files:**
- Modify: `mas_framework/agents/prompt_node.py`
- Modify: `tests/test_prompt_node_execution.py`

**Interfaces:**
- Consumes: `PromptNode(role="PN_Verifier", llm_name="mock").execute({"task": ...})`
- Produces role-specific mock prompt text with `TARGET_AUDIT`, `OPTION_BINDING_AUDIT`, and `NO_NEAREST_OPTION_RESCUE`.

- [ ] **Step 1: Write failing test**

Add:

```python
def test_verifier_prompt_contains_option_binding_contract(self):
    prompt_node = PromptNode(role="PN_Verifier", domain="aqua", llm_name="mock")
    predecessor = SimpleNamespace(
        id="solver",
        role="Math Solver",
        outputs=["Computed 13/15, then says The answer is E"],
    )
    prompt_node.spatial_predecessors = [predecessor]

    output = prompt_node.execute({
        "task": "Question? Choices: A)1/18 B)1/9 C)23/90 D)5/18 E)13/45"
    })[0]

    self.assertIn("TARGET_AUDIT", output)
    self.assertIn("OPTION_BINDING_AUDIT", output)
    self.assertIn("NO_NEAREST_OPTION_RESCUE", output)
    self.assertIn("E) 13/45", output)
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
.venv/bin/python -m unittest tests.test_prompt_node_execution.PromptNodeExecutionTests.test_verifier_prompt_contains_option_binding_contract -v
```

Expected: FAIL because current prompt is generic.

- [ ] **Step 3: Implement role-specific prompts**

Modify `PromptNode._process_inputs` to dispatch role-specific instructions:

- Memory: evidence ledger.
- Verifier: target preservation, answer extraction, option binding, nearest-choice rejection.
- Router: suppress unsupported labels and forward verified evidence.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
.venv/bin/python -m unittest tests.test_prompt_node_execution -v
```

Expected: PASS.

### Task 3: Wire Topology Policy Into AQuA Scripts

**Files:**
- Modify: `experiment/aqua/evaluate_aqua.py`
- Modify: `experiment/aqua/finetune_aqua.py`
- Modify: `tests/test_prompt_node_finetune_hook.py`
- Modify: `tests/test_prompt_node_pyg_pipeline.py`

**Interfaces:**
- Produces CLI flag: `--prompt_node_topology_policy`
- Choices: `none`, `canonicalize_generated`, `canonicalize_or_insert`
- Modifies: `apply_prompt_node_policy_to_graph(nx_graph, prompt_node_policy, prompt_node_topology_policy)`
- Modifies: `prepare_efficient_graph_for_execution(nx_graph, task_text, prompt_node_policy, prompt_node_topology_policy)`

- [ ] **Step 1: Write failing tests**

Add tests that the helper accepts `prompt_node_topology_policy="canonicalize_generated"` and normalizes duplicate PN roles before PyG conversion.

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
.venv/bin/python -m unittest tests.test_prompt_node_finetune_hook -v
.venv/bin/python -m unittest tests.test_prompt_node_pyg_pipeline -v
```

Expected: FAIL because helper signatures and CLI flags do not exist.

- [ ] **Step 3: Implement minimal wiring**

Import `canonicalize_prompt_node_topology` in both scripts, add the CLI flag, and apply topology normalization after any explicit insertion policy and before `convert_to_pyg_graph`.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Expected: PASS.

### Task 4: Smoke Evaluation

**Files:**
- Modify: `refine-logs/EXPERIMENT_TRACKER.md`
- Modify: `refine-logs/MANIFEST.md`
- Add run log under `experiment/aqua/run_logs/`

**Interfaces:**
- Uses model: `experiment/aqua/output/aqua_pn_mvr_clean_model_20260708-015036`
- Uses runtime LLM: `gpt-4o-2024-08-06`

- [ ] **Step 1: Run constrained generated-PN eval**

Run from `experiment/aqua`:

```bash
set -a
source /Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env
set +a
../../.venv/bin/python evaluate_aqua.py \
  --model_path output/aqua_pn_mvr_clean_model_20260708-015036 \
  --llm_name gpt-4o-2024-08-06 \
  --decision_method FinalRefer \
  --output_file aqua_sync20_pn_constrained_generated_results.jsonl \
  --summary_log_file ./res_logs/aqua_sync20_pn_constrained_generated_summary.jsonl \
  --limit 20 \
  --eval_batch_size 4 \
  --prompt_node_policy none \
  --prompt_node_topology_policy canonicalize_generated
```

- [ ] **Step 2: Analyze results**

Compare against `aqua_sync20_eval20_results.jsonl` and `aqua_sync20_pn_argdesigner_clean_results.jsonl`.

- [ ] **Step 3: Record outcome**

If the score is below `18/20`, mark the iteration as a negative result and do not claim improvement.

