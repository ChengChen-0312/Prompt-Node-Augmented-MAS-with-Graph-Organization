import argparse
import datetime
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, Iterable, List, Sequence, Tuple


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_bad_exact_gate import (  # noqa: E402
    build_bad_exact_features,
    decide_bad_exact_gate,
)
from experiment.aqua.forced_template_gate_r058_stress import (  # noqa: E402
    DEFAULT_BASELINE_RESULTS,
    _load_jsonl_by_task,
    _repo_path,
)
from experiment.aqua.forced_template_smoke_gate import FORBIDDEN_DECISION_FIELDS  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r092_bad_exact_gate_forced_tail34_validation"
CLAIM_BOUNDARY = "full tail34 forced-template validation with frozen R088 gate"

DEFAULT_FORCED_RUNS = [
    (
        "experiment/aqua/aqua_tail34_r092_forced_template_rank1_results.jsonl",
        "experiment/aqua/res_logs/aqua_tail34_r092_forced_template_rank1_summary.jsonl",
    )
]
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r092_bad_exact_gate_forced_tail34_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r092_bad_exact_gate_forced_tail34_report.md"


def _load_jsonl_records(path: str) -> List[Dict[str, Any]]:
    records = []
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    if not records:
        raise ValueError(f"No JSONL records in {path}")
    return records


def _load_last_jsonl(path: str) -> Dict[str, Any]:
    last = None
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                last = json.loads(line)
    if last is None:
        raise ValueError(f"No JSONL records in {path}")
    return last


def _iter_forced_records(
    forced_runs: Sequence[Tuple[str, str]],
) -> Iterable[Tuple[Dict[str, Any], str]]:
    for result_path, _summary_path in forced_runs:
        for record in _load_jsonl_records(result_path):
            yield record, result_path


def _sum_summary_field(forced_runs: Sequence[Tuple[str, str]], field: str) -> float:
    total = 0.0
    seen = set()
    for _result_path, summary_path in forced_runs:
        if summary_path in seen:
            continue
        seen.add(summary_path)
        total += float(_load_last_jsonl(summary_path).get(field) or 0.0)
    return total


def build_forced_tail34_gate_rows(
    forced_runs: Sequence[Tuple[str, str]] = DEFAULT_FORCED_RUNS,
    baseline_results: str = DEFAULT_BASELINE_RESULTS,
) -> List[Dict[str, Any]]:
    baseline = _load_jsonl_by_task(baseline_results)
    rows = []
    seen_tasks = set()
    for prompt_record, result_path in _iter_forced_records(forced_runs):
        task_id = prompt_record["task_id"]
        if task_id in seen_tasks:
            raise ValueError(f"Duplicate forced-template task record: {task_id}")
        seen_tasks.add(task_id)
        base_record = baseline[task_id]
        features = build_bad_exact_features(prompt_record)
        decision = decide_bad_exact_gate(features)
        final_record = prompt_record if decision["action"] == "accept_template" else base_record
        rows.append(
            {
                "task_id": task_id,
                "baseline_prediction": base_record.get("predicted_answer"),
                "forced_template_prediction": prompt_record.get("predicted_answer"),
                "gate_prediction": final_record.get("predicted_answer"),
                "true_answer": prompt_record.get("true_answer"),
                "baseline_is_solved": bool(base_record.get("is_solved")),
                "forced_template_is_solved": bool(prompt_record.get("is_solved")),
                "gate_is_solved": bool(final_record.get("is_solved")),
                "gate_action": decision["action"],
                "gate_reason": decision["reason"],
                "decision_features": features,
                "decision_field_violation_count": len(
                    FORBIDDEN_DECISION_FIELDS.intersection(features)
                ),
                "result_path": result_path,
            }
        )
    return rows


def _fix_harm(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    return {
        "fix": sum(
            1 for row in rows if not row["baseline_is_solved"] and row["gate_is_solved"]
        ),
        "harm": sum(
            1 for row in rows if row["baseline_is_solved"] and not row["gate_is_solved"]
        ),
    }


def build_forced_tail34_gate_summary(
    forced_runs: Sequence[Tuple[str, str]] = DEFAULT_FORCED_RUNS,
) -> Dict[str, Any]:
    rows = build_forced_tail34_gate_rows(forced_runs)
    accepted = [row for row in rows if row["gate_action"] == "accept_template"]
    fallback = [row for row in rows if row["gate_action"] == "fallback_to_arg"]
    fix_tasks = [
        row["task_id"] for row in rows if not row["baseline_is_solved"] and row["gate_is_solved"]
    ]
    harm_tasks = [
        row["task_id"] for row in rows if row["baseline_is_solved"] and not row["gate_is_solved"]
    ]
    prevented_harm_tasks = [
        row["task_id"]
        for row in rows
        if row["baseline_is_solved"] and not row["forced_template_is_solved"] and row["gate_is_solved"]
    ]
    baseline_wrong_still_wrong_tasks = [
        row["task_id"]
        for row in rows
        if not row["baseline_is_solved"] and not row["gate_is_solved"]
    ]
    return {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "num_tasks": len(rows),
        "baseline_solved": sum(1 for row in rows if row["baseline_is_solved"]),
        "forced_template_solved": sum(1 for row in rows if row["forced_template_is_solved"]),
        "gate_solved": sum(1 for row in rows if row["gate_is_solved"]),
        "gate_fix_harm": _fix_harm(rows),
        "fix_tasks": fix_tasks,
        "harm_tasks": harm_tasks,
        "prevented_harm_tasks": prevented_harm_tasks,
        "baseline_wrong_still_wrong_tasks": baseline_wrong_still_wrong_tasks,
        "accepted_rows": len(accepted),
        "fallback_rows": len(fallback),
        "accepted_tasks": [row["task_id"] for row in accepted],
        "fallback_tasks": [row["task_id"] for row in fallback],
        "gate_action_counts": dict(Counter(row["gate_action"] for row in rows)),
        "gate_reason_counts": dict(Counter(row["gate_reason"] for row in rows)),
        "decision_field_violations": sum(
            row["decision_field_violation_count"] for row in rows
        ),
        "total_forced_template_cost": _sum_summary_field(forced_runs, "cost"),
        "total_prompt_tokens": int(_sum_summary_field(forced_runs, "prompt_tokens")),
        "total_completion_tokens": int(_sum_summary_field(forced_runs, "completion_tokens")),
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "| `{task}` | `{base}` | `{forced}` | `{gate}` | `{gold}` | `{action}` | `{reason}` |".format(
            task=row["task_id"],
            base=row["baseline_prediction"],
            forced=row["forced_template_prediction"],
            gate=row["gate_prediction"],
            gold=row["true_answer"],
            action=row["gate_action"],
            reason=row["gate_reason"],
        )
        for row in summary["rows"]
    ]
    return "\n".join(
        [
            "# R092 Bad-Exact Gate Forced-Template Tail34 Report",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Tasks: `{summary['num_tasks']}`",
            f"- ARG baseline solved: `{summary['baseline_solved']}/{summary['num_tasks']}`",
            f"- Forced-template solved: `{summary['forced_template_solved']}/{summary['num_tasks']}`",
            f"- R088-gated solved: `{summary['gate_solved']}/{summary['num_tasks']}`",
            f"- Gate fix/harm vs ARG: `{summary['gate_fix_harm']}`",
            f"- Fix tasks: `{summary['fix_tasks']}`",
            f"- Harm tasks: `{summary['harm_tasks']}`",
            f"- Prevented-harm tasks: `{summary['prevented_harm_tasks']}`",
            f"- Baseline-wrong still wrong: `{summary['baseline_wrong_still_wrong_tasks']}`",
            f"- Gate actions: `{summary['gate_action_counts']}`",
            f"- Gate reasons: `{summary['gate_reason_counts']}`",
            f"- Decision-field violations: `{summary['decision_field_violations']}`",
            f"- Total forced-template cost: `${summary['total_forced_template_cost']:.6f}`",
            "",
            "| Task | ARG | Forced template | Gate | Gold | Gate action | Gate reason |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            *rows,
            "",
            "## Interpretation",
            "",
            "This report applies the frozen R088 bad-exact-contract gate to forced-template PromptNode "
            "records. A positive result can support broader held-out validation only if it exceeds the "
            "ARG baseline without introducing observed harm; otherwise the forced rank-1 template policy "
            "should return to template selection or graph-policy training. The current full tail34 result "
            "is negative for the frozen R088/R091 gate because it preserves one fix but introduces two harms.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay the frozen R088 gate on forced-template tail34 records.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--forced-results", default=DEFAULT_FORCED_RUNS[0][0])
    parser.add_argument("--forced-summary", default=DEFAULT_FORCED_RUNS[0][1])
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_forced_tail34_gate_summary(
        forced_runs=[(args.forced_results, args.forced_summary)]
    )
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built forced-template tail34 gate report: "
        f"baseline={summary['baseline_solved']}/{summary['num_tasks']} "
        f"forced={summary['forced_template_solved']}/{summary['num_tasks']} "
        f"gate={summary['gate_solved']}/{summary['num_tasks']} "
        f"cost=${summary['total_forced_template_cost']:.6f}"
    )


if __name__ == "__main__":
    main()
