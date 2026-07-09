import argparse
import datetime
import json
import os
import re
import sys
from collections import Counter
from typing import Any, Dict, List


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_clean_positive_report import (  # noqa: E402
    build_clean_positive_summary,
)
from experiment.aqua.forced_template_smoke_report import (  # noqa: E402
    _load_first_jsonl,
    write_json,
    write_text,
)


RULE_NAME = "r086_forced_template_smoke_gate"
CLAIM_BOUNDARY = "smoke-gate replay only, not tail34 accuracy"
VALID_OPTIONS = set("ABCDE")
FORBIDDEN_DECISION_FIELDS = {
    "task_id",
    "true_answer",
    "is_solved",
    "run_group",
    "clean_label",
    "audit_label",
    "baseline_is_solved",
}

DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r086_forced_template_smoke_gate_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r086_forced_template_smoke_gate_report.md"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def normalize_option(value: Any) -> str:
    text = str(value or "").strip().upper()
    return text if text in VALID_OPTIONS else ""


def extract_option_text(question: str, option: str) -> str:
    option = normalize_option(option)
    if not option:
        return ""
    match = re.search(rf"{option}\)(.*?)(?=\s+[A-E]\)|$)", question or "", flags=re.I | re.S)
    return re.sub(r"\s+", " ", match.group(1)).strip() if match else ""


def is_none_of_these_text(option_text: str) -> bool:
    lowered = option_text.lower()
    return any(
        marker in lowered
        for marker in [
            "none of these",
            "none of the above",
            "not among",
            "not listed",
            "not available",
        ]
    )


def load_default_smoke_rows() -> List[Dict[str, Any]]:
    summary = build_clean_positive_summary()
    rows = []
    for row in summary["rows"]:
        result = _load_first_jsonl(_repo_path(row["result_path"]))
        enriched = dict(row)
        enriched["question"] = result.get("question") or ""
        enriched["raw_response"] = result.get("raw_response") or ""
        rows.append(enriched)
    return rows


def build_decision_features(row: Dict[str, Any]) -> Dict[str, Any]:
    predicted_answer = normalize_option(row.get("predicted_answer"))
    option_text = extract_option_text(row.get("question") or "", predicted_answer)
    return {
        "router_supported_option": normalize_option(row.get("router_supported_option")),
        "router_binding_status": str(row.get("router_binding_status") or "").upper(),
        "predicted_answer": predicted_answer,
        "predicted_option_text": option_text,
        "predicted_option_is_none_of_these": is_none_of_these_text(option_text),
        "selected_rank": int(row.get("selected_rank") or 0),
        "has_promptnode_graph": bool(row.get("has_promptnode_graph")),
        "num_nodes": int(row.get("num_nodes") or 0),
        "num_edges": int(row.get("num_edges") or 0),
    }


def decide_forced_template_gate(features: Dict[str, Any]) -> Dict[str, str]:
    if not features["has_promptnode_graph"]:
        return {"action": "fallback_to_arg", "reason": "missing_promptnode_graph"}
    if features["selected_rank"] != 1:
        return {"action": "fallback_to_arg", "reason": "not_rank1_template"}

    router_option = features["router_supported_option"]
    router_status = features["router_binding_status"]
    predicted = features["predicted_answer"]
    predicted_is_none = features["predicted_option_is_none_of_these"]

    if router_status == "EXACT_MATCH" and router_option in VALID_OPTIONS:
        if predicted == router_option:
            return {"action": "accept_template", "reason": "router_exact_final_agreement"}
        return {"action": "fallback_to_arg", "reason": "router_final_conflict"}

    if router_status == "NO_EXACT_OPTION" and predicted in VALID_OPTIONS:
        if predicted_is_none:
            return {"action": "fallback_to_arg", "reason": "weak_none_of_these_boundary"}
        return {"action": "accept_template", "reason": "weak_non_none_terminal_option"}

    return {"action": "fallback_to_arg", "reason": "unsupported_router_status"}


def build_gate_rows(rows: List[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
    source_rows = rows if rows is not None else load_default_smoke_rows()
    gate_rows = []
    for row in source_rows:
        features = build_decision_features(row)
        decision = decide_forced_template_gate(features)
        gate_rows.append(
            {
                "task_id": row.get("task_id"),
                "run_group": row.get("run_group"),
                "run_name": row.get("run_name"),
                "predicted_answer": row.get("predicted_answer"),
                "true_answer": row.get("true_answer"),
                "is_solved": row.get("is_solved"),
                "router_supported_option": row.get("router_supported_option"),
                "router_binding_status": row.get("router_binding_status"),
                "selected_rank": row.get("selected_rank"),
                "cost": row.get("cost"),
                "decision_features": features,
                "gate_action": decision["action"],
                "gate_reason": decision["reason"],
                "decision_field_violation_count": len(
                    FORBIDDEN_DECISION_FIELDS.intersection(features)
                ),
            }
        )
    return gate_rows


def build_gate_summary(rows: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    gate_rows = build_gate_rows(rows)
    clean_rows = [row for row in gate_rows if row["run_group"] == "clean_positive"]
    boundary_rows = [row for row in gate_rows if row["run_group"] == "boundary"]
    accepted_rows = [row for row in gate_rows if row["gate_action"] == "accept_template"]
    suppressed_rows = [row for row in gate_rows if row["gate_action"] == "fallback_to_arg"]

    return {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "clean_positive_rows": len(clean_rows),
        "clean_positive_accepted": sum(
            1 for row in clean_rows if row["gate_action"] == "accept_template"
        ),
        "clean_positive_suppressed": sum(
            1 for row in clean_rows if row["gate_action"] == "fallback_to_arg"
        ),
        "boundary_rows": len(boundary_rows),
        "boundary_accepted": sum(
            1 for row in boundary_rows if row["gate_action"] == "accept_template"
        ),
        "boundary_suppressed": sum(
            1 for row in boundary_rows if row["gate_action"] == "fallback_to_arg"
        ),
        "accepted_rows": len(accepted_rows),
        "suppressed_rows": len(suppressed_rows),
        "gate_action_counts": dict(Counter(row["gate_action"] for row in gate_rows)),
        "gate_reason_counts": dict(Counter(row["gate_reason"] for row in gate_rows)),
        "decision_field_violations": sum(
            row["decision_field_violation_count"] for row in gate_rows
        ),
        "accepted_smoke_cost": sum(float(row.get("cost") or 0.0) for row in accepted_rows),
        "suppressed_smoke_cost": sum(float(row.get("cost") or 0.0) for row in suppressed_rows),
        "total_smoke_cost": sum(float(row.get("cost") or 0.0) for row in gate_rows),
        "rows": gate_rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{group}` | `{task}` | `{pred}` | `{gold}` | `{router}` | `{action}` | `{reason}` | `${cost:.6f}` |".format(
            group=row["run_group"],
            task=row["task_id"],
            pred=row["predicted_answer"],
            gold=row["true_answer"],
            router=f"{row['router_supported_option']}/{row['router_binding_status']}",
            action=row["gate_action"],
            reason=row["gate_reason"],
            cost=float(row.get("cost") or 0.0),
        )
        for row in summary["rows"]
    ]
    return "\n".join(
        [
            "# R086 Forced-Template Smoke Gate Report",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Clean-positive accepted: `{summary['clean_positive_accepted']}/{summary['clean_positive_rows']}`",
            f"- Boundary suppressed: `{summary['boundary_suppressed']}/{summary['boundary_rows']}`",
            f"- Gate action counts: `{summary['gate_action_counts']}`",
            f"- Gate reason counts: `{summary['gate_reason_counts']}`",
            f"- Decision-field violations: `{summary['decision_field_violations']}`",
            f"- Accepted smoke cost: `${summary['accepted_smoke_cost']:.6f}`",
            f"- Total smoke cost: `${summary['total_smoke_cost']:.6f}`",
            "",
            "| Group | Task | Prediction | Gold | Router contract | Gate action | Gate reason | Smoke cost |",
            "| --- | --- | --- | --- | --- | --- | --- | ---: |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "The gate is a smoke-regression rule, not a validated accuracy method. It accepts exact router/final agreement, "
            "permits weak non-`None of these` terminal options for the clean-positive smoke set, and suppresses weak "
            "`None of these` boundary decisions such as `task_114`. The next step is to test whether this rule "
            "generalizes beyond the four smoke records before spending on a broader forced-template run.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay a conservative R086 forced-template smoke gate.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_gate_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built forced-template smoke gate report: "
        f"accepted={summary['accepted_rows']} suppressed={summary['suppressed_rows']} "
        f"violations={summary['decision_field_violations']}"
    )


if __name__ == "__main__":
    main()
