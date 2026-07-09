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

from experiment.aqua.forced_template_gate_r058_stress import _repo_path  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r096_objective_safety_policy_targets"
CLAIM_BOUNDARY = "policy-target export from R095 replay; no new accuracy result"

FORBIDDEN_POLICY_INPUT_FIELDS = {
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
}

DEFAULT_R095_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r095_objective_safety_composed_summary.json"
DEFAULT_TARGET_JSONL = "experiment/aqua/aqua_tail34_r096_objective_safety_policy_targets.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r096_objective_safety_policy_targets_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r096_objective_safety_policy_targets_report.md"


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    abs_path = _repo_path(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _policy_input_from_r095_row(row: Dict[str, Any]) -> Dict[str, Any]:
    features = row["decision_features"]
    return {
        "baseline_prediction": row["baseline_prediction"],
        "objective_prediction": row["objective_prediction"],
        "objective_prediction_differs_from_baseline": features[
            "objective_prediction_differs_from_baseline"
        ],
        "objective_selected_source": features["objective_selected_source"],
        "objective_top_score": features["objective_top_score"],
        "baseline_direct_majority": features["baseline_direct_majority"],
        "baseline_direct_majority_count": features["baseline_direct_majority_count"],
        "baseline_direct_valid_vote_count": features["baseline_direct_valid_vote_count"],
        "baseline_direct_votes_split": features["baseline_direct_votes_split"],
    }


def _target_action(row: Dict[str, Any]) -> str:
    return "switch_to_objective" if row["decision_action"] == "accept_objective" else "fallback_to_arg"


def build_policy_target_rows(r095_summary_json: str = DEFAULT_R095_SUMMARY_JSON) -> List[Dict[str, Any]]:
    r095 = _load_json(r095_summary_json)
    rows = []
    for row in r095["rows"]:
        target_action = _target_action(row)
        policy_input = _policy_input_from_r095_row(row)
        rows.append(
            {
                "task_id": row["task_id"],
                "policy_input": policy_input,
                "target_action": target_action,
                "target_reason": row["decision_reason"],
                "target_prediction_source": (
                    "objective" if target_action == "switch_to_objective" else "arg_baseline"
                ),
                "requires_explicit_promptnode_graph_metadata": target_action == "switch_to_objective",
                "analysis": {
                    "clean_label": row["clean_label"],
                    "gold_binding_status": row["gold_binding_status"],
                    "rationale_issue": row["rationale_issue"],
                },
                "source_run": "R095",
            }
        )
    return rows


def build_policy_target_summary() -> Dict[str, Any]:
    rows = build_policy_target_rows()
    switch_rows = [row for row in rows if row["target_action"] == "switch_to_objective"]
    clean_switch_tasks = [
        row["task_id"] for row in switch_rows if row["analysis"]["clean_label"] == "clean"
    ]
    noisy_switch_tasks = [
        row["task_id"] for row in switch_rows if row["analysis"]["clean_label"] != "clean"
    ]
    return {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "num_rows": len(rows),
        "target_action_counts": dict(Counter(row["target_action"] for row in rows)),
        "switch_target_tasks": [row["task_id"] for row in switch_rows],
        "clean_switch_target_tasks": clean_switch_tasks,
        "noisy_switch_target_tasks": noisy_switch_tasks,
        "policy_input_field_violations": sum(
            1
            for row in rows
            if FORBIDDEN_POLICY_INPUT_FIELDS.intersection(row["policy_input"])
        ),
        "forbidden_policy_input_fields": sorted(FORBIDDEN_POLICY_INPUT_FIELDS),
        "target_jsonl": DEFAULT_TARGET_JSONL,
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    switch_rows = [
        row for row in summary["rows"] if row["target_action"] == "switch_to_objective"
    ]
    table_rows = [
        "| `{task}` | `{label}` | `{reason}` | `{score}` | `{split}` |".format(
            task=row["task_id"],
            label=row["analysis"]["clean_label"],
            reason=row["target_reason"],
            score=row["policy_input"]["objective_top_score"],
            split=row["policy_input"]["baseline_direct_votes_split"],
        )
        for row in switch_rows
    ]
    return "\n".join(
        [
            "# R096 Objective-Safety Policy Target Export",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Rows: `{summary['num_rows']}`",
            f"- Target action counts: `{summary['target_action_counts']}`",
            f"- Switch target tasks: `{summary['switch_target_tasks']}`",
            f"- Clean switch targets: `{summary['clean_switch_target_tasks']}`",
            f"- Noisy switch targets: `{summary['noisy_switch_target_tasks']}`",
            f"- Policy input field violations: `{summary['policy_input_field_violations']}`",
            f"- Target JSONL: `{summary['target_jsonl']}`",
            "",
            "## Switch Targets",
            "",
            "| Task | Audit label | Target reason | Objective top score | Baseline split |",
            "| --- | --- | --- | ---: | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "R096 converts the R095 replay decision into leakage-checked policy targets. The exported "
            "policy inputs exclude task ids, gold labels, correctness, and audit labels. This is a bridge "
            "toward an explicit PromptNode graph-policy/template selector, not a new accuracy result.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export R095 objective-safety selector as policy targets.")
    parser.add_argument("--target-jsonl", default=DEFAULT_TARGET_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    rows = build_policy_target_rows()
    _write_jsonl(args.target_jsonl, rows)
    summary = build_policy_target_summary()
    summary["target_jsonl"] = args.target_jsonl
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R096 policy targets: "
        f"rows={summary['num_rows']} actions={summary['target_action_counts']}"
    )


if __name__ == "__main__":
    main()
