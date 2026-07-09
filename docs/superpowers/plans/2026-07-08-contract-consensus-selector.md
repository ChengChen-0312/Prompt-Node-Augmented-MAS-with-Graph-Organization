# Contract-Consensus Selector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the offline AQuA selector to test a PromptNode contract-consensus rule that uses virtual-node verification evidence, not only invalid-answer fallback.

**Architecture:** Add trace parsing and a fixed contract-consensus rule to `experiment/aqua/offline_utility_selector.py`. The rule reads PN agent traces, extracts strong `PN_Router` contracts and direct-node majorities, and writes replay artifacts for first100/next100/first200.

**Tech Stack:** Python standard library, existing `mas_framework.agents.final_decision` parsers, existing AQuA JSONL logs, `unittest`.

## Global Constraints

- Do not use task IDs, gold answers, clean/noisy labels, or rationales as inference features.
- Do not call any LLM/API.
- Keep invalid-answer fallback separate from PN contract-consensus behavior in the report.
- Treat first200 as exploratory unless tail34 or a new held-out benchmark is later run.

---

### Task 1: Trace Feature Extraction

**Files:**
- Modify: `experiment/aqua/offline_utility_selector.py`
- Modify: `tests/test_offline_utility_selector.py`

**Interfaces:**
- Produces: `extract_contract_consensus_features(record: dict) -> dict`

- [ ] **Step 1: Write failing test**

```python
def test_extract_contract_consensus_features_reads_router_and_direct_majority():
    from experiment.aqua.offline_utility_selector import extract_contract_consensus_features

    record = {
        "agent_outputs": [
            {"node": 0, "role": "Math Solver", "outputs": ["The answer is B"]},
            {"node": 1, "role": "Programming Expert", "outputs": ["The answer is B"]},
            {"node": 2, "role": "PN_Router", "outputs": [
                "SUPPORTED_OPTION: B\nBINDING_STATUS: EXACT_MATCH\nFINAL_EVIDENCE_SUMMARY: verified"
            ]},
        ]
    }

    features = extract_contract_consensus_features(record)
    assert features["router_option"] == "B"
    assert features["direct_majority"] == "B"
    assert features["direct_majority_count"] == 2
```

- [ ] **Step 2: Verify RED**

Run: `.venv/bin/python -m unittest tests.test_offline_utility_selector -v`

- [ ] **Step 3: Implement feature extraction**

Convert `agent_outputs` into the `spatial_info` shape used by `extract_router_contracts()` and `summarize_pn_utility_features()`.

- [ ] **Step 4: Verify GREEN**

Run: `.venv/bin/python -m unittest tests.test_offline_utility_selector -v`

### Task 2: Contract-Consensus Rule

**Files:**
- Modify: `experiment/aqua/offline_utility_selector.py`
- Modify: `tests/test_offline_utility_selector.py`

**Interfaces:**
- Produces: `apply_contract_consensus_rule(baseline_prediction, ensemble_prediction, features, min_direct_majority=2, use_invalid_fallback=True) -> tuple[prediction, source]`

- [ ] **Step 1: Write failing tests**

Test that the rule switches when router and direct majority agree, refuses a router/direct conflict, and uses ensemble only for invalid baseline.

- [ ] **Step 2: Verify RED**

Run: `.venv/bin/python -m unittest tests.test_offline_utility_selector -v`

- [ ] **Step 3: Implement rule**

Keep the rule deterministic and gold-free.

- [ ] **Step 4: Verify GREEN and full suite**

Run:

```bash
.venv/bin/python -m unittest tests.test_offline_utility_selector -v
.venv/bin/python -m unittest discover -s tests -v
```

### Task 3: Replay and Report

**Files:**
- Modify: `experiment/aqua/offline_utility_selector.py`
- Create: `experiment/aqua/aqua_contract_consensus_selector_results.jsonl`
- Create: `experiment/aqua/res_logs/aqua_contract_consensus_selector_summary.json`
- Create: `experiment/aqua/run_logs/aqua_first200_contract_consensus_selector_analysis.md`
- Modify: `refine-logs/EXPERIMENT_TRACKER.md`
- Modify: `refine-logs/MANIFEST.md`
- Modify: `.aris/claims.json`

**Interfaces:**
- Produces CLI option: `--selector contract_consensus --method-prefix pn_router_contract`

- [ ] **Step 1: Add CLI selector option**

Let the existing CLI run either `offline_rule` or `contract_consensus`.

- [ ] **Step 2: Run first200 replay**

Run contract-consensus with `pn_router_contract`, report official, clean, noisy, switches, fix/harm, and selected rows.

- [ ] **Step 3: Update evidence ledger**

Add only verifiable claims: overall accuracy, clean accuracy, noisy accuracy, fix/harm, and claim-supported status.

- [ ] **Step 4: Final verification**

Run JSON checks, targeted tests, full tests, and a direct evidence recomputation script.
