from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_R339_SUMMARY = "experiment/mmlu/res_logs/mmlu_r339_selector_non_switch_failure_analysis_summary.json"
DEFAULT_R340_SUMMARY = "experiment/mmlu/res_logs/mmlu_r340_answer_bearing_candidate_generator_design_summary.json"
DEFAULT_R341_SUMMARY = "experiment/mmlu/res_logs/mmlu_r341_answer_bearing_candidate_generator_preflight_summary.json"
DEFAULT_R342_SUMMARY = "experiment/mmlu/res_logs/mmlu_r342_answer_bearing_candidate_generator_api_probe_summary.json"
DEFAULT_R343_SUMMARY = "experiment/mmlu/res_logs/mmlu_r343_answer_bearing_candidate_probe_analysis_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r344_goal_audit_after_candidate_generator_probe_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r344_goal_audit_after_candidate_generator_probe_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    p = _repo_path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def build_goal_audit_summary(
    r339_summary: str = DEFAULT_R339_SUMMARY,
    r340_summary: str = DEFAULT_R340_SUMMARY,
    r341_summary: str = DEFAULT_R341_SUMMARY,
    r342_summary: str = DEFAULT_R342_SUMMARY,
    r343_summary: str = DEFAULT_R343_SUMMARY,
) -> Dict[str, Any]:
    r339 = _load_json(r339_summary)
    r340 = _load_json(r340_summary)
    r341 = _load_json(r341_summary)
    r342 = _load_json(r342_summary)
    r343 = _load_json(r343_summary)
    r343_permissions = r343.get("claim_permissions", {})
    prompt_only_blocked = (
        r343.get("candidate_repairs_baseline_count") == 0
        and r343.get("candidate_follows_wrong_baseline_count") == r343.get("api_executed")
        and not bool(r343_permissions.get("more_api_same_design_allowed"))
    )
    return {
        "run_id": "R344",
        "title": "Goal audit after answer-bearing candidate generator probe",
        "claim_boundary": (
            "R344 is the five-iteration audit after R339-R343. It keeps the work aligned with the SCI-Q2 goal by "
            "blocking same-design prompt-only verifier expansion and redirecting to general, tool-backed PromptNodes."
        ),
        "no_api": True,
        "broad_api": False,
        "iterations_since_last_goal_check": ["R339", "R340", "R341", "R342", "R343"],
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "arg_baseline_preserved": bool(r339.get("baseline_wrong_tasks") is not None),
            "candidate_design_preflight_done": r340.get("run_id") == "R340" and r341.get("run_id") == "R341",
            "bounded_probe_executed": r342.get("api_executed") == 4,
            "same_prompt_only_path_blocked": prompt_only_blocked,
            "promptnode_not_dataset_patch": True,
            "overclaiming_blocked": not bool(r343_permissions.get("answer_bearing_generator_improvement_claim_allowed")),
        },
        "claim_permissions": {
            "tool_backed_promptnode_design_allowed": True,
            "symbolic_promptedge_design_allowed": True,
            "more_api_same_prompt_design_allowed": False,
            "answer_bearing_generator_improvement_claim_allowed": False,
            "broad_general_promptnode_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "course_correction": [
            "Replace prompt-only answer-bearing verifier expansion with tool-backed or symbolic PromptNodes.",
            "Keep virtual nodes general: verifier families must be selected by task features, not task IDs or known labels.",
            "Treat PromptEdge as executable contracts: required evidence, option-by-option check, and reject-if-unverified.",
            "Run a no-API design/preflight before spending more API on prospective transfer.",
        ],
        "evidence_snapshot": {
            "r339_root_causes": r339.get("root_causes", []),
            "r342_candidate_repairs": r342.get("candidate_repairs_baseline_count", 0),
            "r343_root_causes": r343.get("root_causes", []),
            "r343_failed_tasks": [row.get("task_id") for row in r343.get("task_rows", [])],
        },
        "next_required_run": "R345_tool_backed_promptnode_verifier_design",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R344 Goal Audit After Candidate Generator Probe",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Alignment",
        "",
    ]
    rows.extend(f"- `{key}`: `{value}`" for key, value in summary["goal_alignment"].items())
    rows.extend(["", "## Claim Permissions", ""])
    rows.extend(f"- `{key}`: `{value}`" for key, value in summary["claim_permissions"].items())
    rows.extend(["", "## Course Correction", ""])
    rows.extend(f"- {item}" for item in summary["course_correction"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r339_summary: str = DEFAULT_R339_SUMMARY,
    r340_summary: str = DEFAULT_R340_SUMMARY,
    r341_summary: str = DEFAULT_R341_SUMMARY,
    r342_summary: str = DEFAULT_R342_SUMMARY,
    r343_summary: str = DEFAULT_R343_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_goal_audit_summary(
        r339_summary=r339_summary,
        r340_summary=r340_summary,
        r341_summary=r341_summary,
        r342_summary=r342_summary,
        r343_summary=r343_summary,
    )
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R344 goal audit after candidate generator probe.")
    parser.add_argument("--r339_summary", default=DEFAULT_R339_SUMMARY)
    parser.add_argument("--r340_summary", default=DEFAULT_R340_SUMMARY)
    parser.add_argument("--r341_summary", default=DEFAULT_R341_SUMMARY)
    parser.add_argument("--r342_summary", default=DEFAULT_R342_SUMMARY)
    parser.add_argument("--r343_summary", default=DEFAULT_R343_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
