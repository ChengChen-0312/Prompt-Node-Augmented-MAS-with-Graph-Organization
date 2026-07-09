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


DEFAULT_R352_SUMMARY = "experiment/mmlu/res_logs/mmlu_r352_fresh_coverage_promptnode_expansion_preflight_summary.json"
DEFAULT_R354_SUMMARY = "experiment/mmlu/res_logs/mmlu_r354_fresh_eval_after_coverage_expansion_preflight_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r355_goal_audit_after_second_fresh_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r355_goal_audit_after_second_fresh_preflight_report.md"


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
    r352_summary: str = DEFAULT_R352_SUMMARY,
    r354_summary: str = DEFAULT_R354_SUMMARY,
) -> Dict[str, Any]:
    r352 = _load_json(r352_summary)
    r354 = _load_json(r354_summary)
    r352_forward = int(r352.get("forwarded_candidate_count", 0))
    r354_forward = int(r354.get("local_tool_forwarded_candidate_count", 0))
    template_failed = r352_forward > 0 and r354_forward == 0
    return {
        "run_id": "R355",
        "title": "Goal audit after second fresh preflight",
        "claim_boundary": (
            "R355 is an early goal audit after R354 showed a second fresh split with zero local-template coverage. "
            "It redirects the work toward a learned graph policy instead of more hand-written templates."
        ),
        "no_api": True,
        "broad_api": False,
        "early_goal_audit_reason": "second_fresh_zero_coverage",
        "iterations_since_last_goal_check": ["R351", "R352", "R353", "R354"],
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "r352_dev_coverage_positive": r352_forward > 0 and int(r352.get("candidate_error_count", 0)) == 0,
            "r354_fresh_coverage_zero": r354_forward == 0,
            "local_template_path_failed_as_general_strategy": template_failed,
            "overclaiming_blocked": True,
        },
        "claim_permissions": {
            "hand_template_expansion_allowed_as_primary_path": False,
            "learned_graph_policy_design_required": True,
            "api_execution_allowed_now": False,
            "r352_dev_coverage_claim_allowed": True,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "course_correction": [
            "Stop hand-expanding deterministic templates as the primary path.",
            "Train or fit a graph-policy selector that predicts when to instantiate PromptNodes/PromptEdges from task features and candidate evidence.",
            "Use LLM verifier nodes only behind learned safety gates and evidence contracts.",
            "Treat local tools as one PromptNode family, not the whole method.",
        ],
        "evidence_snapshot": {
            "r352_dev_forwarded": r352_forward,
            "r352_dev_candidate_errors": r352.get("candidate_error_count", 0),
            "r354_fresh_forwarded": r354_forward,
            "r354_tasks": r354.get("tasks", 0),
        },
        "next_required_run": "R356_learned_graph_policy_promptnode_design",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R355 Goal Audit After Second Fresh Preflight",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Alignment",
        "",
    ]
    rows.extend(f"- `{key}`: `{value}`" for key, value in summary["goal_alignment"].items())
    rows.extend(["", "## Course Correction", ""])
    rows.extend(f"- {item}" for item in summary["course_correction"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r352_summary: str = DEFAULT_R352_SUMMARY,
    r354_summary: str = DEFAULT_R354_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_goal_audit_summary(r352_summary=r352_summary, r354_summary=r354_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R355 goal audit after second fresh preflight.")
    parser.add_argument("--r352_summary", default=DEFAULT_R352_SUMMARY)
    parser.add_argument("--r354_summary", default=DEFAULT_R354_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
