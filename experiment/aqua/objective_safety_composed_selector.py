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


RULE_NAME = "r095_objective_safety_composed_selector"
CLAIM_BOUNDARY = "label-free replay over R065 multi-view traces; not an explicit forced-template or transfer result"

DEFAULT_OBJECTIVE_RESULTS = "experiment/aqua/aqua_tail34_objective_guided_selector_results.jsonl"
DEFAULT_AUDIT_JSONL = "experiment/aqua/aqua_tail34_option_binding_audit.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r095_objective_safety_composed_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r095_objective_safety_composed_report.md"


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    records = []
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def _load_audit_by_task(path: str) -> Dict[str, Dict[str, Any]]:
    return {record["task_id"]: record for record in _load_jsonl(path)}


def build_objective_safety_features(
    baseline_record: Dict[str, Any],
    objective_record: Dict[str, Any],
) -> Dict[str, Any]:
    baseline_features = extract_contract_consensus_features(baseline_record)
    direct_valid = int(baseline_features.get("direct_valid_vote_count") or 0)
    direct_majority = int(baseline_features.get("direct_majority_count") or 0)
    return {
        "objective_prediction_differs_from_baseline": (
            objective_record.get("predicted_answer") != baseline_record.get("predicted_answer")
        ),
        "objective_selected_source": objective_record.get("selected_source"),
        "objective_top_score": int(objective_record.get("top_score") or 0),
        "baseline_direct_majority": baseline_features.get("direct_majority"),
        "baseline_direct_majority_count": direct_majority,
        "baseline_direct_valid_vote_count": direct_valid,
        "baseline_direct_votes_split": direct_valid > direct_majority,
    }


def decide_objective_safety_gate(features: Dict[str, Any]) -> Dict[str, str]:
    if not features["objective_prediction_differs_from_baseline"]:
        return {"action": "fallback_to_arg", "reason": "same_prediction_as_arg"}
    if features["objective_selected_source"] != "objective_top":
        return {"action": "fallback_to_arg", "reason": "objective_selector_kept_baseline"}
    if int(features["objective_top_score"]) >= 3:
        return {"action": "accept_objective", "reason": "objective_top_score_ge3"}
    if features["baseline_direct_votes_split"]:
        return {"action": "accept_objective", "reason": "baseline_direct_split_allows_switch"}
    return {"action": "fallback_to_arg", "reason": "insufficient_safety_evidence"}


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
        "objective_selector_solved": sum(1 for row in rows if row["objective_selector_is_solved"]),
        "gate_solved": sum(1 for row in rows if row["safety_composed_is_solved"]),
        "fix_harm": _fix_harm(rows, "safety_composed_is_solved"),
        "fix_tasks": [
            row["task_id"] for row in rows if not row["baseline_is_solved"] and row["safety_composed_is_solved"]
        ],
        "harm_tasks": [
            row["task_id"] for row in rows if row["baseline_is_solved"] and not row["safety_composed_is_solved"]
        ],
    }


def build_objective_safety_summary(
    objective_results: str = DEFAULT_OBJECTIVE_RESULTS,
    baseline_results: str = DEFAULT_BASELINE_RESULTS,
    audit_jsonl: str = DEFAULT_AUDIT_JSONL,
) -> Dict[str, Any]:
    objective_records = _load_jsonl(objective_results)
    baseline = _load_jsonl_by_task(baseline_results)
    audits = _load_audit_by_task(audit_jsonl)
    rows = []
    for record in objective_records:
        task_id = record["task_id"]
        base_record = baseline[task_id]
        features = build_objective_safety_features(base_record, record)
        decision = decide_objective_safety_gate(features)
        prediction = (
            record.get("predicted_answer")
            if decision["action"] == "accept_objective"
            else base_record.get("predicted_answer")
        )
        safety_is_solved = prediction == record.get("true_answer", base_record.get("true_answer"))
        audit = audits[task_id]
        rows.append(
            {
                "task_id": task_id,
                "baseline_prediction": base_record.get("predicted_answer"),
                "objective_prediction": record.get("predicted_answer"),
                "safety_composed_prediction": prediction,
                "true_answer": record.get("true_answer", base_record.get("true_answer")),
                "baseline_is_solved": bool(base_record.get("is_solved")),
                "objective_selector_is_solved": bool(record.get("is_solved")),
                "safety_composed_is_solved": bool(safety_is_solved),
                "decision_action": decision["action"],
                "decision_reason": decision["reason"],
                "decision_features": features,
                "decision_field_violation_count": len(
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
        if row["decision_action"] == "accept_objective"
        and row["objective_prediction"] != row["baseline_prediction"]
    ]
    suppressed_switch_tasks = [
        row["task_id"]
        for row in rows
        if row["decision_action"] == "fallback_to_arg"
        and row["objective_prediction"] != row["baseline_prediction"]
    ]
    by_label: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        by_label.setdefault(row["clean_label"], []).append(row)

    return {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "num_tasks": len(rows),
        "baseline_solved": sum(1 for row in rows if row["baseline_is_solved"]),
        "objective_selector_solved": sum(1 for row in rows if row["objective_selector_is_solved"]),
        "safety_composed_solved": sum(1 for row in rows if row["safety_composed_is_solved"]),
        "safety_composed_fix_harm": _fix_harm(rows, "safety_composed_is_solved"),
        "accepted_switch_tasks": accepted_switch_tasks,
        "suppressed_switch_tasks": suppressed_switch_tasks,
        "decision_action_counts": dict(Counter(row["decision_action"] for row in rows)),
        "decision_reason_counts": dict(Counter(row["decision_reason"] for row in rows)),
        "by_clean_label": {
            label: _bucket_summary(label_rows) for label, label_rows in by_label.items()
        },
        "decision_field_violations": sum(row["decision_field_violation_count"] for row in rows),
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    switch_rows = [
        row
        for row in summary["rows"]
        if row["objective_prediction"] != row["baseline_prediction"]
    ]
    table_rows = [
        "| `{task}` | `{label}` | `{base}` | `{obj}` | `{safe}` | `{gold}` | `{action}` | `{reason}` | `{score}` | `{valid}`/`{maj}` |".format(
            task=row["task_id"],
            label=row["clean_label"],
            base=row["baseline_prediction"],
            obj=row["objective_prediction"],
            safe=row["safety_composed_prediction"],
            gold=row["true_answer"],
            action=row["decision_action"],
            reason=row["decision_reason"],
            score=row["decision_features"]["objective_top_score"],
            valid=row["decision_features"]["baseline_direct_valid_vote_count"],
            maj=row["decision_features"]["baseline_direct_majority_count"],
        )
        for row in switch_rows
    ]
    return "\n".join(
        [
            "# R095 Objective-Safety Composed Selector Report",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Tasks: `{summary['num_tasks']}`",
            f"- ARG baseline solved: `{summary['baseline_solved']}/{summary['num_tasks']}`",
            f"- R065 objective selector solved: `{summary['objective_selector_solved']}/{summary['num_tasks']}`",
            f"- Safety-composed solved: `{summary['safety_composed_solved']}/{summary['num_tasks']}`",
            f"- Safety-composed fix/harm: `{summary['safety_composed_fix_harm']}`",
            f"- Accepted switches: `{summary['accepted_switch_tasks']}`",
            f"- Suppressed switches: `{summary['suppressed_switch_tasks']}`",
            f"- Clean/noisy buckets: `{summary['by_clean_label']}`",
            f"- Decision-field violations: `{summary['decision_field_violations']}`",
            "",
            "## Switch Rows",
            "",
            "| Task | Audit label | ARG | Objective | Safety-composed | Gold | Action | Reason | Objective top score | Baseline valid/majority votes |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "R095 composes R094's clean-harm safety idea with R065's multi-view objective signal. It keeps the "
            "clean fix `task_250` through the high objective score and keeps the noisy `task_108` fix through "
            "baseline direct-vote split, while suppressing weaker noisy switches. This is the strongest current "
            "paper direction, but it remains a replay over R065 multi-view traces and lacks explicit forced-template "
            "PromptNode graph metadata.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay the R095 safety-composed objective selector.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_objective_safety_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R095 objective-safety selector: "
        f"baseline={summary['baseline_solved']}/{summary['num_tasks']} "
        f"objective={summary['objective_selector_solved']}/{summary['num_tasks']} "
        f"safety={summary['safety_composed_solved']}/{summary['num_tasks']}"
    )


if __name__ == "__main__":
    main()
