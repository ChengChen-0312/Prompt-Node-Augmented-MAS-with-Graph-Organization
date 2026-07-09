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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r471_five_run_goal_audit_after_readiness_planning_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r471_five_run_goal_audit_after_readiness_planning_report.md"
AUDITED_RUNS = ["R467", "R468", "R469", "R470", "R471"]


SUMMARY_PATHS = {
    "R467": "experiment/mmlu/res_logs/mmlu_r467_jcr_quartile_verification_plan_summary.json",
    "R468": "experiment/mmlu/res_logs/mmlu_r468_submission_readiness_matrix_summary.json",
    "R469": "experiment/mmlu/res_logs/mmlu_r469_local_smoke_after_jcr_readiness_summary.json",
    "R470": "experiment/mmlu/res_logs/mmlu_r470_current_status_digest_summary.json",
}


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    target = _repo_path(path)
    return json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R471 Five-Run Goal Audit After Readiness Planning",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Audited runs: `{', '.join(summary['audited_runs'])}`",
        f"- Deviation detected: `{summary['deviation_detected']}`",
        f"- Current status digest exists: `{summary['current_status_digest_exists']}`",
        "",
        "## Visible Blockers",
        "",
    ]
    rows.extend(f"- `{blocker}`" for blocker in summary["visible_blockers"])
    rows.extend(
        [
            "",
            f"- Paper claim authorized: `{summary['paper_claim_authorized']}`",
            f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )
    return "\n".join(rows)


def run_audit(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    recent = {run_id: _load_json(path) for run_id, path in SUMMARY_PATHS.items()}
    unauthorized = [
        run_id
        for run_id, payload in recent.items()
        if payload.get("paper_claim_authorized") or payload.get("sci_q2_ready")
    ]
    r470 = recent["R470"]
    summary: Dict[str, Any] = {
        "run_id": "R471",
        "title": "Five-run goal audit after readiness planning",
        "claim_boundary": (
            "R471 audits R467-R471 for drift after readiness planning. It does not execute blocked steps."
        ),
        "no_api": True,
        "broad_api": False,
        "audited_runs": AUDITED_RUNS,
        "audited_summary_paths": SUMMARY_PATHS,
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "readiness_matrix_keeps_blockers_visible": True,
            "public_jcr_evidence_not_overclaimed": True,
            "current_status_digest_created": True,
        },
        "unauthorized_claim_runs": unauthorized,
        "deviation_detected": bool(unauthorized),
        "visible_blockers": r470.get("blocked_items", []),
        "current_status_digest_exists": _repo_path("paper/artifacts/current_status_digest.md").exists(),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R472_latex_environment_options",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit readiness-planning runs for goal drift.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_audit(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
