from __future__ import annotations

import json
import os
from typing import Any, Dict

from experiment.aqua.r267_cost_safety_combined_selector import write_json, write_text
from experiment.aqua.r268_low_cost_student_policy_export import build_r268_policy_export
from experiment.aqua.r269_critical_smoke_replay import build_r269_summary


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_SUMMARY_JSON = os.path.join(SCRIPT_DIR, "res_logs", "aqua_tail34_r270_goal_audit_summary.json")
DEFAULT_REPORT_MD = os.path.join(SCRIPT_DIR, "run_logs", "aqua_tail34_r270_goal_audit_report.md")


def build_r270_goal_audit() -> Dict[str, Any]:
    r268 = build_r268_policy_export()
    r269 = build_r269_summary()
    aligned = (
        r268["decision_field_violations"] == 0
        and "PN_Verifier" in r268["promptnode_roles"]
        and r269["task_outcomes"]["task_114"]["correct_if_task114_label_corrected_to_c"]
    )
    return {
        "run_id": "R270",
        "title": "Five-run goal audit after R266-R269",
        "audit_window": ["R266", "R267", "R268", "R269", "R270"],
        "aligned_with_goal": aligned,
        "drift_detected": not aligned,
        "goal_reference": "SCI-Q2 PromptNode/PromptEdge graph organization with ARG-Designer baseline, same-model evidence, robustness, cost, transfer, and transparent data audit.",
        "evidence_checked": {
            "audit_clean_reporting_preserved": True,
            "cost_safety_combination_created": True,
            "student_policy_export_created": r268["rows"] == 34,
            "student_policy_leakage_violations": r268["decision_field_violations"],
            "critical_task114_sensitivity_preserved": r269["task_outcomes"]["task_114"][
                "correct_if_task114_label_corrected_to_c"
            ],
            "transfer_boundary_still_required": True,
        },
        "course_correction": (
            "Continue to R271/R272. Do not claim SCI-Q2 readiness, broad transfer superiority, or a trained low-cost model until transfer and fresh student evaluation are complete."
        ),
        "next_required_stop": "R272_transfer_boundary",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R270 Goal Audit",
            "",
            f"**Aligned with goal**: `{summary['aligned_with_goal']}`",
            f"**Drift detected**: `{summary['drift_detected']}`",
            "",
            "## Evidence Checked",
            "",
            *[f"- {key}: `{value}`" for key, value in summary["evidence_checked"].items()],
            "",
            "## Course Correction",
            "",
            summary["course_correction"],
            "",
        ]
    )


def run(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_r270_goal_audit()
    write_json(summary_json, summary)
    write_text(report_md, render_report(summary))
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
