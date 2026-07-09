from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Set

from experiment.aqua.r267_cost_safety_combined_selector import (
    DEFAULT_REPORT_MD as R267_REPORT_MD,
    build_r267_summary,
    write_json,
    write_text,
)


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_ROWS_JSONL = os.path.join(SCRIPT_DIR, "aqua_tail34_r268_low_cost_student_policy_rows.jsonl")
DEFAULT_SUMMARY_JSON = os.path.join(SCRIPT_DIR, "res_logs", "aqua_tail34_r268_low_cost_student_policy_summary.json")
DEFAULT_REPORT_MD = os.path.join(SCRIPT_DIR, "run_logs", "aqua_tail34_r268_low_cost_student_policy_report.md")

FORBIDDEN_FEATURE_FIELDS: Set[str] = {
    "true_answer",
    "is_solved",
    "baseline_is_solved",
    "objective_is_solved",
    "clean_label",
    "audit_label",
    "gold_binding_status",
    "rationale_issue",
    "task_id",
}

PROMPTNODE_ROLES = ["PN_Memory", "PN_Verifier", "PN_Router"]
EDGE_ACTIONS = ["read", "write", "forward"]
LIFECYCLE_ACTIONS = ["update", "compress", "prune", "merge", "upgrade"]


def _safe_features(row: Dict[str, Any]) -> Dict[str, Any]:
    trigger = row.get("trigger_features", {})
    decision = row.get("decision_features", {})
    features = {
        "direct_valid_vote_count": trigger.get("direct_valid_vote_count"),
        "direct_max_count": trigger.get("direct_max_count"),
        "direct_distinct_count": trigger.get("direct_distinct_count"),
        "missing_direct_vote_count": trigger.get("missing_direct_vote_count"),
        "final_direct_support_count": trigger.get("final_direct_support_count"),
        "direct_conflict": trigger.get("direct_conflict"),
        "weak_final_support": trigger.get("weak_final_support"),
        "missing_direct_vote": trigger.get("missing_direct_vote"),
        "low_direct_coverage": trigger.get("low_direct_coverage"),
        "r063_trigger": trigger.get("r063_trigger"),
        "missing_direct_vote_trigger": trigger.get("missing_direct_vote_trigger"),
        "objective_prediction_differs_from_baseline": decision.get("objective_prediction_differs_from_baseline"),
        "objective_selected_source": decision.get("objective_selected_source"),
        "objective_top_score": decision.get("objective_top_score"),
        "baseline_direct_majority_count": decision.get("baseline_direct_majority_count"),
        "baseline_direct_valid_vote_count": decision.get("baseline_direct_valid_vote_count"),
        "baseline_direct_votes_split": decision.get("baseline_direct_votes_split"),
    }
    return {key: value for key, value in features.items() if key not in FORBIDDEN_FEATURE_FIELDS}


def _feature_violations(features: Dict[str, Any]) -> List[str]:
    return sorted(FORBIDDEN_FEATURE_FIELDS.intersection(features))


def build_policy_rows(r267_summary: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    r267_summary = r267_summary or build_r267_summary()
    rows: List[Dict[str, Any]] = []
    for record in r267_summary["records"]:
        features = _safe_features(record)
        accept = record["selected_source"] == "safety_accept_objective"
        run_promptnodes = bool(record.get("multiview_would_run"))
        rows.append(
            {
                "task_id": record["task_id"],
                "policy_input": features,
                "policy_target": {
                    "run_promptnodes": run_promptnodes,
                    "accept_objective": accept,
                    "fallback_to_arg": not accept,
                    "promptnode_roles": PROMPTNODE_ROLES if run_promptnodes else [],
                    "edge_actions": EDGE_ACTIONS if run_promptnodes else [],
                    "lifecycle_actions": LIFECYCLE_ACTIONS if run_promptnodes else ["prune"],
                    "decision_reason": record.get("r095_decision_reason"),
                },
                "metadata_not_model_visible": {
                    "teacher_run": "R267",
                    "prediction": record["predicted_answer"],
                    "official_correct": bool(record["is_solved"]),
                },
                "feature_violations": _feature_violations(features),
            }
        )
    return rows


def build_r268_policy_export() -> Dict[str, Any]:
    r267_summary = build_r267_summary()
    rows = build_policy_rows(r267_summary)
    decision_field_violations = sum(len(row["feature_violations"]) for row in rows)
    accept_tasks = [row["task_id"] for row in rows if row["policy_target"]["accept_objective"]]
    run_tasks = [row["task_id"] for row in rows if row["policy_target"]["run_promptnodes"]]
    return {
        "run_id": "R268",
        "title": "Low-cost student policy export from R267",
        "claim_boundary": "policy_target_export_only_no_training_no_api_no_accuracy_claim",
        "source_run": "R267",
        "source_report": R267_REPORT_MD,
        "rows": len(rows),
        "policy_rows": rows,
        "run_promptnode_tasks": run_tasks,
        "accept_objective_tasks": accept_tasks,
        "fallback_tasks": [row["task_id"] for row in rows if not row["policy_target"]["accept_objective"]],
        "decision_field_violations": decision_field_violations,
        "forbidden_feature_fields": sorted(FORBIDDEN_FEATURE_FIELDS),
        "promptnode_roles": PROMPTNODE_ROLES,
        "edge_actions": EDGE_ACTIONS,
        "lifecycle_actions": LIFECYCLE_ACTIONS,
        "requires_training_before_accuracy_claim": True,
        "requires_fresh_eval_before_submission_claim": True,
    }


def write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R268 Low-Cost Student Policy Export",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Rows: `{summary['rows']}`",
            f"- Run PromptNode tasks: `{len(summary['run_promptnode_tasks'])}`",
            f"- Accept-objective tasks: `{summary['accept_objective_tasks']}`",
            f"- Decision-field violations: `{summary['decision_field_violations']}`",
            f"- PromptNode roles: `{summary['promptnode_roles']}`",
            f"- Edge actions: `{summary['edge_actions']}`",
            f"- Lifecycle actions: `{summary['lifecycle_actions']}`",
            "",
            "This export is a distillation target for a future student selector or graph policy. It is not a trained model and does not reduce runtime cost until it is trained and evaluated prospectively.",
            "",
        ]
    )


def run(
    rows_jsonl: str = DEFAULT_ROWS_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_r268_policy_export()
    write_jsonl(rows_jsonl, summary["policy_rows"])
    write_json(summary_json, {k: v for k, v in summary.items() if k != "policy_rows"})
    write_text(report_md, render_report(summary))
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
