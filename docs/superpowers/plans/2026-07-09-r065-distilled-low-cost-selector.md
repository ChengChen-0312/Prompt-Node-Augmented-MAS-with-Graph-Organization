# R065-Distilled Low-Cost Selector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a no-API distillation package that turns R065's expensive AQuA tail34 multi-view teacher into paper-ready tables and a candidate low-cost student selector.

**Architecture:** The implementation follows existing AQuA run-log patterns: focused scripts under `experiment/aqua/`, tests under `tests/`, machine-readable summaries under `experiment/aqua/res_logs/`, and reports under `experiment/aqua/run_logs/`. R262 summarizes existing runs; R263 exports feature rows and evaluates interpretable student gate candidates.

**Tech Stack:** Python 3.12, standard library JSON/CSV collections, existing JSONL artifacts, `unittest`. No new dependency and no API call.

## Global Constraints

- No API calls in R262 or R263.
- Do not use true answers, correctness, clean/noisy audit labels, or task ids as model-visible selector features.
- Tail34 is frozen evaluation; it may be scored, but not used as training-label source for a deployable selector.
- Preserve R065 claim boundary: `31/34` is a teacher/replay ceiling, not a fresh integrated low-cost result.
- The workspace is not a git repository, so commit steps are skipped in this directory.

---

### Task 1: R262 Paper-Ready Result Tables

**Files:**
- Create: `tests/test_r262_aqua_paper_ready_tables.py`
- Create: `experiment/aqua/r262_paper_ready_result_tables.py`
- Create output: `experiment/aqua/run_logs/aqua_r262_paper_ready_result_tables.md`
- Create output: `experiment/aqua/res_logs/aqua_r262_paper_ready_result_tables_summary.json`
- Modify: `refine-logs/EXPERIMENT_TRACKER.md`

**Interfaces:**
- Consumes: existing summary/report files for R065/R068/R069/R072/R147 and `PAPER_PLAN.md`.
- Produces: `build_result_table(rows: list[dict]) -> list[dict]`, `assess_cost_boundary(rows: list[dict]) -> dict`, and `run_table_export(...) -> dict`.

- [ ] **Step 1: Write the failing test**

```python
import unittest

from experiment.aqua.r262_paper_ready_result_tables import (
    assess_cost_boundary,
    build_result_table,
)


class TestR262AquaPaperReadyTables(unittest.TestCase):
    def test_table_computes_delta_and_cost_ratio(self):
        rows = [
            {"run_id": "ARG", "accuracy": "28/34", "cost": 0.934},
            {"run_id": "R065", "accuracy": "31/34", "cost": 5.05},
        ]
        table = build_result_table(rows)
        r065 = [row for row in table if row["run_id"] == "R065"][0]

        self.assertEqual(r065["delta_vs_arg_correct"], 3)
        self.assertGreater(r065["cost_ratio_vs_arg"], 5.0)

    def test_cost_boundary_flags_expensive_teacher(self):
        summary = assess_cost_boundary(
            [
                {"run_id": "R065", "correct": 31, "total": 34, "cost": 5.05},
                {"run_id": "R072", "correct": 29, "total": 34, "cost": 2.82},
            ]
        )

        self.assertEqual(summary["best_accuracy_run"], "R065")
        self.assertEqual(summary["best_fresh_cost_run"], "R072")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m unittest tests.test_r262_aqua_paper_ready_tables`

Expected: `ModuleNotFoundError: No module named 'experiment.aqua.r262_paper_ready_result_tables'`.

- [ ] **Step 3: Implement the table exporter**

Implement `experiment/aqua/r262_paper_ready_result_tables.py` with:

```python
from __future__ import annotations

import argparse
import json
import os
from typing import Any


def parse_accuracy(value: str) -> tuple[int, int]:
    left, right = str(value).split("/", 1)
    return int(left), int(right)


def build_result_table(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    arg = next(row for row in rows if row["run_id"] == "ARG")
    arg_correct, arg_total = parse_accuracy(arg["accuracy"])
    arg_cost = float(arg.get("cost") or 0.0)
    table = []
    for row in rows:
        correct, total = parse_accuracy(row["accuracy"])
        cost = float(row.get("cost") or 0.0)
        out = dict(row)
        out.update(
            {
                "correct": correct,
                "total": total,
                "delta_vs_arg_correct": correct - arg_correct,
                "cost_ratio_vs_arg": round(cost / arg_cost, 6) if arg_cost else None,
            }
        )
        table.append(out)
    return table
```

Add render/report/CLI following existing report style.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m unittest tests.test_r262_aqua_paper_ready_tables`

Expected: `OK`.

- [ ] **Step 5: Run R262 export**

Run:

```bash
.venv/bin/python experiment/aqua/r262_paper_ready_result_tables.py \
  --summary_json experiment/aqua/res_logs/aqua_r262_paper_ready_result_tables_summary.json \
  --report_md experiment/aqua/run_logs/aqua_r262_paper_ready_result_tables.md
```

Expected: JSON summary with R065/R068/R069/R072/R147 rows and cost boundaries.

- [ ] **Step 6: Update tracker**

Append R262 to `refine-logs/EXPERIMENT_TRACKER.md` with status `TABLES`.

---

### Task 2: R263 Distillation Feature Table And Student Gate Search

**Files:**
- Create: `tests/test_r263_r065_distillation.py`
- Create: `experiment/aqua/r263_r065_distillation.py`
- Create output: `experiment/aqua/aqua_r263_r065_distillation_feature_table.jsonl`
- Create output: `experiment/aqua/run_logs/aqua_r263_r065_distillation_report.md`
- Create output: `experiment/aqua/res_logs/aqua_r263_r065_distillation_summary.json`
- Modify: `refine-logs/EXPERIMENT_TRACKER.md`

**Interfaces:**
- Consumes: `experiment/aqua/aqua_tail34_objective_guided_selector_results.jsonl`, `experiment/aqua/aqua_tail34_arg_baseline_results.jsonl`, `experiment/aqua/aqua_tail34_r068_selective_multiview_results.jsonl`, and audit JSONL if available.
- Produces: `build_feature_row(source: dict) -> dict`, `evaluate_gate(rows: list[dict], spec: dict) -> dict`, `search_gate_specs(rows: list[dict]) -> list[dict]`.

- [ ] **Step 1: Write the failing test**

```python
import unittest

from experiment.aqua.r263_r065_distillation import evaluate_gate, search_gate_specs


class TestR263R065Distillation(unittest.TestCase):
    def test_evaluate_gate_counts_trigger_cost_and_fix_harm(self):
        rows = [
            {
                "task_id": "a",
                "arg_correct": False,
                "teacher_correct": True,
                "teacher_would_fix": True,
                "teacher_would_harm": False,
                "features": {"risk_score": 2},
            },
            {
                "task_id": "b",
                "arg_correct": True,
                "teacher_correct": True,
                "teacher_would_fix": False,
                "teacher_would_harm": False,
                "features": {"risk_score": 0},
            },
        ]
        result = evaluate_gate(rows, {"name": "risk_ge_1", "risk_min": 1}, promptnode_cost_per_trigger=0.1)

        self.assertEqual(result["selected_correct"], 2)
        self.assertEqual(result["triggers"], 1)
        self.assertEqual(result["fixes"], 1)
        self.assertEqual(result["harms"], 0)

    def test_search_returns_sorted_candidates(self):
        rows = [
            {"arg_correct": False, "teacher_correct": True, "teacher_would_fix": True, "teacher_would_harm": False, "features": {"risk_score": 2}},
            {"arg_correct": True, "teacher_correct": True, "teacher_would_fix": False, "teacher_would_harm": False, "features": {"risk_score": 0}},
        ]
        candidates = search_gate_specs(rows)

        self.assertEqual(candidates[0]["harms"], 0)
        self.assertGreaterEqual(candidates[0]["selected_correct"], 2)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m unittest tests.test_r263_r065_distillation`

Expected: `ModuleNotFoundError: No module named 'experiment.aqua.r263_r065_distillation'`.

- [ ] **Step 3: Implement gate evaluation**

Implement:

```python
def gate_triggers(features: dict[str, Any], spec: dict[str, Any]) -> bool:
    risk_min = int(spec.get("risk_min", 0))
    top_min = int(spec.get("objective_top_score_min", 0))
    return int(features.get("risk_score", 0)) >= risk_min and int(features.get("objective_top_score", 0)) >= top_min
```

`evaluate_gate` should use teacher prediction only when the gate triggers; otherwise it uses ARG. It must report selected accuracy, fix/harm, trigger count, estimated cost, and whether success criteria pass.

- [ ] **Step 4: Implement feature export**

Feature rows must include:

```python
{
  "task_id": "...",
  "features": {
    "risk_score": 0,
    "arg_invalid": false,
    "objective_top_score": 0,
    "objective_differs_from_arg": false,
    "r068_triggered": false
  },
  "labels_not_model_visible": {
    "arg_correct": true,
    "teacher_correct": true,
    "teacher_source": "baseline|objective_top"
  }
}
```

The model-visible `features` dict must not include `true_answer`, `is_correct`, `clean_label`, or `task_id`.

- [ ] **Step 5: Run tests**

Run: `.venv/bin/python -m unittest tests.test_r263_r065_distillation`

Expected: `OK`.

- [ ] **Step 6: Run R263 export/search**

Run:

```bash
.venv/bin/python experiment/aqua/r263_r065_distillation.py \
  --arg_jsonl experiment/aqua/aqua_tail34_arg_baseline_results.jsonl \
  --teacher_jsonl experiment/aqua/aqua_tail34_objective_guided_selector_results.jsonl \
  --r068_jsonl experiment/aqua/aqua_tail34_r068_selective_multiview_results.jsonl \
  --output_jsonl experiment/aqua/aqua_r263_r065_distillation_feature_table.jsonl \
  --summary_json experiment/aqua/res_logs/aqua_r263_r065_distillation_summary.json \
  --report_md experiment/aqua/run_logs/aqua_r263_r065_distillation_report.md
```

Expected: summary lists candidate gates and whether any meet the R065-distillation success criteria.

- [ ] **Step 7: Update tracker**

Append R263 to `refine-logs/EXPERIMENT_TRACKER.md` with status `DISTILLATION`.

---

## Self-Review

- Spec coverage: Tasks cover paper tables, feature export, candidate gate search, and no-API claim boundaries.
- Placeholder scan: No TBD/TODO placeholders remain.
- Type consistency: `build_result_table`, `assess_cost_boundary`, `evaluate_gate`, and `search_gate_specs` are defined before use.
- Scope: This plan stops before fresh API. Fresh API requires a later preflight if R263 passes.
