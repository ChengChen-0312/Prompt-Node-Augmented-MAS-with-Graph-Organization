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


DEFAULT_R347_SUMMARY = "experiment/mmlu/res_logs/mmlu_r347_tool_backed_promptnode_prospective_replay24_summary.json"
DEFAULT_R348_SUMMARY = "experiment/mmlu/res_logs/mmlu_r348_fresh_tool_promptnode_eval_design_summary.json"
DEFAULT_R349_SUMMARY = "experiment/mmlu/res_logs/mmlu_r349_fresh_tool_promptnode_eval_preflight_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r350_goal_audit_after_tool_promptnode_fresh_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r350_goal_audit_after_tool_promptnode_fresh_preflight_report.md"


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
    r347_summary: str = DEFAULT_R347_SUMMARY,
    r348_summary: str = DEFAULT_R348_SUMMARY,
    r349_summary: str = DEFAULT_R349_SUMMARY,
) -> Dict[str, Any]:
    r347 = _load_json(r347_summary)
    r348 = _load_json(r348_summary)
    r349 = _load_json(r349_summary)
    coverage = int(r349.get("local_tool_forwarded_candidate_count", 0))
    fresh_ready = r349.get("tasks") == 48 and r349.get("leakage_pass") is True and r349.get("overlap_with_excluded_task_count") == 0
    return {
        "run_id": "R350",
        "title": "Goal audit after fresh tool PromptNode preflight",
        "claim_boundary": (
            "R350 is the five-iteration audit after R345-R349. R347 replay is positive, but R349 shows zero fresh "
            "tool coverage, so API execution is paused until the PromptNode library covers fresh tasks."
        ),
        "no_api": True,
        "broad_api": False,
        "iterations_since_last_goal_check": ["R345", "R346", "R347", "R348", "R349"],
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "arg_baseline_preserved": True,
            "r347_replay_positive": int(r347.get("tool_promptnode_delta_correct", 0)) > 0 and int(r347.get("harms", 0)) == 0,
            "r348_policy_frozen": r348.get("policy_frozen_after_run") == "R347",
            "r349_fresh_split_ready": fresh_ready,
            "fresh_tool_coverage_gap_detected": coverage == 0,
            "overclaiming_blocked": True,
        },
        "claim_permissions": {
            "r347_replay_mechanism_evidence_allowed": bool(
                (r347.get("claim_permissions") or {}).get("replay_mechanism_evidence_allowed")
            ),
            "fresh_api_execution_allowed_now": False,
            "fresh_coverage_expansion_allowed": True,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "course_correction": [
            "Do not run fresh API while the frozen tool policy forwards zero candidates.",
            "Expand PromptNode coverage with general nonmath and broader STEM nodes before API execution.",
            "Keep R347 as positive mechanism replay, not a submission-level main result.",
            "Require a fresh preflight with nonzero coverage and no leakage before spending API.",
        ],
        "evidence_snapshot": {
            "r347_arg_vs_tool": f"{r347.get('arg_correct', 0)}/{r347.get('records', 0)} -> {r347.get('tool_promptnode_correct', 0)}/{r347.get('records', 0)}",
            "r349_tasks": r349.get("tasks", 0),
            "r349_local_tool_forwarded_candidate_count": coverage,
            "r349_api_calls_planned": r349.get("api_calls_planned", 0),
        },
        "next_required_run": "R351_fresh_coverage_promptnode_expansion_design",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R350 Goal Audit After Fresh Tool PromptNode Preflight",
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
    r347_summary: str = DEFAULT_R347_SUMMARY,
    r348_summary: str = DEFAULT_R348_SUMMARY,
    r349_summary: str = DEFAULT_R349_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_goal_audit_summary(r347_summary=r347_summary, r348_summary=r348_summary, r349_summary=r349_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R350 goal audit after fresh tool PromptNode preflight.")
    parser.add_argument("--r347_summary", default=DEFAULT_R347_SUMMARY)
    parser.add_argument("--r348_summary", default=DEFAULT_R348_SUMMARY)
    parser.add_argument("--r349_summary", default=DEFAULT_R349_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
