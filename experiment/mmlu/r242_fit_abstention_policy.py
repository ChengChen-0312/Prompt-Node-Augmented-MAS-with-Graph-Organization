from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r232_tiny_diagnostic_preflight_audit import load_jsonl


def policy_spec_switches(spec: Dict[str, int], features: Dict[str, Any]) -> bool:
    return (
        bool(features.get("objective_differs"))
        and int(features.get("objective_top_score") or 0) >= int(spec["score_threshold"])
        and int(features.get("baseline_direct_majority_count") or 0) < int(spec["majority_count_lt"])
    )


def evaluate_policy_spec(spec: Dict[str, int], rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    details = []
    for row in rows:
        switch = policy_spec_switches(spec, row.get("features", {}))
        selected = row.get("objective_prediction") if switch else row.get("baseline_prediction")
        true_answer = row.get("true_answer")
        baseline_correct = row.get("baseline_prediction") == true_answer
        selected_correct = selected == true_answer
        clean = row.get("clean_label") == "clean"
        details.append(
            {
                "task_id": row.get("task_id"),
                "split_role": row.get("split_role"),
                "switch": switch,
                "selected_prediction": selected,
                "selected_correct": selected_correct,
                "baseline_correct": baseline_correct,
                "fix": (not baseline_correct) and selected_correct,
                "harm": baseline_correct and not selected_correct,
                "clean_harm": clean and baseline_correct and not selected_correct,
            }
        )
    return {
        "records": len(details),
        "switches": sum(1 for row in details if row["switch"]),
        "accuracy_count": sum(1 for row in details if row["selected_correct"]),
        "accuracy": sum(1 for row in details if row["selected_correct"]) / len(details) if details else None,
        "baseline_accuracy_count": sum(1 for row in details if row["baseline_correct"]),
        "fixes": sum(1 for row in details if row["fix"]),
        "harms": sum(1 for row in details if row["harm"]),
        "clean_harms": sum(1 for row in details if row["clean_harm"]),
        "details": details,
    }


def candidate_specs() -> List[Dict[str, int]]:
    return [
        {"score_threshold": threshold, "majority_count_lt": majority_lt}
        for threshold in range(0, 12)
        for majority_lt in range(0, 5)
    ]


def _fit_key(item: Dict[str, Any]) -> tuple:
    metrics = item["train_metrics"]
    spec = item["spec"]
    return (
        -metrics["harms"],
        -metrics["clean_harms"],
        metrics["accuracy_count"],
        metrics["fixes"],
        metrics["switches"],
        spec["majority_count_lt"],
        spec["score_threshold"],
    )


def fit_policy_spec(train_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    candidates = []
    for spec in candidate_specs():
        metrics = evaluate_policy_spec(spec, train_rows)
        candidates.append({"spec": spec, "train_metrics": {k: v for k, v in metrics.items() if k != "details"}})
    best = sorted(candidates, key=_fit_key, reverse=True)[0]
    best["candidate_count"] = len(candidates)
    return best


def run_fit(
    feature_table_jsonl: str,
    output_json: str,
    report_md: str,
) -> Dict[str, Any]:
    rows = load_jsonl(feature_table_jsonl)
    train_rows = [row for row in rows if row.get("split_role") == "train"]
    frozen_rows = [row for row in rows if row.get("split_role") == "frozen_eval"]
    fitted = fit_policy_spec(train_rows)
    frozen_metrics = evaluate_policy_spec(fitted["spec"], frozen_rows)
    all_metrics = evaluate_policy_spec(fitted["spec"], rows)
    summary = {
        "run_id": "R242",
        "title": "Fit train-time abstention policy",
        "claim_boundary": "Offline train/frozen policy fit only; no API, no superiority claim, and no SCI-Q2 readiness claim.",
        "no_api": True,
        "feature_table_jsonl": feature_table_jsonl,
        "spec": fitted["spec"],
        "candidate_count": fitted["candidate_count"],
        "train_metrics": fitted["train_metrics"],
        "frozen_eval_metrics": {k: v for k, v in frozen_metrics.items() if k != "details"},
        "all_metrics": {k: v for k, v in all_metrics.items() if k != "details"},
    }
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))
    return summary


def _line(name: str, metrics: Dict[str, Any]) -> str:
    return (
        f"| {name} | `{metrics['accuracy_count']}/{metrics['records']}` | "
        f"`{metrics['baseline_accuracy_count']}/{metrics['records']}` | "
        f"`{metrics['fixes']}/{metrics['harms']}` | `{metrics['clean_harms']}` | `{metrics['switches']}` |"
    )


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R242 Fit Train-Time Abstention Policy",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Fitted spec: `objective_top_score >= {summary['spec']['score_threshold']} and baseline_direct_majority_count < {summary['spec']['majority_count_lt']}`",
            f"- Candidate specs: `{summary['candidate_count']}`",
            "",
            "| Split | Policy Acc | Baseline Acc | Fix/Harm | Clean Harms | Switches |",
            "|---|---:|---:|---:|---:|---:|",
            _line("train", summary["train_metrics"]),
            _line("frozen_eval", summary["frozen_eval_metrics"]),
            _line("all", summary["all_metrics"]),
            "",
            "## Boundary",
            "",
            "The fitted policy is selected only on train rows and evaluated on frozen rows. This is still offline evidence and does not authorize a paper-level superiority claim.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fit interpretable abstention policy.")
    parser.add_argument("--feature_table_jsonl", required=True)
    parser.add_argument("--output_json", required=True)
    parser.add_argument("--report_md", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_fit(
        feature_table_jsonl=args.feature_table_jsonl,
        output_json=args.output_json,
        report_md=args.report_md,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
