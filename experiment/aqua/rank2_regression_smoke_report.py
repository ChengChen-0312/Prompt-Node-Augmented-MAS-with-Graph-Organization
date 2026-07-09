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


RULE_NAME = "r103_rank2_regression_smoke_report"
CLAIM_BOUNDARY = "four-task rank2 regression smoke; rejects R101 heuristic as deployable selector"

DEFAULT_R095_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r095_objective_safety_composed_summary.json"
DEFAULT_R103_RESULTS_JSONL = "experiment/aqua/aqua_tail34_r103_rank2_regression_smoke_results.jsonl"
DEFAULT_R103_SUMMARY_JSONL = "experiment/aqua/res_logs/aqua_tail34_r103_rank2_regression_smoke_summary.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r103_rank2_regression_smoke_report_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r103_rank2_regression_smoke_report.md"

CLEAN_HARM_GUARDS = ["task_8", "task_188"]
CLEAN_RECOVERY_TARGETS = ["task_250"]
NOISY_OPTIONAL_TARGETS = ["task_108"]


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _baseline_index() -> Dict[str, Dict[str, Any]]:
    return {row["task_id"]: row for row in _load_json(DEFAULT_R095_SUMMARY_JSON)["rows"]}


def build_rank2_smoke_rows() -> List[Dict[str, Any]]:
    baseline = _baseline_index()
    rows = []
    for result in _load_jsonl(DEFAULT_R103_RESULTS_JSONL):
        task_id = result["task_id"]
        base = baseline[task_id]
        rank2_is_solved = bool(result["is_solved"])
        baseline_is_solved = bool(base["baseline_is_solved"])
        rows.append(
            {
                "task_id": task_id,
                "baseline_prediction": base["baseline_prediction"],
                "rank2_prediction": result["predicted_answer"],
                "true_answer": base["true_answer"],
                "baseline_is_solved": baseline_is_solved,
                "rank2_is_solved": rank2_is_solved,
                "fix": (not baseline_is_solved) and rank2_is_solved,
                "harm": baseline_is_solved and not rank2_is_solved,
                "clean_label": base["clean_label"],
                "role": (
                    "clean_harm_guard"
                    if task_id in CLEAN_HARM_GUARDS
                    else "clean_recovery_target"
                    if task_id in CLEAN_RECOVERY_TARGETS
                    else "noisy_optional_target"
                    if task_id in NOISY_OPTIONAL_TARGETS
                    else "other"
                ),
            }
        )
    return rows


def _fix_harm(rows: List[Dict[str, Any]]) -> str:
    return f"{sum(1 for row in rows if row['fix'])}/{sum(1 for row in rows if row['harm'])}"


def build_rank2_smoke_summary() -> Dict[str, Any]:
    rows = build_rank2_smoke_rows()
    clean_rows = [row for row in rows if row["clean_label"] == "clean"]
    noisy_rows = [row for row in rows if row["clean_label"] != "clean"]
    run_summary = _load_jsonl(DEFAULT_R103_SUMMARY_JSONL)[-1]
    return {
        "rule": RULE_NAME,
        "num_tasks": len(rows),
        "baseline_solved": sum(1 for row in rows if row["baseline_is_solved"]),
        "rank2_solved": sum(1 for row in rows if row["rank2_is_solved"]),
        "fix_harm": _fix_harm(rows),
        "clean_fix_harm": _fix_harm(clean_rows),
        "noisy_fix_harm": _fix_harm(noisy_rows),
        "clean_harm_guard_harms": [
            row["task_id"] for row in rows if row["role"] == "clean_harm_guard" and row["harm"]
        ],
        "clean_recovery_targets_solved": [
            row["task_id"]
            for row in rows
            if row["role"] == "clean_recovery_target" and row["rank2_is_solved"]
        ],
        "total_cost": float(run_summary.get("cost", 0.0)),
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{task}` | `{role}` | `{label}` | `{base}` | `{rank2}` | `{truth}` | `{fix}` | `{harm}` |".format(
            task=row["task_id"],
            role=row["role"],
            label=row["clean_label"],
            base=row["baseline_prediction"],
            rank2=row["rank2_prediction"],
            truth=row["true_answer"],
            fix=row["fix"],
            harm=row["harm"],
        )
        for row in summary["rows"]
    ]
    return "\n".join(
        [
            "# R103 Rank2 Regression Smoke Report",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Baseline solved: `{summary['baseline_solved']}/{summary['num_tasks']}`",
            f"- Rank2 solved: `{summary['rank2_solved']}/{summary['num_tasks']}`",
            f"- Fix/harm: `{summary['fix_harm']}`",
            f"- Clean fix/harm: `{summary['clean_fix_harm']}`",
            f"- Noisy fix/harm: `{summary['noisy_fix_harm']}`",
            f"- Clean harm guard harms: `{summary['clean_harm_guard_harms']}`",
            f"- Clean recovery targets solved: `{summary['clean_recovery_targets_solved']}`",
            f"- Total cost: `${summary['total_cost']:.6f}`",
            "",
            "| Task | Role | Audit label | ARG | Rank2 | Truth | Fix | Harm |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "The R101 rank2 hypothesis does not survive the regression smoke: it fixes noisy `task_108`, "
            "but harms clean guard `task_188` and fails to reproduce the clean `task_250` recovery. "
            "Do not use this heuristic as a deployable selector.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize R103 rank2 regression smoke.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_rank2_smoke_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R103 rank2 smoke report: "
        f"rank2={summary['rank2_solved']}/{summary['num_tasks']} "
        f"clean_fix_harm={summary['clean_fix_harm']}"
    )


if __name__ == "__main__":
    main()
