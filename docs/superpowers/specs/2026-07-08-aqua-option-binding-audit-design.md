# AQuA Option-Binding Audit Design

## Goal

Determine whether AQuA rows are clean, noisy, or ambiguous before claiming that
PromptNode graph organization improves accuracy.

## Motivation

Repeated sync20 experiments tie or underperform ARG-Designer. The same three rows
remain wrong:

- `task_152`: official rationale has an arithmetic contradiction.
- `task_199`: official rationale uses an unclear event definition.
- `task_172`: official rationale appears to answer the distance-difference fact
  rather than the stated XY distance target.

Further sync20 prompt tuning risks chasing label noise. R024 audits the data
quality first.

## Audit Contract

For each row, the auditor sees:

- task text
- A-E choices
- gold label and gold option text
- official rationale
- optional baseline/PN predictions and raw responses

The auditor must return JSON:

```json
{
  "clean_label": "clean|noisy|ambiguous",
  "gold_binding_status": "exact|equivalent|unsupported|contradictory|unknown",
  "target_preserved": true,
  "option_mismatch": false,
  "rationale_issue": "none|arithmetic_error|shifted_target|underspecified_event|invalid_logic|unknown",
  "faithful_answer": "A|B|C|D|E|NONE|UNKNOWN",
  "confidence": "high|medium|low",
  "brief_reason": "..."
}
```

This audit is not used for model prediction and must not be fed into eval-time
agents. It is a paper-integrity and experiment-design artifact.

## Implementation

Add `experiment/aqua/audit_option_binding.py`:

- `build_audit_prompt(record, task_id, result_records=None)`
- `parse_audit_response(text)`
- `make_audit_record(task_id, processed_record, raw_record, audit_json, result_records)`
- async CLI that writes JSONL and summary JSON

## Success Criteria

Run on sync20 first:

- output: `experiment/aqua/aqua_sync20_option_binding_audit.jsonl`
- summary: clean/noisy/ambiguous counts
- run log: `experiment/aqua/run_logs/aqua_sync20_option_binding_audit.md`

Then use the clean/noisy split to decide whether further PN experiments should
target a larger clean subset or pivot to a cleaner benchmark.
