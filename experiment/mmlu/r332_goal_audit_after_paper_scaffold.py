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


DEFAULT_R328_SUMMARY = "experiment/mmlu/res_logs/mmlu_r328_selector_policy_claim_update_summary.json"
DEFAULT_R329_SUMMARY = "experiment/mmlu/res_logs/mmlu_r329_case_study_extraction_summary.json"
DEFAULT_R330_SUMMARY = "experiment/mmlu/res_logs/mmlu_r330_paper_tables_and_figures_plan_summary.json"
DEFAULT_R331_SUMMARY = "experiment/mmlu/res_logs/mmlu_r331_paper_outline_scaffold_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r332_goal_audit_after_paper_scaffold_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r332_goal_audit_after_paper_scaffold_report.md"


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
    r328_summary: str = DEFAULT_R328_SUMMARY,
    r329_summary: str = DEFAULT_R329_SUMMARY,
    r330_summary: str = DEFAULT_R330_SUMMARY,
    r331_summary: str = DEFAULT_R331_SUMMARY,
) -> Dict[str, Any]:
    r328 = _load_json(r328_summary)
    r329 = _load_json(r329_summary)
    r330 = _load_json(r330_summary)
    r331 = _load_json(r331_summary)
    selector_permissions = r328.get("selector_claim_permissions", {})
    return {
        "run_id": "R332",
        "title": "Goal audit after paper scaffold",
        "claim_boundary": (
            "R332 is the five-iteration audit after R327-R331. The writing scaffold is useful, but the SCI-Q2 path "
            "still depends on prospective selector evaluation or another held-out transfer result."
        ),
        "no_api": True,
        "broad_api": False,
        "iterations_since_last_goal_check": ["R327", "R328", "R329", "R330", "R331"],
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "paper_scaffold_created": bool(r331.get("claims_evidence_matrix")),
            "selector_claim_not_overstated": not bool(selector_permissions.get("external_accuracy_improvement_claim_allowed")),
            "case_studies_ready": bool(r329.get("includes_required_mechanisms")),
            "tables_and_figures_planned": bool(r330.get("tables")) and bool(r330.get("figures")),
            "prospective_eval_still_missing": True,
        },
        "claim_permissions": {
            "offline_selector_feasibility_claim_allowed": bool(
                selector_permissions.get("offline_selector_feasibility_claim_allowed")
            ),
            "promptedge_safety_feature_claim_allowed": bool(
                selector_permissions.get("promptedge_safety_feature_claim_allowed")
            ),
            "external_accuracy_improvement_claim_allowed": False,
            "broad_general_promptnode_claim_allowed": False,
            "full_paper_drafting_allowed": False,
            "sci_q2_ready": False,
        },
        "course_correction": [
            "Prioritize prospective selector evaluation before drafting full paper prose.",
            "Keep PAPER_PLAN.md as a scaffold, not a submission draft.",
            "Run only leakage-safe, bounded-cost prospective evaluation using the R327 selector policy.",
            "If prospective eval fails, narrow the paper to AQuA+MMLU STEM evidence and selector feasibility.",
        ],
        "next_required_run": "R333_prospective_selector_eval_design",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R332 Goal Audit After Paper Scaffold",
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
    r328_summary: str = DEFAULT_R328_SUMMARY,
    r329_summary: str = DEFAULT_R329_SUMMARY,
    r330_summary: str = DEFAULT_R330_SUMMARY,
    r331_summary: str = DEFAULT_R331_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_goal_audit_summary(
        r328_summary=r328_summary,
        r329_summary=r329_summary,
        r330_summary=r330_summary,
        r331_summary=r331_summary,
    )
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R332 goal audit after paper scaffold.")
    parser.add_argument("--r328_summary", default=DEFAULT_R328_SUMMARY)
    parser.add_argument("--r329_summary", default=DEFAULT_R329_SUMMARY)
    parser.add_argument("--r330_summary", default=DEFAULT_R330_SUMMARY)
    parser.add_argument("--r331_summary", default=DEFAULT_R331_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
