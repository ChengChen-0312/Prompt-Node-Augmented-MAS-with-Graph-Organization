# AQuA Option-Binding Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible LLM-assisted audit that labels AQuA rows as clean, noisy, or ambiguous.

**Architecture:** Pure prompt/parser helpers are tested without API calls. The CLI loads AQuA rows and prior result files, calls the configured LLM asynchronously, writes JSONL, and emits a compact summary.

**Tech Stack:** Python, unittest, existing `LLMRegistry`, AQuA JSONL files.

## Global Constraints

- Audit output is for analysis only; it must not be used to pick eval answers.
- No task-id correction rules.
- Preserve raw LLM audit text when parsing fails.
- Sync20 audit runs with `gpt-4o-2024-08-06` unless explicitly changed.

---

### Task 1: Prompt/Parser Helpers

**Files:**
- Create: `experiment/aqua/audit_option_binding.py`
- Test: `tests/test_aqua_option_binding_audit.py`

**Interfaces:**
- `build_audit_prompt(processed_record, raw_record, task_id, result_records=None) -> list[dict]`
- `parse_audit_response(text) -> dict`

Steps:

1. Write tests for prompt content and JSON extraction from fenced/plain responses.
2. Run targeted tests and confirm missing module failure.
3. Implement helpers.
4. Run targeted tests.

### Task 2: Record/Summary Helpers

**Files:**
- Modify: `experiment/aqua/audit_option_binding.py`
- Test: `tests/test_aqua_option_binding_audit.py`

**Interfaces:**
- `make_audit_record(...) -> dict`
- `summarize_audits(records) -> dict`

Steps:

1. Write tests for clean/noisy count summary and prior-result attachment.
2. Run targeted tests and confirm missing function failure.
3. Implement helpers.
4. Run targeted tests.

### Task 3: Sync20 Audit Run

Command:

```bash
cd experiment/aqua
set -a
source /Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env
set +a
../../.venv/bin/python audit_option_binding.py \
  --llm_name gpt-4o-2024-08-06 \
  --limit 20 \
  --output_file aqua_sync20_option_binding_audit.jsonl \
  --summary_file res_logs/aqua_sync20_option_binding_audit_summary.json \
  --result_file aqua_sync20_eval20_results.jsonl \
  --result_file aqua_sync20_pn_candidate_select_results.jsonl
```

Then write a markdown breakdown from the JSONL output.
