# Contract-Coverage Graph Objective Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an offline, label-free contract-coverage objective that ranks PromptNode graph variants from existing AQuA traces and reports whether it can guide future graph selection/training.

**Architecture:** Add one focused analysis module under `experiment/aqua/` and one focused test file under `tests/`. The module reuses `offline_utility_selector.extract_contract_consensus_features` and existing result JSONL files; it does not call the LLM and does not alter answer predictions.

**Tech Stack:** Python 3.12, existing `.venv`, stdlib `json`/`argparse`/`collections`, existing ARG-Designer AQuA result schemas.

## Global Constraints

- Do not use `true_answer`, clean/noisy audit labels, task IDs, or official rationales as objective inputs.
- Do not call the LLM.
- Do not change existing prediction files.
- Accuracy is diagnostic only; no new performance claim is established by R038.
- This directory is not a git repository, so verification and manifest updates replace commit steps.

---

### Task 1: Objective Scoring Unit

**Files:**
- Create: `experiment/aqua/contract_graph_objective.py`
- Test: `tests/test_contract_graph_objective.py`

**Interfaces:**
- Consumes: `extract_contract_consensus_features(record)` from `experiment.aqua.offline_utility_selector`
- Produces: `score_contract_features(features: dict, has_prompt_node_graph: bool = False) -> dict`

- [ ] **Step 1: Write the failing test**

```python
def test_score_contract_features_rewards_strong_direct_agreement_and_penalizes_conflict():
    from experiment.aqua.contract_graph_objective import score_contract_features

    score = score_contract_features(
        {
            "router_option": "B",
            "strong_router_contract_count": 1,
            "direct_majority": "B",
            "direct_majority_count": 2,
            "direct_valid_vote_count": 2,
            "router_matches_direct_majority": True,
            "router_conflicts_with_direct_majority": False,
            "all_router_contracts_weak": False,
        },
        has_prompt_node_graph=True,
    )
    conflict = score_contract_features(
        {
            "router_option": "C",
            "strong_router_contract_count": 1,
            "direct_majority": "A",
            "direct_majority_count": 3,
            "direct_valid_vote_count": 3,
            "router_matches_direct_majority": False,
            "router_conflicts_with_direct_majority": True,
            "all_router_contracts_weak": False,
        },
        has_prompt_node_graph=True,
    )

    assert score["score"] == 10
    assert score["components"]["strong_contract"] == 4
    assert conflict["score"] == 4
    assert conflict["components"]["conflict_penalty"] == -4
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m unittest tests.test_contract_graph_objective`

Expected: FAIL with `ModuleNotFoundError: No module named 'experiment.aqua.contract_graph_objective'`.

- [ ] **Step 3: Write minimal implementation**

Create `score_contract_features` with the exact component weights from the spec and return both `score` and `components`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m unittest tests.test_contract_graph_objective`

Expected: PASS.

---

### Task 2: Per-Task Variant Ranking

**Files:**
- Modify: `experiment/aqua/contract_graph_objective.py`
- Modify: `tests/test_contract_graph_objective.py`

**Interfaces:**
- Consumes: `score_contract_features`
- Produces: `rank_task_variants(task_id: str, result_sets: dict, method_keys: list[str] | None = None) -> list[dict]`

- [ ] **Step 1: Write the failing test**

```python
def test_rank_task_variants_returns_sorted_label_free_scores():
    from experiment.aqua.contract_graph_objective import rank_task_variants

    def record(role, option, direct):
        return {
            "generated_graph": {"roles": ["Math Solver", role]},
            "agent_outputs": [
                {"node": 0, "role": "Math Solver", "outputs": [f"The answer is {direct}"]},
                {"node": 1, "role": "Programming Expert", "outputs": [f"The answer is {direct}"]},
                {
                    "node": 2,
                    "role": "PN_Router",
                    "outputs": [
                        f"SUPPORTED_OPTION: {option}\n"
                        "BINDING_STATUS: EXACT_MATCH\n"
                        "FINAL_EVIDENCE_SUMMARY: verified"
                    ],
                },
            ],
            "predicted_answer": option,
            "true_answer": "A",
        }

    ranked = rank_task_variants(
        "task_x",
        {
            "router": {"task_x": record("PN_Router", "B", "B")},
            "candidate": {"task_x": record("PN_Router", "C", "A")},
        },
        method_keys=["router", "candidate"],
    )

    assert ranked[0]["method_key"] == "router"
    assert "true_answer" not in ranked[0]
    assert ranked[0]["score"] > ranked[1]["score"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m unittest tests.test_contract_graph_objective`

Expected: FAIL because `rank_task_variants` is not defined.

- [ ] **Step 3: Write minimal implementation**

Use `extract_contract_consensus_features`, detect PromptNode roles from `generated_graph.roles`, and sort by `(score, method_key)` descending/stable with lower method index as tie-break.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m unittest tests.test_contract_graph_objective`

Expected: PASS.

---

### Task 3: First200 Report Generator

**Files:**
- Modify: `experiment/aqua/contract_graph_objective.py`
- Modify: `tests/test_contract_graph_objective.py`
- Create output: `experiment/aqua/run_logs/aqua_first200_contract_graph_objective_report.md`
- Create output: `experiment/aqua/res_logs/aqua_first200_contract_graph_objective_summary.json`

**Interfaces:**
- Consumes: `load_prefix_result_sets`, `common_task_ids`, `build_multi_contract_union_records`
- Produces: CLI with `--output-md` and `--summary-json`

- [ ] **Step 1: Write the failing test**

```python
def test_build_objective_summary_counts_unique_top_and_ties():
    from experiment.aqua.contract_graph_objective import build_objective_summary

    records = [
        {"task_id": "a", "ranked_variants": [{"method_key": "router", "score": 10}, {"method_key": "candidate", "score": 4}]},
        {"task_id": "b", "ranked_variants": [{"method_key": "router", "score": 5}, {"method_key": "candidate", "score": 5}]},
    ]

    summary = build_objective_summary(records)

    assert summary["total_tasks"] == 2
    assert summary["positive_top_score_tasks"] == 2
    assert summary["unique_top_method_distribution"] == {"router": 1}
    assert summary["top_score_ties"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m unittest tests.test_contract_graph_objective`

Expected: FAIL because `build_objective_summary` is not defined.

- [ ] **Step 3: Implement summary and CLI**

The CLI should default to `aqua_100` and `aqua_next100`, write JSON and markdown, and explicitly label selected-method accuracy as diagnostic.

- [ ] **Step 4: Generate real first200 outputs**

Run:

```bash
.venv/bin/python experiment/aqua/contract_graph_objective.py \
  --output-md experiment/aqua/run_logs/aqua_first200_contract_graph_objective_report.md \
  --summary-json experiment/aqua/res_logs/aqua_first200_contract_graph_objective_summary.json
```

Expected: command exits `0`, outputs exist.

---

### Task 4: Documentation And Verification

**Files:**
- Modify: `refine-logs/EXPERIMENT_TRACKER.md`
- Modify: `refine-logs/MANIFEST.md`
- Modify: `.aris/claims.json`

**Interfaces:**
- Consumes: R038 summary JSON and markdown report.
- Produces: manifest entries and claim-index rows for objective diagnostics only.

- [ ] **Step 1: Update tracker**

Add `R038` with status `DONE_PARTIAL`, noting that this is a label-free graph objective diagnostic, not a new accuracy result.

- [ ] **Step 2: Update manifest**

Register the new script, test, report, summary, spec, and plan.

- [ ] **Step 3: Update claims**

Add only diagnostic claims: positive top-score coverage, tie count, and top-method distribution source. Do not add a new accuracy superiority claim.

- [ ] **Step 4: Run verification**

Run:

```bash
.venv/bin/python -m json.tool .aris/claims.json >/tmp/claims_r038_check.json
.venv/bin/python -m json.tool experiment/aqua/res_logs/aqua_first200_contract_graph_objective_summary.json >/tmp/r038_summary_check.json
.venv/bin/python -m unittest tests.test_contract_graph_objective tests.test_contract_ablation_analysis tests.test_offline_utility_selector
.venv/bin/python -m unittest discover -s tests
```

Expected: all commands exit `0`.
