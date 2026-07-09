import argparse
import datetime
import json
import os
import sys
from typing import Any, Dict, List


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_gate_r058_stress import _repo_path  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r098_template_plan_replay_on_r092"
CLAIM_BOUNDARY = "R097 plan replay over R092 forced-template results; no new API; not R095 reproduction"

DEFAULT_R095_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r095_objective_safety_composed_summary.json"
DEFAULT_R097_PLAN_JSONL = "experiment/aqua/aqua_tail34_r097_objective_safety_template_plan.jsonl"
DEFAULT_R092_FORCED_JSONL = "experiment/aqua/aqua_tail34_r092_forced_template_rank1_results.jsonl"
DEFAULT_REPLAY_JSONL = "experiment/aqua/aqua_tail34_r098_objective_safety_template_plan_replay.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r098_objective_safety_template_plan_replay_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r098_objective_safety_template_plan_replay_report.md"


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    abs_path = _repo_path(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _index_by_task(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {row["task_id"]: row for row in rows}


def build_template_plan_replay_rows(
    r095_summary_json: str = DEFAULT_R095_SUMMARY_JSON,
    r097_plan_jsonl: str = DEFAULT_R097_PLAN_JSONL,
    r092_forced_jsonl: str = DEFAULT_R092_FORCED_JSONL,
) -> List[Dict[str, Any]]:
    r095_rows = _load_json(r095_summary_json)["rows"]
    plan_by_task = _index_by_task(_load_jsonl(r097_plan_jsonl))
    forced_by_task = _index_by_task(_load_jsonl(r092_forced_jsonl))
    rows = []
    for r095 in r095_rows:
        task_id = r095["task_id"]
        plan = plan_by_task[task_id]
        forced = forced_by_task.get(task_id)
        should_switch = plan["target_action"] == "switch_to_objective"
        forced_prediction = forced.get("predicted_answer") if forced else None
        selected_prediction = forced_prediction if should_switch and forced_prediction else r095["baseline_prediction"]
        selected_is_solved = selected_prediction == r095["true_answer"]
        baseline_is_solved = bool(r095["baseline_is_solved"])
        desired_prediction_match = (
            forced_prediction == r095["objective_prediction"] if should_switch and forced else None
        )
        rows.append(
            {
                "task_id": task_id,
                "plan_action": plan["target_action"],
                "target_reason": plan["target_reason"],
                "baseline_prediction": r095["baseline_prediction"],
                "objective_prediction": r095["objective_prediction"],
                "template_prediction": forced_prediction if should_switch else None,
                "selected_prediction": selected_prediction,
                "true_answer": r095["true_answer"],
                "baseline_is_solved": baseline_is_solved,
                "selected_is_solved": selected_is_solved,
                "fix": (not baseline_is_solved) and selected_is_solved,
                "harm": baseline_is_solved and not selected_is_solved,
                "desired_prediction_match": desired_prediction_match,
                "clean_label": r095["clean_label"],
                "gold_binding_status": r095["gold_binding_status"],
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def _fix_harm(rows: List[Dict[str, Any]]) -> str:
    return f"{sum(1 for row in rows if row['fix'])}/{sum(1 for row in rows if row['harm'])}"


def build_template_plan_replay_summary() -> Dict[str, Any]:
    rows = build_template_plan_replay_rows()
    switch_rows = [row for row in rows if row["plan_action"] == "switch_to_objective"]
    clean_rows = [row for row in rows if row["clean_label"] == "clean"]
    noisy_rows = [row for row in rows if row["clean_label"] != "clean"]
    clean_switch_rows = [row for row in switch_rows if row["clean_label"] == "clean"]
    noisy_switch_rows = [row for row in switch_rows if row["clean_label"] != "clean"]
    return {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "num_tasks": len(rows),
        "arg_baseline_solved": sum(1 for row in rows if row["baseline_is_solved"]),
        "template_plan_replay_solved": sum(1 for row in rows if row["selected_is_solved"]),
        "switch_plan_count": len(switch_rows),
        "forced_result_available_for_switches": sum(
            1 for row in switch_rows if row["template_prediction"] is not None
        ),
        "desired_prediction_match_count": sum(
            1 for row in switch_rows if row["desired_prediction_match"] is True
        ),
        "desired_prediction_mismatch_tasks": [
            row["task_id"] for row in switch_rows if row["desired_prediction_match"] is False
        ],
        "clean_desired_prediction_match_tasks": [
            row["task_id"] for row in clean_switch_rows if row["desired_prediction_match"] is True
        ],
        "noisy_desired_prediction_match_tasks": [
            row["task_id"] for row in noisy_switch_rows if row["desired_prediction_match"] is True
        ],
        "fix_harm": _fix_harm(rows),
        "clean_fix_harm": _fix_harm(clean_rows),
        "noisy_fix_harm": _fix_harm(noisy_rows),
        "fix_tasks": [row["task_id"] for row in rows if row["fix"]],
        "harm_tasks": [row["task_id"] for row in rows if row["harm"]],
        "rows": rows,
        "replay_jsonl": DEFAULT_REPLAY_JSONL,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    switch_rows = [row for row in summary["rows"] if row["plan_action"] == "switch_to_objective"]
    table_rows = [
        "| `{task}` | `{label}` | `{baseline}` | `{objective}` | `{template}` | `{match}` | `{selected}` | `{fix}` | `{harm}` |".format(
            task=row["task_id"],
            label=row["clean_label"],
            baseline=row["baseline_prediction"],
            objective=row["objective_prediction"],
            template=row["template_prediction"],
            match=row["desired_prediction_match"],
            selected=row["selected_prediction"],
            fix=row["fix"],
            harm=row["harm"],
        )
        for row in switch_rows
    ]
    return "\n".join(
        [
            "# R098 R097 Template Plan Replay over R092 Forced Results",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- ARG baseline solved: `{summary['arg_baseline_solved']}/{summary['num_tasks']}`",
            f"- Template-plan replay solved: `{summary['template_plan_replay_solved']}/{summary['num_tasks']}`",
            f"- Switch plan count: `{summary['switch_plan_count']}`",
            f"- Forced result available for switches: `{summary['forced_result_available_for_switches']}`",
            f"- Desired prediction matches: `{summary['desired_prediction_match_count']}`",
            f"- Desired prediction mismatches: `{summary['desired_prediction_mismatch_tasks']}`",
            f"- Fix/harm: `{summary['fix_harm']}`",
            f"- Clean fix/harm: `{summary['clean_fix_harm']}`",
            f"- Noisy fix/harm: `{summary['noisy_fix_harm']}`",
            "",
            "## Switch Replay",
            "",
            "| Task | Audit label | ARG | R095 objective | R092 template | Match | Selected | Fix | Harm |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "The explicit R083 rank-1 template plan reproduces the noisy `task_108` switch but not "
            "the clean `task_250` objective switch. Therefore R097 should not be promoted to a "
            "full held-out run as-is; the next step must search or train a template/graph policy "
            "that can recover the clean switch before spending on full API validation.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay R097 template plan over existing R092 forced results.")
    parser.add_argument("--replay-jsonl", default=DEFAULT_REPLAY_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    rows = build_template_plan_replay_rows()
    _write_jsonl(args.replay_jsonl, rows)
    summary = build_template_plan_replay_summary()
    summary["replay_jsonl"] = args.replay_jsonl
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R098 template-plan replay: "
        f"selected={summary['template_plan_replay_solved']}/{summary['num_tasks']} "
        f"mismatch={summary['desired_prediction_mismatch_tasks']}"
    )


if __name__ == "__main__":
    main()
