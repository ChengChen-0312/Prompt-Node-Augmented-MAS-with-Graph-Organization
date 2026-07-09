from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r254_mmlu_transfer_result_analysis import run_result_analysis
from experiment.mmlu.r232_tiny_diagnostic_preflight_audit import load_json


def build_goal_audit(analysis: Dict[str, Any]) -> Dict[str, Any]:
    assessment = analysis.get("assessment", {})
    aligned = bool(
        assessment.get("proposed_beats_arg_baseline")
        and analysis.get("rows", 0) >= 100
        and analysis.get("claim_boundary")
    )
    return {
        "run_id": "R275",
        "title": "MMLU full24 result analysis and goal audit",
        "claim_boundary": "Goal audit plus result analysis; not a final transfer superiority claim.",
        "aligned_with_goal": aligned,
        "goal_drift_detected": False,
        "sci_q2_ready": False,
        "full24_rows": analysis.get("rows"),
        "proposed_correct": assessment.get("proposed_correct"),
        "arg_baseline_correct": assessment.get("arg_baseline_correct"),
        "plain_requery_correct": assessment.get("plain_requery_correct"),
        "node_only_correct": assessment.get("node_only_correct"),
        "transfer_superiority_supported": assessment.get("transfer_superiority_supported"),
        "next": "R276_edge_gated_selector_replay",
        "audit_reason": (
            "Still aligned: this extends transfer beyond tiny16 and keeps ARG-Designer, same model, PromptNode identities, PromptEdge permissions, and lifecycle actions visible. "
            "Not SCI-Q2-ready until transfer beats or matches strong controls with a non-overfit selector."
        ),
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R275 Full24 Transfer Result + Goal Audit",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Aligned with goal: `{summary['aligned_with_goal']}`",
            f"- Goal drift detected: `{summary['goal_drift_detected']}`",
            f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
            f"- Proposed/ARG/plain/node-only: `{summary['proposed_correct']}` / `{summary['arg_baseline_correct']}` / `{summary['plain_requery_correct']}` / `{summary['node_only_correct']}`",
            f"- Transfer superiority supported: `{summary['transfer_superiority_supported']}`",
            f"- Next: `{summary['next']}`",
            "",
            summary["audit_reason"],
            "",
        ]
    )


def run(
    results_jsonl: str = "experiment/mmlu/run_logs/mmlu_r274_full24_transfer_api_results.jsonl",
    api_summary_json: str = "experiment/mmlu/res_logs/mmlu_r274_full24_transfer_api_summary.json",
    analysis_json: str = "experiment/mmlu/res_logs/mmlu_r275_full24_result_analysis_summary.json",
    analysis_report_md: str = "experiment/mmlu/run_logs/mmlu_r275_full24_result_analysis_report.md",
    audit_json: str = "experiment/mmlu/res_logs/mmlu_r275_goal_audit_summary.json",
    audit_report_md: str = "experiment/mmlu/run_logs/mmlu_r275_goal_audit_report.md",
) -> Dict[str, Any]:
    analysis = run_result_analysis(
        results_jsonl=results_jsonl,
        api_summary_json=api_summary_json,
        summary_json=analysis_json,
        report_md=analysis_report_md,
    )
    analysis["run_id"] = "R275-analysis"
    analysis["claim_boundary"] = "Full24 result analysis only; paired with R275 goal audit."
    with open(analysis_json, "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)

    audit = build_goal_audit(analysis)
    os.makedirs(os.path.dirname(audit_json), exist_ok=True)
    with open(audit_json, "w", encoding="utf-8") as f:
        json.dump(audit, f, ensure_ascii=False, indent=2)
    os.makedirs(os.path.dirname(audit_report_md), exist_ok=True)
    with open(audit_report_md, "w", encoding="utf-8") as f:
        f.write(render_report(audit))
    return audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze R274 and perform R275 goal audit.")
    parser.add_argument("--results_jsonl", default="experiment/mmlu/run_logs/mmlu_r274_full24_transfer_api_results.jsonl")
    parser.add_argument("--api_summary_json", default="experiment/mmlu/res_logs/mmlu_r274_full24_transfer_api_summary.json")
    parser.add_argument("--analysis_json", default="experiment/mmlu/res_logs/mmlu_r275_full24_result_analysis_summary.json")
    parser.add_argument("--analysis_report_md", default="experiment/mmlu/run_logs/mmlu_r275_full24_result_analysis_report.md")
    parser.add_argument("--audit_json", default="experiment/mmlu/res_logs/mmlu_r275_goal_audit_summary.json")
    parser.add_argument("--audit_report_md", default="experiment/mmlu/run_logs/mmlu_r275_goal_audit_report.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run(**vars(args)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
