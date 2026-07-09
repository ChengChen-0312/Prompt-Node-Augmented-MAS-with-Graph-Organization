import argparse
import datetime
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List, Sequence


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


RULE_NAME = "r089_bad_exact_gate_forced_smoke_replay"
CLAIM_BOUNDARY = "forced-template smoke replay, not tail34 accuracy"

DEFAULT_FORCED_SMOKE_RESULTS = [
    "experiment/aqua/aqua_tail34_r084_forced_template_rank1_task56_smoke_results.jsonl",
    "experiment/aqua/aqua_tail34_r085_forced_template_rank1_task188_smoke_results.jsonl",
    "experiment/aqua/aqua_tail34_r085_forced_template_rank1_task8_smoke_results.jsonl",
    "experiment/aqua/aqua_tail34_r084_forced_template_rank1_router_hardened_smoke1_results.jsonl",
]
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r089_bad_exact_gate_forced_smoke_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r089_bad_exact_gate_forced_smoke_report.md"


def _load_first_jsonl(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                return json.loads(line)
    raise ValueError(f"No JSONL records in {path}")


def build_forced_smoke_gate_rows(
    forced_smoke_results: Sequence[str] = DEFAULT_FORCED_SMOKE_RESULTS,
    baseline_results: str = DEFAULT_BASELINE_RESULTS,
) -> List[Dict[str, Any]]:
    baseline = _load_jsonl_by_task(baseline_results)
    rows = []
    for result_path in forced_smoke_results:
        prompt_record = _load_first_jsonl(result_path)
        base_record = baseline[prompt_record["task_id"]]
        features = build_bad_exact_features(prompt_record)
        decision = decide_bad_exact_gate(features)
        final_record = prompt_record if decision["action"] == "accept_template" else base_record
        rows.append(
            {
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


def build_forced_smoke_gate_summary() -> Dict[str, Any]:
    rows = build_forced_smoke_gate_rows()
    accepted = [row for row in rows if row["gate_action"] == "accept_template"]
    fallback = [row for row in rows if row["gate_action"] == "fallback_to_arg"]
    return {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "num_smoke_rows": len(rows),
        "baseline_solved": sum(1 for row in rows if row["baseline_is_solved"]),
        "forced_template_solved": sum(1 for row in rows if row["forced_template_is_solved"]),
        "gate_solved": sum(1 for row in rows if row["gate_is_solved"]),
        "gate_fix_harm": _fix_harm(rows),
        "accepted_rows": len(accepted),
        "fallback_rows": len(fallback),
        "accepted_tasks": [row["task_id"] for row in accepted],
        "fallback_tasks": [row["task_id"] for row in fallback],
        "gate_action_counts": dict(Counter(row["gate_action"] for row in rows)),
        "gate_reason_counts": dict(Counter(row["gate_reason"] for row in rows)),
        "decision_field_violations": sum(
            row["decision_field_violation_count"] for row in rows
        ),
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
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
            "# R089 Bad-Exact Gate on Forced-Template Smoke Report",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Smoke rows: `{summary['num_smoke_rows']}`",
            f"- ARG baseline solved: `{summary['baseline_solved']}/{summary['num_smoke_rows']}`",
            f"- Forced-template solved: `{summary['forced_template_solved']}/{summary['num_smoke_rows']}`",
            f"- R088-gated solved: `{summary['gate_solved']}/{summary['num_smoke_rows']}`",
            f"- Gate fix/harm vs ARG: `{summary['gate_fix_harm']}`",
            f"- Accepted tasks: `{summary['accepted_tasks']}`",
            f"- Fallback tasks: `{summary['fallback_tasks']}`",
            f"- Gate reasons: `{summary['gate_reason_counts']}`",
            f"- Decision-field violations: `{summary['decision_field_violations']}`",
            "",
            "| Task | ARG | Forced template | Gate | Gold | Gate action | Gate reason |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "The R088 gate is non-harmful on the current forced-template smoke set: it accepts exact trusted "
            "contracts for `task_188` and `task_8`, while falling back on weak or unsupported contracts for "
            "`task_56` and `task_114`. This remains a four-record smoke replay and does not establish tail34 "
            "accuracy.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay the R088 gate on forced-template smoke records.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_forced_smoke_gate_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built bad-exact forced-smoke report: "
        f"baseline={summary['baseline_solved']}/{summary['num_smoke_rows']} "
        f"forced={summary['forced_template_solved']}/{summary['num_smoke_rows']} "
        f"gate={summary['gate_solved']}/{summary['num_smoke_rows']}"
    )


if __name__ == "__main__":
    main()
