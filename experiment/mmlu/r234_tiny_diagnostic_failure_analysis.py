from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, List

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r232_tiny_diagnostic_preflight_audit import load_json, load_jsonl


def normalize_label(value: Any) -> str:
    label = str(value or "").strip().upper()
    if label.startswith("NONE"):
        return "NONE"
    return label[:1] if label[:1] in {"A", "B", "C", "D", "E"} else "NONE"


def _variant_map(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {str(row.get("control_variant")): row for row in rows}


def classify_task_outcome(
    task_rows: List[Dict[str, Any]],
    audit_row: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    variants = _variant_map(task_rows)
    proposed = variants.get("proposed_router_final", {})
    abstain = variants.get("abstain_only_router", {})
    always = variants.get("always_switch_to_objective", {})
    node_only = variants.get("node_only_no_promptedge_text", {})
    random_row = variants.get("random_switch_labels_same_rate", {})

    true_answer = normalize_label(proposed.get("true_answer") or abstain.get("true_answer"))
    baseline = normalize_label(proposed.get("baseline_prediction") or abstain.get("baseline_prediction"))
    objective = normalize_label(proposed.get("objective_prediction") or always.get("objective_prediction"))
    proposed_pred = normalize_label(proposed.get("predicted_answer"))
    abstain_pred = normalize_label(abstain.get("predicted_answer"))
    always_pred = normalize_label(always.get("predicted_answer"))
    node_only_pred = normalize_label(node_only.get("predicted_answer"))
    random_pred = normalize_label(random_row.get("predicted_answer"))

    baseline_correct = baseline == true_answer
    objective_correct = objective == true_answer
    proposed_correct = proposed_pred == true_answer
    proposed_fix = (not baseline_correct) and proposed_correct
    proposed_harm = baseline_correct and not proposed_correct

    if objective_correct and proposed_correct:
        failure_mode = "objective_correct_router_followed"
    elif proposed_harm and not objective_correct:
        failure_mode = "objective_wrong_router_harmed_baseline"
    elif (not baseline_correct) and (not objective_correct):
        failure_mode = "baseline_and_objective_wrong"
    elif baseline_correct and proposed_correct:
        failure_mode = "baseline_correct_router_safe"
    else:
        failure_mode = "mixed_or_unclassified"

    audit_row = audit_row or {}
    return {
        "task_id": proposed.get("task_id") or abstain.get("task_id"),
        "true_answer": true_answer,
        "baseline_prediction": baseline,
        "objective_prediction": objective,
        "proposed_prediction": proposed_pred,
        "abstain_prediction": abstain_pred,
        "always_prediction": always_pred,
        "node_only_prediction": node_only_pred,
        "random_prediction": random_pred,
        "baseline_correct": baseline_correct,
        "objective_correct": objective_correct,
        "proposed_correct": proposed_correct,
        "proposed_fix": proposed_fix,
        "proposed_harm": proposed_harm,
        "proposed_matches_always": proposed_pred == always_pred,
        "proposed_matches_node_only": proposed_pred == node_only_pred,
        "failure_mode": failure_mode,
        "clean_label": audit_row.get("clean_label", "unknown"),
        "gold_binding_status": audit_row.get("gold_binding_status", "unknown"),
        "rationale_issue": audit_row.get("rationale_issue", "unknown"),
        "audit_brief_reason": audit_row.get("brief_reason", ""),
    }


def summarize_failure_modes(outcomes: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "tasks": len(outcomes),
        "failure_modes": dict(sorted(Counter(row["failure_mode"] for row in outcomes).items())),
        "clean_labels": dict(sorted(Counter(row.get("clean_label", "unknown") for row in outcomes).items())),
        "proposed_fixes": sum(1 for row in outcomes if row.get("proposed_fix")),
        "proposed_harms": sum(1 for row in outcomes if row.get("proposed_harm")),
        "proposed_matches_always": sum(1 for row in outcomes if row.get("proposed_matches_always")),
        "proposed_matches_node_only": sum(1 for row in outcomes if row.get("proposed_matches_node_only")),
        "objective_correct": sum(1 for row in outcomes if row.get("objective_correct")),
        "baseline_correct": sum(1 for row in outcomes if row.get("baseline_correct")),
    }


def load_audit_lookup(paths: List[str]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for path in paths:
        if not os.path.exists(path):
            continue
        for row in load_jsonl(path):
            task_id = str(row.get("task_id") or "")
            if task_id and task_id not in lookup:
                lookup[task_id] = row
    return lookup


def run_failure_analysis(
    r233_results_jsonl: str,
    r233_summary_json: str,
    audit_paths: List[str],
    output_json: str,
    report_md: str,
) -> Dict[str, Any]:
    rows = load_jsonl(r233_results_jsonl)
    r233_summary = load_json(r233_summary_json)
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("task_id"))].append(row)
    audit_lookup = load_audit_lookup(audit_paths)
    outcomes = [
        classify_task_outcome(task_rows, audit_lookup.get(task_id))
        for task_id, task_rows in sorted(grouped.items())
    ]
    summary = summarize_failure_modes(outcomes)
    summary.update(
        {
            "run_id": "R234",
            "title": "Tiny diagnostic failure analysis",
            "claim_boundary": "Failure analysis only; no new API, no superiority claim, and no SCI-Q2 readiness claim.",
            "no_api": True,
            "r233_accuracy": r233_summary.get("accuracy"),
            "r233_api_cost": r233_summary.get("api_cost"),
            "r233_api_errors": r233_summary.get("api_errors"),
            "outcomes": outcomes,
            "audit_paths": audit_paths,
        }
    )
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R234 Tiny Diagnostic Failure Analysis",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Summary",
        "",
        f"- Tasks: `{summary['tasks']}`",
        f"- Failure modes: `{summary['failure_modes']}`",
        f"- Clean labels: `{summary['clean_labels']}`",
        f"- Proposed fixes/harms: `{summary['proposed_fixes']}/{summary['proposed_harms']}`",
        f"- Proposed matches always-switch: `{summary['proposed_matches_always']}/{summary['tasks']}`",
        f"- Proposed matches node-only: `{summary['proposed_matches_node_only']}/{summary['tasks']}`",
        f"- Baseline correct tasks: `{summary['baseline_correct']}`",
        f"- Objective correct tasks: `{summary['objective_correct']}`",
        "",
        "## Per-Task Breakdown",
        "",
        "| Task | Clean | Baseline | Objective | Proposed | Mode | Fix/Harm |",
        "|---|---|---:|---:|---:|---|---:|",
    ]
    for row in summary["outcomes"]:
        rows.append(
            f"| `{row['task_id']}` | `{row['clean_label']}` | `{row['baseline_prediction']}` | `{row['objective_prediction']}` | `{row['proposed_prediction']}` | `{row['failure_mode']}` | `{int(row['proposed_fix'])}/{int(row['proposed_harm'])}` |"
        )
    rows.extend(
        [
            "",
            "## Interpretation",
            "",
            "The current prompt-level router is not learning an abstention boundary. It follows the objective prediction on every API-routed task, matching the always-switch control and the node-only control. This explains the balanced `1/1` fix/harm pattern and blocks any expansion of this prompt as a robust SCI-Q2 result.",
            "",
            "The next method iteration should train or distill an abstention policy that uses conflict and support features to suppress objective switches when the baseline has strong direct support, instead of asking the LLM router to infer that boundary from feature names.",
            "",
        ]
    )
    return "\n".join(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze R233 tiny diagnostic failure modes.")
    parser.add_argument("--r233_results_jsonl", required=True)
    parser.add_argument("--r233_summary_json", required=True)
    parser.add_argument("--audit_paths", nargs="*", default=[])
    parser.add_argument("--output_json", required=True)
    parser.add_argument("--report_md", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_failure_analysis(
        r233_results_jsonl=args.r233_results_jsonl,
        r233_summary_json=args.r233_summary_json,
        audit_paths=args.audit_paths,
        output_json=args.output_json,
        report_md=args.report_md,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
