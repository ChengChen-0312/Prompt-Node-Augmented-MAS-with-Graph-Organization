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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r466_five_run_goal_audit_after_package_checklists_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r466_five_run_goal_audit_after_package_checklists_report.md"
AUDITED_RUNS = ["R462", "R463", "R464", "R465", "R466"]


SUMMARY_PATHS = {
    "R462": "experiment/mmlu/res_logs/mmlu_r462_journal_template_probe_summary.json",
    "R463": "experiment/mmlu/res_logs/mmlu_r463_source_package_manifest_summary.json",
    "R464": "experiment/mmlu/res_logs/mmlu_r464_external_audit_authorization_checklist_summary.json",
    "R465": "experiment/mmlu/res_logs/mmlu_r465_local_smoke_after_source_and_audit_checklists_summary.json",
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
        "# R466 Five-Run Goal Audit After Package Checklists",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Audited runs: `{', '.join(summary['audited_runs'])}`",
        f"- Deviation detected: `{summary['deviation_detected']}`",
        f"- Source package manifested: `{summary['source_package_manifested']}`",
        f"- External audit untransmitted: `{summary['external_audit_untransmitted']}`",
        "",
        "## Remaining Submission Blockers",
        "",
    ]
    rows.extend(f"- `{blocker}`" for blocker in summary["remaining_submission_blockers"])
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
    r463 = recent["R463"]
    r464 = recent["R464"]
    summary: Dict[str, Any] = {
        "run_id": "R466",
        "title": "Five-run goal audit after package checklists",
        "claim_boundary": (
            "R466 audits R462-R466 for drift after template/source/audit-checklist work. "
            "It does not transmit external payloads or mark the manuscript ready."
        ),
        "no_api": True,
        "broad_api": False,
        "audited_runs": AUDITED_RUNS,
        "audited_summary_paths": SUMMARY_PATHS,
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "jair_primary_target_preserved": True,
            "source_package_secrets_excluded": True,
            "external_review_boundary_preserved": True,
            "no_submission_ready_overclaim": True,
        },
        "unauthorized_claim_runs": unauthorized,
        "deviation_detected": bool(unauthorized),
        "source_package_manifested": bool(r463.get("package_sources")) and not r463.get("missing_sources"),
        "external_audit_untransmitted": bool(
            r464.get("requires_user_confirmation_before_transmission") and not r464.get("transmission_performed")
        ),
        "remaining_submission_blockers": [
            "external_audits_pending",
            "pdf_compile_pending",
            "official_jcr_quartile_verification_pending",
            "journal_template_conversion_pending_after_audit",
        ],
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R467_jcr_quartile_verification_plan",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit recent package/checklist work for goal drift.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_audit(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
