# R001 Selective PromptNode PromptEdge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build R163, an R001-compatible offline export that lets ARG-Designer learn selective first-class PromptNode insertion and PromptEdge metadata before execution.

**Architecture:** Add a small PromptEdge vocabulary to the existing PromptNode graph utilities, then export selective graph-policy rows from existing non-test R077/R112 artifacts. The first run is offline and leakage-checked: it creates rows, `.pt` files, a summary, and a report, but makes no answer-accuracy claim and uses no API.

**Tech Stack:** Python 3, NetworkX, PyTorch, PyG `Data`, existing ARG-Designer AQuA adapters, `unittest`.

## Global Constraints

- Same model setting as R001 for future API work: `gpt-4o-2024-08-06`.
- Do not train or select from gold answers, correctness flags, clean/noisy labels, audit labels, or task ids.
- AQuA sync20 is diagnostic only; do not claim sync20 improvement as a paper result.
- PromptNodes must be graph nodes before execution, not final-answer patches.
- PromptEdge semantics must be represented as graph communication metadata at minimum; learned edge-label generation is only claimable after edge labels enter the model loss.
- Next mandatory goal audit is R165.

---

### Task 1: PromptEdge Vocabulary and Metadata Helpers

**Files:**
- Modify: `experiment/aqua/prompt_node_graph.py`
- Test: `tests/test_r001_selective_promptedge_policy.py`

**Interfaces:**
- Produces: `PROMPT_EDGE_TYPES: tuple[str, ...]`
- Produces: `infer_prompt_edge_type(source_role: str, target_role: str) -> str`
- Produces: `attach_prompt_edge_metadata(graph: nx.DiGraph) -> nx.DiGraph`
- Produces: `summarize_prompt_edges(graph: nx.DiGraph) -> dict[str, int]`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_r001_selective_promptedge_policy.py` with:

```python
import unittest
import networkx as nx


class R001SelectivePromptEdgePolicyTests(unittest.TestCase):
    def test_prompt_edge_metadata_assigns_expected_types(self):
        from experiment.aqua.prompt_node_graph import (
            attach_prompt_edge_metadata,
            summarize_prompt_edges,
        )

        graph = nx.DiGraph()
        graph.add_node(0, role="Math Solver")
        graph.add_node(1, role="Programming Expert")
        graph.add_node(2, role="PN_Memory")
        graph.add_node(3, role="PN_Verifier")
        graph.add_node(4, role="PN_Router")
        graph.add_edges_from([(0, 1), (0, 2), (1, 2), (2, 3), (3, 4)])

        annotated = attach_prompt_edge_metadata(graph)

        self.assertEqual(annotated.edges[0, 1]["prompt_edge_type"], "agent_flow")
        self.assertEqual(annotated.edges[0, 2]["prompt_edge_type"], "write_memory")
        self.assertEqual(annotated.edges[1, 2]["prompt_edge_type"], "write_memory")
        self.assertEqual(annotated.edges[2, 3]["prompt_edge_type"], "verify_contract")
        self.assertEqual(annotated.edges[3, 4]["prompt_edge_type"], "forward_verified")
        self.assertEqual(
            summarize_prompt_edges(annotated),
            {
                "agent_flow": 1,
                "write_memory": 2,
                "verify_contract": 1,
                "forward_verified": 1,
            },
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m unittest tests.test_r001_selective_promptedge_policy.R001SelectivePromptEdgePolicyTests.test_prompt_edge_metadata_assigns_expected_types -v`

Expected: FAIL with import error for `attach_prompt_edge_metadata`.

- [ ] **Step 3: Implement metadata helpers**

Add to `experiment/aqua/prompt_node_graph.py`:

```python
PROMPT_EDGE_TYPES = (
    "agent_flow",
    "write_memory",
    "read_memory",
    "verify_contract",
    "forward_verified",
    "suppress_unsupported",
    "repair_option",
)


def infer_prompt_edge_type(source_role: str, target_role: str) -> str:
    source = str(source_role or "")
    target = str(target_role or "")
    if target == "PN_Memory" and not is_prompt_node_role(source):
        return "write_memory"
    if source == "PN_Memory" and target == "PN_Verifier":
        return "verify_contract"
    if source == "PN_Verifier" and target == "PN_Router":
        return "forward_verified"
    if source == "PN_Router" and target == "PN_Repair":
        return "repair_option"
    if is_prompt_node_role(source) or is_prompt_node_role(target):
        return "read_memory"
    return "agent_flow"


def attach_prompt_edge_metadata(nx_graph: nx.Graph) -> nx.DiGraph:
    graph = nx.DiGraph(nx_graph)
    for source, target, data in graph.edges(data=True):
        source_role = graph.nodes[source].get("role", "")
        target_role = graph.nodes[target].get("role", "")
        edge_type = data.get("prompt_edge_type") or data.get("prompt_edge")
        if edge_type in {"write", "read", "forward"}:
            edge_type = infer_prompt_edge_type(source_role, target_role)
        elif edge_type not in PROMPT_EDGE_TYPES:
            edge_type = infer_prompt_edge_type(source_role, target_role)
        data["prompt_edge_type"] = edge_type
        data["prompt_edge"] = edge_type
        data.setdefault("label", 1)
    graph.graph["prompt_edge_type_counts"] = summarize_prompt_edges(graph)
    return graph


def summarize_prompt_edges(nx_graph: nx.Graph) -> dict[str, int]:
    counts = Counter()
    for _, _, data in nx_graph.edges(data=True):
        edge_type = data.get("prompt_edge_type") or data.get("prompt_edge") or "agent_flow"
        counts[str(edge_type)] += 1
    return dict(sorted(counts.items()))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m unittest tests.test_r001_selective_promptedge_policy.R001SelectivePromptEdgePolicyTests.test_prompt_edge_metadata_assigns_expected_types -v`

Expected: PASS.

---

### Task 2: R163 Selective Policy Export

**Files:**
- Create: `experiment/aqua/r001_selective_promptedge_policy_export.py`
- Modify: `tests/test_r001_selective_promptedge_policy.py`

**Interfaces:**
- Produces: `build_selective_promptedge_policy_rows(r077_rows, r112_rows) -> tuple[list[dict], dict]`
- Produces: `write_r163_artifacts(...) -> dict`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_r001_selective_promptedge_policy.py`:

```python
    def test_selective_export_marks_switch_rows_without_forbidden_fields(self):
        from experiment.aqua.r001_selective_promptedge_policy_export import (
            build_selective_promptedge_policy_rows,
            FORBIDDEN_SELECTOR_FIELDS,
        )

        r077_rows = [
            {
                "source_task_id": "task_a",
                "source_slice_prefix": "aqua_100",
                "source_candidate_method": "candidate",
                "selector_policy_input": {
                    "question": "Q?",
                    "candidate_method": "candidate",
                    "label_free_objective_features": {
                        "objective_bucket": "preferred_graph",
                        "score_margin_to_next": 5,
                    },
                    "candidate_graph_observation": {"num_prompt_nodes": 3},
                },
                "clean_fix_distillation_target": {
                    "target_class": "clean_fix_preserve_graph",
                    "graph_policy_target": {
                        "candidate_label": 1,
                        "training_target": "preferred_graph",
                        "objective_reward": 10,
                        "score_margin_to_next": 5,
                        "roles": ["Math Solver", "PN_Memory", "PN_Verifier", "PN_Router"],
                        "edges": [[0, 1], [1, 2], [2, 3]],
                        "prompt_node_edge_permissions": {"PN_Verifier->PN_Router": ["forward"]},
                    },
                },
            }
        ]
        r112_rows = [
            {
                "task_id": "task_a",
                "slice_prefix": "aqua_100",
                "policy_input": {
                    "objective_prediction_differs_from_baseline": True,
                    "baseline_direct_votes_split": True,
                    "objective_top_score": 8,
                },
                "target_action": "switch_to_objective",
            }
        ]

        rows, summary = build_selective_promptedge_policy_rows(r077_rows, r112_rows)

        self.assertEqual(summary["selective_insert_rows"], 1)
        self.assertEqual(rows[0]["selective_action"], "insert_promptnode_graph")
        self.assertEqual(rows[0]["graph_policy_target"]["candidate_label"], 1)
        self.assertIn("prompt_edge_type_counts", rows[0]["graph_policy_target"])
        serialized = str(rows[0])
        for field in FORBIDDEN_SELECTOR_FIELDS:
            self.assertNotIn(field, serialized)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m unittest tests.test_r001_selective_promptedge_policy.R001SelectivePromptEdgePolicyTests.test_selective_export_marks_switch_rows_without_forbidden_fields -v`

Expected: FAIL with missing module.

- [ ] **Step 3: Implement export builder**

Create `experiment/aqua/r001_selective_promptedge_policy_export.py` with:

```python
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import networkx as nx

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.graph_objective_pairwise_export import load_jsonl_rows  # noqa: E402
from experiment.aqua.graph_policy_pt_export import export_positive_policy_pt_dataset  # noqa: E402
from experiment.aqua.prompt_node_graph import attach_prompt_edge_metadata  # noqa: E402

RULE_NAME = "r163_r001_selective_promptedge_policy_export"

FORBIDDEN_SELECTOR_FIELDS = {
    "true_answer",
    "predicted_answer",
    "router_option",
    "direct_majority",
    "audit_label",
    "clean_label",
    "is_solved",
    "baseline_is_solved",
    "task_id",
    "source_task_id",
}


def _field_violates(value: Any) -> bool:
    if isinstance(value, dict):
        return any(key in FORBIDDEN_SELECTOR_FIELDS or _field_violates(child) for key, child in value.items())
    if isinstance(value, list):
        return any(_field_violates(child) for child in value)
    return False
```

Then implement the row builder following the test:

```python
def _policy_key(task_id: Any, slice_prefix: Any) -> tuple[str, str]:
    return str(task_id), str(slice_prefix)


def _graph_with_edge_metadata(target: Dict[str, Any]) -> Dict[str, Any]:
    roles = list(target.get("roles") or [])
    graph = nx.DiGraph()
    for index, role in enumerate(roles):
        graph.add_node(index, role=role)
    for edge in target.get("edges") or []:
        if isinstance(edge, (list, tuple)) and len(edge) == 2:
            graph.add_edge(int(edge[0]), int(edge[1]))
    annotated = attach_prompt_edge_metadata(graph)
    target = dict(target)
    target["prompt_edge_type_counts"] = dict(annotated.graph.get("prompt_edge_type_counts") or {})
    target["prompt_node_edge_permissions"] = dict(target.get("prompt_node_edge_permissions") or {})
    return target


def build_selective_promptedge_policy_rows(
    r077_rows: Sequence[Dict[str, Any]],
    r112_rows: Sequence[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    r112_by_key = {
        _policy_key(row.get("task_id"), row.get("slice_prefix")): row
        for row in r112_rows
    }
    rows: List[Dict[str, Any]] = []
    action_counts: Counter[str] = Counter()
    edge_counts: Counter[str] = Counter()
    violations = 0

    for source in r077_rows:
        selector_input = dict(source.get("selector_policy_input") or {})
        target_wrapper = dict(source.get("clean_fix_distillation_target") or {})
        target = dict(target_wrapper.get("graph_policy_target") or {})
        key = _policy_key(source.get("source_task_id"), source.get("source_slice_prefix"))
        objective_row = r112_by_key.get(key, {})
        objective_input = dict(objective_row.get("policy_input") or {})
        target_action = str(objective_row.get("target_action") or "fallback_to_arg")
        objective_features = dict(selector_input.get("label_free_objective_features") or {})
        margin = float(objective_features.get("score_margin_to_next") or target.get("score_margin_to_next") or 0)
        has_promptnodes = bool((selector_input.get("candidate_graph_observation") or {}).get("num_prompt_nodes"))
        should_insert = (
            target_action == "switch_to_objective"
            and target_wrapper.get("target_class") == "clean_fix_preserve_graph"
            and int(target.get("candidate_label", 0) or 0) == 1
            and has_promptnodes
            and margin >= 3
        )
        action = "insert_promptnode_graph" if should_insert else "fallback_to_arg_graph"
        action_counts[action] += 1
        target = _graph_with_edge_metadata(target) if should_insert else dict(target, candidate_label=0)
        edge_counts.update(target.get("prompt_edge_type_counts") or {})
        row = {
            "rule": RULE_NAME,
            "source_slice_prefix": source.get("source_slice_prefix"),
            "source_candidate_method": source.get("source_candidate_method"),
            "selector_policy_input": {
                "slice_prefix": selector_input.get("slice_prefix"),
                "question": selector_input.get("question"),
                "candidate_method": selector_input.get("candidate_method"),
                "objective_bucket": objective_features.get("objective_bucket"),
                "score_margin_to_next": margin,
                "objective_prediction_differs_from_baseline": bool(
                    objective_input.get("objective_prediction_differs_from_baseline")
                ),
                "baseline_direct_votes_split": bool(objective_input.get("baseline_direct_votes_split")),
                "objective_top_score": objective_input.get("objective_top_score"),
                "candidate_graph_observation": selector_input.get("candidate_graph_observation") or {},
            },
            "selective_action": action,
            "graph_policy_target": target,
            "claim_boundary": (
                "R001-compatible selective PromptNode/PromptEdge policy target. Selector-visible fields exclude "
                "gold answers, predictions, correctness, audit labels, clean/noisy labels, and task ids."
            ),
        }
        if _field_violates(row["selector_policy_input"]):
            violations += 1
        rows.append(row)

    summary = {
        "rule": RULE_NAME,
        "source_r077_rows": len(r077_rows),
        "source_r112_rows": len(r112_rows),
        "exported_rows": len(rows),
        "selective_insert_rows": action_counts.get("insert_promptnode_graph", 0),
        "fallback_rows": action_counts.get("fallback_to_arg_graph", 0),
        "prompt_edge_type_counts": dict(sorted(edge_counts.items())),
        "selector_input_forbidden_field_violations": violations,
        "forbidden_selector_fields": sorted(FORBIDDEN_SELECTOR_FIELDS),
        "claim_boundary": "Offline target export only; no API calls and no answer-accuracy claim.",
    }
    return rows, summary
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m unittest tests.test_r001_selective_promptedge_policy.R001SelectivePromptEdgePolicyTests.test_selective_export_marks_switch_rows_without_forbidden_fields -v`

Expected: PASS.

---

### Task 3: CLI Artifacts and PyG Export Smoke

**Files:**
- Modify: `experiment/aqua/r001_selective_promptedge_policy_export.py`
- Modify: `tests/test_r001_selective_promptedge_policy.py`

**Interfaces:**
- Consumes: `build_selective_promptedge_policy_rows(...)`
- Produces files:
  - `experiment/aqua/aqua_first200_r163_selective_promptedge_policy_rows.jsonl`
  - `experiment/aqua/res_logs/aqua_first200_r163_selective_promptedge_policy_summary.json`
  - `experiment/aqua/run_logs/aqua_first200_r163_selective_promptedge_policy_report.md`
  - `experiment/FinetuneData_AQuA_R163_selective_promptedge/*.pt`

- [ ] **Step 1: Write the failing CLI/export test**

Append to `tests/test_r001_selective_promptedge_policy.py`:

```python
    def test_real_r077_r112_export_creates_selective_pt_files(self):
        import tempfile
        from experiment.aqua.graph_objective_pairwise_export import load_jsonl_rows
        from experiment.aqua.r001_selective_promptedge_policy_export import (
            build_selective_promptedge_policy_rows,
            export_selective_positive_pt_dataset,
        )

        r077 = load_jsonl_rows("experiment/aqua/aqua_first200_r077_clean_fix_graph_policy_distill_rows.jsonl")
        r112 = load_jsonl_rows("experiment/aqua/aqua_first200_r112_objective_safety_feature_targets.jsonl")
        rows, summary = build_selective_promptedge_policy_rows(r077, r112)
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest, pt_summary = export_selective_positive_pt_dataset(rows, tmpdir)

        self.assertEqual(summary["selector_input_forbidden_field_violations"], 0)
        self.assertGreater(summary["selective_insert_rows"], 0)
        self.assertEqual(len(manifest), pt_summary["exported_pt_files"])
        self.assertEqual(pt_summary["outcome_field_violations"], 0)
        self.assertEqual(pt_summary["promptnode_edge_permission_pt_files"], pt_summary["exported_pt_files"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m unittest tests.test_r001_selective_promptedge_policy.R001SelectivePromptEdgePolicyTests.test_real_r077_r112_export_creates_selective_pt_files -v`

Expected: FAIL with missing `export_selective_positive_pt_dataset`.

- [ ] **Step 3: Implement artifact writers**

Add to `experiment/aqua/r001_selective_promptedge_policy_export.py`:

```python
def _to_pt_export_rows(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    export_rows = []
    for index, row in enumerate(rows):
        if row.get("selective_action") != "insert_promptnode_graph":
            continue
        export_rows.append(
            {
                "task_id": f"r163_selective_{index:04d}",
                "slice_prefix": row.get("source_slice_prefix"),
                "candidate_method": row.get("source_candidate_method"),
                "policy_input": row.get("selector_policy_input") or {},
                "graph_policy_target": row.get("graph_policy_target") or {},
            }
        )
    return export_rows


def export_selective_positive_pt_dataset(rows: Sequence[Dict[str, Any]], output_dir: str):
    return export_positive_policy_pt_dataset(_to_pt_export_rows(rows), output_dir)
```

Also add JSON/JSONL/report helpers and `main()` that loads defaults and writes artifacts.

- [ ] **Step 4: Run focused tests**

Run: `.venv/bin/python -m unittest tests.test_r001_selective_promptedge_policy -v`

Expected: PASS.

- [ ] **Step 5: Run the R163 export command**

Run:

```bash
.venv/bin/python experiment/aqua/r001_selective_promptedge_policy_export.py \
  --r077-jsonl experiment/aqua/aqua_first200_r077_clean_fix_graph_policy_distill_rows.jsonl \
  --r112-jsonl experiment/aqua/aqua_first200_r112_objective_safety_feature_targets.jsonl \
  --output-jsonl experiment/aqua/aqua_first200_r163_selective_promptedge_policy_rows.jsonl \
  --pt-output-dir experiment/FinetuneData_AQuA_R163_selective_promptedge \
  --manifest-jsonl experiment/aqua/aqua_first200_r163_selective_promptedge_pt_manifest.jsonl \
  --summary-json experiment/aqua/res_logs/aqua_first200_r163_selective_promptedge_policy_summary.json \
  --report-md experiment/aqua/run_logs/aqua_first200_r163_selective_promptedge_policy_report.md
```

Expected: exit code 0 and summary reports `selector_input_forbidden_field_violations=0`.

---

### Task 4: R163 Documentation and Tracker Update

**Files:**
- Modify: `refine-logs/EXPERIMENT_TRACKER.md`
- Create or update: `experiment/aqua/run_logs/aqua_first200_r163_selective_promptedge_policy_report.md`

**Interfaces:**
- Consumes: R163 summary JSON.
- Produces: tracker row R163.

- [ ] **Step 1: Add tracker row**

Append a row to `refine-logs/EXPERIMENT_TRACKER.md`:

```markdown
| R163 | M11 | R001-style selective PromptNode/PromptEdge policy export | offline non-test target export for selective first-class PromptNode insertion and typed PromptEdge metadata | AQuA first200 policy targets | selective insert rows, fallback rows, forbidden-field violations, `.pt` export count | MUST-BEFORE-TRAIN | DONE_PARTIAL | No API and no answer-accuracy claim. This prepares R164 training smoke from R001-compatible graph-policy targets; next audit remains R165. See `experiment/aqua/run_logs/aqua_first200_r163_selective_promptedge_policy_report.md`. |
```

- [ ] **Step 2: Verify report and tracker**

Run:

```bash
rg -n "R163|selective PromptNode/PromptEdge|forbidden-field" refine-logs/EXPERIMENT_TRACKER.md experiment/aqua/run_logs/aqua_first200_r163_selective_promptedge_policy_report.md
```

Expected: finds the tracker row and report claim boundary.

- [ ] **Step 3: Run final focused verification**

Run:

```bash
.venv/bin/python -m unittest tests.test_r001_selective_promptedge_policy tests.test_prompt_node_roles tests.test_graph_policy_pt_export -v
```

Expected: PASS.

## Self-Review

- Spec coverage: Task 1 covers PromptEdge metadata; Task 2 covers selective non-leaky policy target construction; Task 3 covers `.pt` compatibility; Task 4 records R163 and keeps R165 audit alignment.
- Placeholder scan: no `TBD`, `TODO`, or vague implementation step remains.
- Type consistency: `build_selective_promptedge_policy_rows`, `export_selective_positive_pt_dataset`, and PromptEdge helper names are consistent across tasks.
- Known limitation: this plan does not train the graph generator. R164 should run the training smoke or short fine-tune after R163 export verifies cleanly.
