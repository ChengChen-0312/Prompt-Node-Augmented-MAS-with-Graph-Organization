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


RULE_NAME = "r106_rank5_regression_smoke_report"
CLAIM_BOUNDARY = "four-task rank5 regression smoke; consensus not clean-safe"

DEFAULT_R095_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r095_objective_safety_composed_summary.json"
DEFAULT_R103_RESULTS_JSONL = "experiment/aqua/aqua_tail34_r103_rank2_regression_smoke_results.jsonl"
DEFAULT_R106_RESULTS_JSONL = "experiment/aqua/aqua_tail34_r106_rank5_regression_smoke_results.jsonl"
DEFAULT_R106_SUMMARY_JSONL = "experiment/aqua/res_logs/aqua_tail34_r106_rank5_regression_smoke_summary.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r106_rank5_regression_smoke_report_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r106_rank5_regression_smoke_report.md"

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


def _rank2_index() -> Dict[str, Dict[str, Any]]:
    return {row["task_id"]: row for row in _load_jsonl(DEFAULT_R103_RESULTS_JSONL)}


def _role(task_id: str) -> str:
    if task_id in CLEAN_HARM_GUARDS:
        return "clean_harm_guard"
    if task_id in CLEAN_RECOVERY_TARGETS:
        return "clean_recovery_target"
    if task_id in NOISY_OPTIONAL_TARGETS:
        return "noisy_optional_target"
    return "other"


def build_rank5_smoke_rows() -> List[Dict[str, Any]]:
    baseline = _baseline_index()
    rank2 = _rank2_index()
    rows = []
    for result in _load_jsonl(DEFAULT_R106_RESULTS_JSONL):
        task_id = result["task_id"]
        base = baseline[task_id]
        rank2_result = rank2[task_id]
        rank5_is_solved = bool(result["is_solved"])
        baseline_is_solved = bool(base["baseline_is_solved"])
        rank2_prediction = rank2_result["predicted_answer"]
        rank5_prediction = result["predicted_answer"]
        rows.append(
            {
                "task_id": task_id,
                "baseline_prediction": base["baseline_prediction"],
                "rank2_prediction": rank2_prediction,
                "rank5_prediction": rank5_prediction,
                "true_answer": base["true_answer"],
                "baseline_is_solved": baseline_is_solved,
                "rank2_is_solved": bool(rank2_result["is_solved"]),
                "rank5_is_solved": rank5_is_solved,
                "fix": (not baseline_is_solved) and rank5_is_solved,
                "harm": baseline_is_solved and not rank5_is_solved,
                "rank2_rank5_consensus": rank2_prediction == rank5_prediction,
                "clean_label": base["clean_label"],
                "role": _role(task_id),
            }
        )
    return rows


def _fix_harm(rows: List[Dict[str, Any]]) -> str:
    return f"{sum(1 for row in rows if row['fix'])}/{sum(1 for row in rows if row['harm'])}"


def build_rank5_smoke_summary() -> Dict[str, Any]:
    rows = build_rank5_smoke_rows()
    clean_rows = [row for row in rows if row["clean_label"] == "clean"]
    noisy_rows = [row for row in rows if row["clean_label"] != "clean"]
    consensus_rows = [row for row in rows if row["rank2_rank5_consensus"]]
    run_summary = _load_jsonl(DEFAULT_R106_SUMMARY_JSONL)[-1]
    return {
        "rule": RULE_NAME,
        "num_tasks": len(rows),
        "baseline_solved": sum(1 for row in rows if row["baseline_is_solved"]),
        "rank5_solved": sum(1 for row in rows if row["rank5_is_solved"]),
        "fix_harm": _fix_harm(rows),
        "clean_fix_harm": _fix_harm(clean_rows),
        "noisy_fix_harm": _fix_harm(noisy_rows),
        "clean_harm_guard_harms": [
            row["task_id"] for row in rows if row["role"] == "clean_harm_guard" and row["harm"]
        ],
        "clean_recovery_targets_solved": [
            row["task_id"]
            for row in rows
            if row["role"] == "clean_recovery_target" and row["rank5_is_solved"]
        ],
        "rank2_rank5_consensus_tasks": [row["task_id"] for row in consensus_rows],
        "consensus_clean_recovery_solved": [
            row["task_id"]
            for row in consensus_rows
            if row["role"] == "clean_recovery_target" and row["rank5_is_solved"]
        ],
        "total_cost": float(run_summary.get("cost", 0.0)),
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{task}` | `{role}` | `{label}` | `{base}` | `{rank2}` | `{rank5}` | `{truth}` | `{fix}` | `{harm}` | `{consensus}` |".format(
            task=row["task_id"],
            role=row["role"],
            label=row["clean_label"],
            base=row["baseline_prediction"],
            rank2=row["rank2_prediction"],
            rank5=row["rank5_prediction"],
            truth=row["true_answer"],
            fix=row["fix"],
            harm=row["harm"],
            consensus=row["rank2_rank5_consensus"],
        )
        for row in summary["rows"]
    ]
    return "\n".join(
        [
            "# R106 Rank5 Regression Smoke Report",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Baseline solved: `{summary['baseline_solved']}/{summary['num_tasks']}`",
            f"- Rank5 solved: `{summary['rank5_solved']}/{summary['num_tasks']}`",
            f"- Fix/harm: `{summary['fix_harm']}`",
            f"- Clean fix/harm: `{summary['clean_fix_harm']}`",
            f"- Noisy fix/harm: `{summary['noisy_fix_harm']}`",
            f"- Clean harm guard harms: `{summary['clean_harm_guard_harms']}`",
            f"- Clean recovery targets solved: `{summary['clean_recovery_targets_solved']}`",
            f"- Rank2/rank5 consensus tasks: `{summary['rank2_rank5_consensus_tasks']}`",
            f"- Consensus clean recovery solved: `{summary['consensus_clean_recovery_solved']}`",
            f"- Total cost: `${summary['total_cost']:.6f}`",
            "",
            "| Task | Role | Audit label | ARG | Rank2 | Rank5 | Truth | Fix | Harm | Rank2=Rank5 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "Rank5 recovers clean `task_250` and noisy `task_108`, but it also harms clean guard "
            "`task_8`. Rank2/rank5 agreement is too conservative for clean recovery because the only "
            "agreement point is noisy `task_108`. This rejects both plain rank5 deployment and simple "
            "rank-consensus gating as SCI-Q2-level evidence.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize R106 rank5 regression smoke.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_rank5_smoke_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R106 rank5 smoke report: "
        f"rank5={summary['rank5_solved']}/{summary['num_tasks']} "
        f"clean_fix_harm={summary['clean_fix_harm']} "
        f"consensus={summary['rank2_rank5_consensus_tasks']}"
    )


if __name__ == "__main__":
    main()
