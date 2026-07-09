import argparse
import json
import os
import sys
from typing import Any, Dict, List


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_gate_r058_stress import _repo_path  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r109_objective_safety_rule_distillation"
CLAIM_BOUNDARY = "rule distillation over R096 targets; no new accuracy or cheap-proxy claim"

DEFAULT_R096_TARGET_JSONL = "experiment/aqua/aqua_tail34_r096_objective_safety_policy_targets.jsonl"
DEFAULT_R108_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r108_rank5_guard_deployability_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r109_objective_safety_rule_distillation_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r109_objective_safety_rule_distillation_report.md"

FORBIDDEN_RULE_INPUT_FIELDS = {
    "task_id",
    "true_answer",
    "is_solved",
    "baseline_is_solved",
    "objective_selector_is_solved",
    "safety_composed_is_solved",
    "clean_label",
    "audit_label",
    "gold_binding_status",
    "rationale_issue",
    "target_action",
    "target_reason",
    "analysis",
}


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _distilled_action(policy_input: Dict[str, Any]) -> str:
    if not policy_input["objective_prediction_differs_from_baseline"]:
        return "fallback_to_arg"
    if int(policy_input["objective_top_score"]) >= 3:
        return "switch_to_objective"
    if bool(policy_input["baseline_direct_votes_split"]):
        return "switch_to_objective"
    return "fallback_to_arg"


def _input_violation_count(rows: List[Dict[str, Any]]) -> int:
    count = 0
    for row in rows:
        count += sum(1 for key in row["rule_input"] if key in FORBIDDEN_RULE_INPUT_FIELDS)
    return count


def build_distillation_rows() -> List[Dict[str, Any]]:
    rows = []
    for target in _load_jsonl(DEFAULT_R096_TARGET_JSONL):
        rule_input = dict(target["policy_input"])
        predicted_action = _distilled_action(rule_input)
        rows.append(
            {
                "task_id": target["task_id"],
                "rule_input": rule_input,
                "target_action": target["target_action"],
                "distilled_action": predicted_action,
                "matches_target": predicted_action == target["target_action"],
                "target_reason": target["target_reason"],
                "analysis": target["analysis"],
            }
        )
    return rows


def build_distillation_summary() -> Dict[str, Any]:
    rows = build_distillation_rows()
    r108 = _load_json(DEFAULT_R108_SUMMARY_JSON)
    switch_rows = [row for row in rows if row["distilled_action"] == "switch_to_objective"]
    objective_diff_suppressed = [
        row["task_id"]
        for row in rows
        if row["rule_input"]["objective_prediction_differs_from_baseline"]
        and row["distilled_action"] == "fallback_to_arg"
    ]
    matches = sum(1 for row in rows if row["matches_target"])
    return {
        "rule": RULE_NAME,
        "num_rows": len(rows),
        "target_agreement": f"{matches}/{len(rows)}",
        "switch_tasks": [row["task_id"] for row in switch_rows],
        "objective_diff_suppressed_tasks": objective_diff_suppressed,
        "rule_input_field_violations": _input_violation_count(rows),
        "distilled_rule": (
            "switch_to_objective iff objective_prediction_differs_from_baseline and "
            "(objective_top_score>=3 or baseline_direct_votes_split)"
        ),
        "requires_multiview_objective_features": True,
        "cheap_single_template_proxy_ready": bool(r108["single_template_guard_sufficient"]),
        "rows": rows,
        "source_runs": ["R096", "R108"],
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    switch_rows = [row for row in summary["rows"] if row["distilled_action"] == "switch_to_objective"]
    suppressed_rows = [
        row
        for row in summary["rows"]
        if row["rule_input"]["objective_prediction_differs_from_baseline"]
        and row["distilled_action"] == "fallback_to_arg"
    ]
    switch_table = [
        "| `{task}` | `{reason}` | `{score}` | `{split}` | `{label}` |".format(
            task=row["task_id"],
            reason=row["target_reason"],
            score=row["rule_input"]["objective_top_score"],
            split=row["rule_input"]["baseline_direct_votes_split"],
            label=row["analysis"]["clean_label"],
        )
        for row in switch_rows
    ]
    suppressed_table = [
        "| `{task}` | `{reason}` | `{score}` | `{split}` | `{label}` |".format(
            task=row["task_id"],
            reason=row["target_reason"],
            score=row["rule_input"]["objective_top_score"],
            split=row["rule_input"]["baseline_direct_votes_split"],
            label=row["analysis"]["clean_label"],
        )
        for row in suppressed_rows
    ]
    return "\n".join(
        [
            "# R109 Objective-Safety Rule Distillation",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Rows: `{summary['num_rows']}`",
            f"- Target agreement: `{summary['target_agreement']}`",
            f"- Switch tasks: `{summary['switch_tasks']}`",
            f"- Objective-diff suppressed tasks: `{summary['objective_diff_suppressed_tasks']}`",
            f"- Rule input field violations: `{summary['rule_input_field_violations']}`",
            f"- Requires multi-view objective features: `{summary['requires_multiview_objective_features']}`",
            f"- Cheap single-template proxy ready: `{summary['cheap_single_template_proxy_ready']}`",
            "",
            "## Distilled Rule",
            "",
            f"`{summary['distilled_rule']}`",
            "",
            "## Switch Tasks",
            "",
            "| Task | Reason | Objective score | Baseline split | Audit label |",
            "| --- | --- | --- | --- | --- |",
            *switch_table,
            "",
            "## Objective-Diff Suppressed Tasks",
            "",
            "| Task | Reason | Objective score | Baseline split | Audit label |",
            "| --- | --- | --- | --- | --- |",
            *suppressed_table,
            "",
            "## Interpretation",
            "",
            "The R096 target policy is exactly captured by a small objective-safety rule, but R108 shows "
            "the required objective features cannot be replaced by the current single rank5-template "
            "trace features. This is a rule-specification artifact for a future proxy or selector, "
            "not a new accuracy result.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Distill the R096 objective-safety policy into a rule spec.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_distillation_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R109 objective-safety rule distillation: "
        f"agreement={summary['target_agreement']} "
        f"switch_tasks={summary['switch_tasks']}"
    )


if __name__ == "__main__":
    main()
