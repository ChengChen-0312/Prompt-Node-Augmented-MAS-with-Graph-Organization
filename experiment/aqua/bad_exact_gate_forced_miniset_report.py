import argparse
import datetime
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List, Sequence, Tuple


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


RULE_NAME = "r091_bad_exact_gate_forced_miniset"
CLAIM_BOUNDARY = "five-task forced-template mini-set, not tail34 accuracy"

DEFAULT_FORCED_RUNS = [
    (
        "task56",
        "experiment/aqua/aqua_tail34_r084_forced_template_rank1_task56_smoke_results.jsonl",
        "experiment/aqua/res_logs/aqua_tail34_r084_forced_template_rank1_task56_smoke_summary.jsonl",
    ),
    (
        "task188",
        "experiment/aqua/aqua_tail34_r085_forced_template_rank1_task188_smoke_results.jsonl",
        "experiment/aqua/res_logs/aqua_tail34_r085_forced_template_rank1_task188_smoke_summary.jsonl",
    ),
    (
        "task8",
        "experiment/aqua/aqua_tail34_r085_forced_template_rank1_task8_smoke_results.jsonl",
        "experiment/aqua/res_logs/aqua_tail34_r085_forced_template_rank1_task8_smoke_summary.jsonl",
    ),
    (
        "task114",
        "experiment/aqua/aqua_tail34_r084_forced_template_rank1_router_hardened_smoke1_results.jsonl",
        "experiment/aqua/res_logs/aqua_tail34_r084_forced_template_rank1_router_hardened_smoke1_summary.jsonl",
    ),
    (
        "task108",
        "experiment/aqua/aqua_tail34_r090_forced_template_rank1_task108_smoke_results.jsonl",
        "experiment/aqua/res_logs/aqua_tail34_r090_forced_template_rank1_task108_smoke_summary.jsonl",
    ),
]

DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r091_bad_exact_gate_forced_miniset_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r091_bad_exact_gate_forced_miniset_report.md"


def _load_first_jsonl(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                return json.loads(line)
    raise ValueError(f"No JSONL records in {path}")


def _load_last_jsonl(path: str) -> Dict[str, Any]:
    last = None
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                last = json.loads(line)
    if last is None:
        raise ValueError(f"No JSONL records in {path}")
    return last


def build_forced_miniset_rows(
    forced_runs: Sequence[Tuple[str, str, str]] = DEFAULT_FORCED_RUNS,
    baseline_results: str = DEFAULT_BASELINE_RESULTS,
) -> List[Dict[str, Any]]:
    baseline = _load_jsonl_by_task(baseline_results)
    rows = []
    for run_name, result_path, summary_path in forced_runs:
        prompt_record = _load_first_jsonl(result_path)
        cost_record = _load_last_jsonl(summary_path)
        base_record = baseline[prompt_record["task_id"]]
        features = build_bad_exact_features(prompt_record)
        decision = decide_bad_exact_gate(features)
        final_record = prompt_record if decision["action"] == "accept_template" else base_record
        rows.append(
            {
                "run_name": run_name,
                "task_id": prompt_record["task_id"],
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
                "cost": float(cost_record.get("cost") or 0.0),
                "prompt_tokens": int(cost_record.get("prompt_tokens") or 0),
                "completion_tokens": int(cost_record.get("completion_tokens") or 0),
                "result_path": result_path,
                "summary_path": summary_path,
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


def build_forced_miniset_summary() -> Dict[str, Any]:
    rows = build_forced_miniset_rows()
    accepted = [row for row in rows if row["gate_action"] == "accept_template"]
    fallback = [row for row in rows if row["gate_action"] == "fallback_to_arg"]
    return {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "num_tasks": len(rows),
        "baseline_solved": sum(1 for row in rows if row["baseline_is_solved"]),
        "forced_template_solved": sum(1 for row in rows if row["forced_template_is_solved"]),
        "gate_solved": sum(1 for row in rows if row["gate_is_solved"]),
        "gate_fix_harm": _fix_harm(rows),
        "accepted_tasks": [row["task_id"] for row in accepted],
        "fallback_tasks": [row["task_id"] for row in fallback],
        "gate_action_counts": dict(Counter(row["gate_action"] for row in rows)),
        "gate_reason_counts": dict(Counter(row["gate_reason"] for row in rows)),
        "decision_field_violations": sum(
            row["decision_field_violation_count"] for row in rows
        ),
        "total_forced_template_cost": sum(row["cost"] for row in rows),
        "total_prompt_tokens": sum(row["prompt_tokens"] for row in rows),
        "total_completion_tokens": sum(row["completion_tokens"] for row in rows),
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{task}` | `{base}` | `{forced}` | `{gate}` | `{gold}` | `{action}` | `{reason}` | `${cost:.6f}` |".format(
            task=row["task_id"],
            base=row["baseline_prediction"],
            forced=row["forced_template_prediction"],
            gate=row["gate_prediction"],
            gold=row["true_answer"],
            action=row["gate_action"],
            reason=row["gate_reason"],
            cost=row["cost"],
        )
        for row in summary["rows"]
    ]
    return "\n".join(
        [
            "# R091 Bad-Exact Gate Forced-Template Mini-Set Report",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Tasks: `{summary['num_tasks']}`",
            f"- ARG baseline solved: `{summary['baseline_solved']}/{summary['num_tasks']}`",
            f"- Forced-template solved: `{summary['forced_template_solved']}/{summary['num_tasks']}`",
            f"- R088-gated solved: `{summary['gate_solved']}/{summary['num_tasks']}`",
            f"- Gate fix/harm vs ARG: `{summary['gate_fix_harm']}`",
            f"- Accepted tasks: `{summary['accepted_tasks']}`",
            f"- Fallback tasks: `{summary['fallback_tasks']}`",
            f"- Total forced-template cost: `${summary['total_forced_template_cost']:.6f}`",
            f"- Decision-field violations: `{summary['decision_field_violations']}`",
            "",
            "| Task | ARG | Forced template | Gate | Gold | Gate action | Gate reason | Cost |",
            "| --- | --- | --- | --- | --- | --- | --- | ---: |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "The current five forced-template smoke records show the first small positive pattern for the R088 gate: "
            "it keeps the `task_108` fresh fix, falls back on weak or unsupported cases, and introduces no observed "
            "harm against the ARG baseline. The set was assembled from iterative smoke tasks, so it cannot be used "
            "as a tail34 accuracy claim.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize the R088 gate over the forced-template mini-set.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_forced_miniset_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built forced-template mini-set report: "
        f"baseline={summary['baseline_solved']}/{summary['num_tasks']} "
        f"forced={summary['forced_template_solved']}/{summary['num_tasks']} "
        f"gate={summary['gate_solved']}/{summary['num_tasks']} "
        f"cost=${summary['total_forced_template_cost']:.6f}"
    )


if __name__ == "__main__":
    main()
