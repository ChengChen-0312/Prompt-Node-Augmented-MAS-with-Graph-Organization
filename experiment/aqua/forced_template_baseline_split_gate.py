import argparse
import datetime
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_gate_r058_stress import (  # noqa: E402
    DEFAULT_BASELINE_RESULTS,
    _load_jsonl_by_task,
    _repo_path,
)
from experiment.aqua.forced_template_smoke_gate import FORBIDDEN_DECISION_FIELDS  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402
from experiment.aqua.offline_utility_selector import extract_contract_consensus_features  # noqa: E402


RULE_NAME = "r094_baseline_split_protected_forced_template_gate"
CLAIM_BOUNDARY = "label-free replay over R092 traces; official gain is noisy-only, not SCI main result"

DEFAULT_R092_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r092_bad_exact_gate_forced_tail34_summary.json"
DEFAULT_AUDIT_JSONL = "experiment/aqua/aqua_tail34_option_binding_audit.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r094_baseline_split_gate_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r094_baseline_split_gate_report.md"


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _load_audit_by_task(path: str) -> Dict[str, Dict[str, Any]]:
    records = {}
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                records[record["task_id"]] = record
    return records


def build_baseline_split_features(
    baseline_record: Dict[str, Any],
    r092_row: Dict[str, Any],
) -> Dict[str, Any]:
    baseline_features = extract_contract_consensus_features(baseline_record)
    direct_valid = int(baseline_features.get("direct_valid_vote_count") or 0)
    direct_majority = int(baseline_features.get("direct_majority_count") or 0)
    return {
        "forced_differs_from_baseline": (
            r092_row["forced_template_prediction"] != r092_row["baseline_prediction"]
        ),
        "r088_gate_action": r092_row["gate_action"],
        "r088_gate_reason": r092_row["gate_reason"],
        "baseline_direct_majority": baseline_features.get("direct_majority"),
        "baseline_direct_majority_count": direct_majority,
        "baseline_direct_valid_vote_count": direct_valid,
        "baseline_direct_votes_split": direct_valid > direct_majority,
    }


def decide_baseline_split_gate(features: Dict[str, Any]) -> Dict[str, str]:
    if not features["forced_differs_from_baseline"]:
        return {"action": "fallback_to_arg", "reason": "same_prediction_as_arg"}
    if features["r088_gate_action"] != "accept_template":
        return {"action": "fallback_to_arg", "reason": "r088_rejects_template"}
    if features["baseline_direct_votes_split"]:
        return {"action": "accept_template", "reason": "baseline_direct_split_allows_switch"}
    return {"action": "fallback_to_arg", "reason": "baseline_not_split_suppresses_switch"}


def _fix_harm(rows: List[Dict[str, Any]], solved_key: str) -> Dict[str, int]:
    return {
        "fix": sum(
            1 for row in rows if not row["baseline_is_solved"] and row[solved_key]
        ),
        "harm": sum(
            1 for row in rows if row["baseline_is_solved"] and not row[solved_key]
        ),
    }


def _bucket_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "num_tasks": len(rows),
        "baseline_solved": sum(1 for row in rows if row["baseline_is_solved"]),
        "forced_template_solved": sum(1 for row in rows if row["forced_template_is_solved"]),
        "gate_solved": sum(1 for row in rows if row["split_gate_is_solved"]),
        "fix_harm": _fix_harm(rows, "split_gate_is_solved"),
        "fix_tasks": [
            row["task_id"] for row in rows if not row["baseline_is_solved"] and row["split_gate_is_solved"]
        ],
        "harm_tasks": [
            row["task_id"] for row in rows if row["baseline_is_solved"] and not row["split_gate_is_solved"]
        ],
    }


def build_baseline_split_gate_summary(
    r092_summary_json: str = DEFAULT_R092_SUMMARY_JSON,
    baseline_results: str = DEFAULT_BASELINE_RESULTS,
    audit_jsonl: str = DEFAULT_AUDIT_JSONL,
) -> Dict[str, Any]:
    r092 = _load_json(r092_summary_json)
    baseline = _load_jsonl_by_task(baseline_results)
    audits = _load_audit_by_task(audit_jsonl)
    rows = []
    for row in r092["rows"]:
        base_record = baseline[row["task_id"]]
        features = build_baseline_split_features(base_record, row)
        decision = decide_baseline_split_gate(features)
        split_prediction = (
            row["forced_template_prediction"]
            if decision["action"] == "accept_template"
            else row["baseline_prediction"]
        )
        split_is_solved = (
            row["forced_template_is_solved"]
            if decision["action"] == "accept_template"
            else row["baseline_is_solved"]
        )
        audit = audits[row["task_id"]]
        rows.append(
            {
                **row,
                "split_gate_prediction": split_prediction,
                "split_gate_is_solved": bool(split_is_solved),
                "split_gate_action": decision["action"],
                "split_gate_reason": decision["reason"],
                "split_gate_features": features,
                "split_gate_field_violation_count": len(
                    FORBIDDEN_DECISION_FIELDS.intersection(features)
                ),
                "clean_label": audit.get("clean_label", "unknown"),
                "gold_binding_status": audit.get("gold_binding_status", "unknown"),
                "rationale_issue": audit.get("rationale_issue", "unknown"),
            }
        )

    accepted_switch_tasks = [
        row["task_id"]
        for row in rows
        if row["split_gate_action"] == "accept_template"
        and row["forced_template_prediction"] != row["baseline_prediction"]
    ]
    suppressed_switch_tasks = [
        row["task_id"]
        for row in rows
        if row["split_gate_action"] == "fallback_to_arg"
        and row["gate_action"] == "accept_template"
        and row["forced_template_prediction"] != row["baseline_prediction"]
    ]
    by_label: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        by_label.setdefault(row["clean_label"], []).append(row)

    return {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "num_tasks": len(rows),
        "baseline_solved": r092["baseline_solved"],
        "forced_template_solved": r092["forced_template_solved"],
        "r088_gate_solved": r092["gate_solved"],
        "split_gate_solved": sum(1 for row in rows if row["split_gate_is_solved"]),
        "split_gate_fix_harm": _fix_harm(rows, "split_gate_is_solved"),
        "accepted_switch_tasks": accepted_switch_tasks,
        "suppressed_switch_tasks": suppressed_switch_tasks,
        "split_gate_action_counts": dict(Counter(row["split_gate_action"] for row in rows)),
        "split_gate_reason_counts": dict(Counter(row["split_gate_reason"] for row in rows)),
        "by_clean_label": {
            label: _bucket_summary(label_rows) for label, label_rows in by_label.items()
        },
        "decision_field_violations": sum(row["split_gate_field_violation_count"] for row in rows),
        "total_forced_template_cost": r092["total_forced_template_cost"],
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    switch_rows = [
        row
        for row in summary["rows"]
        if row["forced_template_prediction"] != row["baseline_prediction"]
    ]
    table_rows = [
        "| `{task}` | `{label}` | `{base}` | `{forced}` | `{split}` | `{gold}` | `{action}` | `{reason}` | `{valid}`/`{maj}` |".format(
            task=row["task_id"],
            label=row["clean_label"],
            base=row["baseline_prediction"],
            forced=row["forced_template_prediction"],
            split=row["split_gate_prediction"],
            gold=row["true_answer"],
            action=row["split_gate_action"],
            reason=row["split_gate_reason"],
            valid=row["split_gate_features"]["baseline_direct_valid_vote_count"],
            maj=row["split_gate_features"]["baseline_direct_majority_count"],
        )
        for row in switch_rows
    ]
    return "\n".join(
        [
            "# R094 Baseline-Split Protected Forced-Template Gate Report",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Tasks: `{summary['num_tasks']}`",
            f"- ARG baseline solved: `{summary['baseline_solved']}/{summary['num_tasks']}`",
            f"- Forced-template solved: `{summary['forced_template_solved']}/{summary['num_tasks']}`",
            f"- R088-gated solved: `{summary['r088_gate_solved']}/{summary['num_tasks']}`",
            f"- Baseline-split gate solved: `{summary['split_gate_solved']}/{summary['num_tasks']}`",
            f"- Split gate fix/harm vs ARG: `{summary['split_gate_fix_harm']}`",
            f"- Accepted switch tasks: `{summary['accepted_switch_tasks']}`",
            f"- Suppressed switch tasks: `{summary['suppressed_switch_tasks']}`",
            f"- Clean/noisy buckets: `{summary['by_clean_label']}`",
            f"- Decision-field violations: `{summary['decision_field_violations']}`",
            f"- Forced-template cost inherited from R092: `${summary['total_forced_template_cost']:.6f}`",
            "",
            "## Switch Rows",
            "",
            "| Task | Audit label | ARG | Forced template | Split gate | Gold | Action | Reason | Baseline valid/majority votes |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "The baseline-split gate is label-free and suppresses the two clean harms from R092 while keeping "
            "`task_108`. However, the retained improvement is noisy-only: clean accuracy ties ARG. This is a "
            "candidate safety gate or ablation, not a final SCI-Q2 main result.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay a baseline-split protected gate over R092 forced-template traces.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_baseline_split_gate_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R094 baseline-split gate: "
        f"baseline={summary['baseline_solved']}/{summary['num_tasks']} "
        f"r088={summary['r088_gate_solved']}/{summary['num_tasks']} "
        f"split={summary['split_gate_solved']}/{summary['num_tasks']}"
    )


if __name__ == "__main__":
    main()
