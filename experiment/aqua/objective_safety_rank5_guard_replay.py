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


RULE_NAME = "r107_objective_safety_rank5_guard_replay"
CLAIM_BOUNDARY = "four-task replay over R106 rank5 outputs and R095 objective-safety features"

DEFAULT_R095_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r095_objective_safety_composed_summary.json"
DEFAULT_R106_RESULTS_JSONL = "experiment/aqua/aqua_tail34_r106_rank5_regression_smoke_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r107_objective_safety_rank5_guard_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r107_objective_safety_rank5_guard_report.md"

FORBIDDEN_SELECTOR_FIELDS = {
    "task_id",
    "true_answer",
    "is_solved",
    "baseline_is_solved",
    "rank5_is_solved",
    "guarded_is_solved",
    "clean_label",
    "gold_binding_status",
    "audit_label",
    "rationale_issue",
}


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _r095_index() -> Dict[str, Dict[str, Any]]:
    return {row["task_id"]: row for row in _load_json(DEFAULT_R095_SUMMARY_JSON)["rows"]}


def _selector_inputs(r095_row: Dict[str, Any]) -> Dict[str, Any]:
    features = r095_row["decision_features"]
    return {
        "baseline_direct_votes_split": bool(features["baseline_direct_votes_split"]),
        "baseline_direct_majority_count": int(features["baseline_direct_majority_count"]),
        "baseline_direct_valid_vote_count": int(features["baseline_direct_valid_vote_count"]),
        "objective_prediction_differs_from_baseline": bool(
            features["objective_prediction_differs_from_baseline"]
        ),
        "objective_top_score": int(features["objective_top_score"]),
    }


def _accept_rank5(inputs: Dict[str, Any]) -> bool:
    if not inputs["objective_prediction_differs_from_baseline"]:
        return False
    return bool(inputs["baseline_direct_votes_split"]) or int(inputs["objective_top_score"]) >= 3


def _input_violation_count(rows: List[Dict[str, Any]]) -> int:
    count = 0
    for row in rows:
        count += sum(1 for key in row["selector_inputs"] if key in FORBIDDEN_SELECTOR_FIELDS)
    return count


def build_guard_rows() -> List[Dict[str, Any]]:
    r095 = _r095_index()
    rows = []
    for rank5_result in _load_jsonl(DEFAULT_R106_RESULTS_JSONL):
        task_id = rank5_result["task_id"]
        base = r095[task_id]
        inputs = _selector_inputs(base)
        action = "accept_rank5" if _accept_rank5(inputs) else "fallback_to_arg"
        guarded_prediction = (
            rank5_result["predicted_answer"] if action == "accept_rank5" else base["baseline_prediction"]
        )
        baseline_is_solved = bool(base["baseline_is_solved"])
        rank5_is_solved = bool(rank5_result["is_solved"])
        guarded_is_solved = guarded_prediction == base["true_answer"]
        rows.append(
            {
                "task_id": task_id,
                "selector_inputs": inputs,
                "action": action,
                "baseline_prediction": base["baseline_prediction"],
                "rank5_prediction": rank5_result["predicted_answer"],
                "guarded_prediction": guarded_prediction,
                "true_answer": base["true_answer"],
                "baseline_is_solved": baseline_is_solved,
                "rank5_is_solved": rank5_is_solved,
                "guarded_is_solved": guarded_is_solved,
                "fix": (not baseline_is_solved) and guarded_is_solved,
                "harm": baseline_is_solved and not guarded_is_solved,
                "rank5_harm": baseline_is_solved and not rank5_is_solved,
                "clean_label": base["clean_label"],
            }
        )
    return rows


def _fix_harm(rows: List[Dict[str, Any]]) -> str:
    return f"{sum(1 for row in rows if row['fix'])}/{sum(1 for row in rows if row['harm'])}"


def build_guard_summary() -> Dict[str, Any]:
    rows = build_guard_rows()
    clean_rows = [row for row in rows if row["clean_label"] == "clean"]
    noisy_rows = [row for row in rows if row["clean_label"] != "clean"]
    return {
        "rule": RULE_NAME,
        "num_tasks": len(rows),
        "baseline_solved": sum(1 for row in rows if row["baseline_is_solved"]),
        "rank5_solved": sum(1 for row in rows if row["rank5_is_solved"]),
        "guarded_solved": sum(1 for row in rows if row["guarded_is_solved"]),
        "switch_tasks": [row["task_id"] for row in rows if row["action"] == "accept_rank5"],
        "fallback_tasks": [row["task_id"] for row in rows if row["action"] == "fallback_to_arg"],
        "fix_harm": _fix_harm(rows),
        "clean_fix_harm": _fix_harm(clean_rows),
        "noisy_fix_harm": _fix_harm(noisy_rows),
        "suppressed_rank5_harm_tasks": [
            row["task_id"]
            for row in rows
            if row["rank5_harm"] and row["action"] == "fallback_to_arg"
        ],
        "selector_input_field_violations": _input_violation_count(rows),
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{task}` | `{action}` | `{base}` | `{rank5}` | `{guarded}` | `{truth}` | `{label}` | `{fix}` | `{harm}` |".format(
            task=row["task_id"],
            action=row["action"],
            base=row["baseline_prediction"],
            rank5=row["rank5_prediction"],
            guarded=row["guarded_prediction"],
            truth=row["true_answer"],
            label=row["clean_label"],
            fix=row["fix"],
            harm=row["harm"],
        )
        for row in summary["rows"]
    ]
    return "\n".join(
        [
            "# R107 Objective-Safety Rank5 Guard Replay",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Baseline solved: `{summary['baseline_solved']}/{summary['num_tasks']}`",
            f"- Rank5 solved: `{summary['rank5_solved']}/{summary['num_tasks']}`",
            f"- Guarded solved: `{summary['guarded_solved']}/{summary['num_tasks']}`",
            f"- Switch tasks: `{summary['switch_tasks']}`",
            f"- Fallback tasks: `{summary['fallback_tasks']}`",
            f"- Fix/harm: `{summary['fix_harm']}`",
            f"- Clean fix/harm: `{summary['clean_fix_harm']}`",
            f"- Noisy fix/harm: `{summary['noisy_fix_harm']}`",
            f"- Suppressed rank5 harms: `{summary['suppressed_rank5_harm_tasks']}`",
            f"- Selector input field violations: `{summary['selector_input_field_violations']}`",
            "",
            "| Task | Action | ARG | Rank5 | Guarded | Truth | Audit label | Fix | Harm |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "The R095 objective-safety guard suppresses the R106 rank5 clean harm on `task_8` "
            "while preserving the rank5 clean recovery on `task_250`. This is still only a "
            "four-task replay over existing features and outputs; it is a candidate guard for "
            "the next smoke/prospective validation, not a held-out result.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay objective-safety guard over R106 rank5 outputs.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_guard_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R107 objective-safety rank5 guard replay: "
        f"guarded={summary['guarded_solved']}/{summary['num_tasks']} "
        f"clean_fix_harm={summary['clean_fix_harm']}"
    )


if __name__ == "__main__":
    main()
