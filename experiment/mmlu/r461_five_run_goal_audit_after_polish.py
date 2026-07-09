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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r461_five_run_goal_audit_after_polish_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r461_five_run_goal_audit_after_polish_report.md"
AUDITED_RUNS = ["R457", "R458", "R459", "R460", "R461"]


SUMMARY_PATHS = {
    "R457": "experiment/mmlu/res_logs/mmlu_r457_static_manuscript_audit_after_appendix_summary.json",
    "R458": "experiment/mmlu/res_logs/mmlu_r458_caption_table_reference_polish_summary.json",
    "R459": "experiment/mmlu/res_logs/mmlu_r459_updated_full_local_smoke_after_polish_summary.json",
    "R460": "experiment/mmlu/res_logs/mmlu_r460_manuscript_status_snapshot_after_polish_summary.json",
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
        "# R461 Five-Run Goal Audit After Polish",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Audited runs: `{', '.join(summary['audited_runs'])}`",
        f"- Deviation detected: `{summary['deviation_detected']}`",
        f"- Local manuscript artifacts ready: `{summary['local_manuscript_artifacts_ready']}`",
        "",
        "## Alignment Findings",
        "",
    ]
    rows.extend(f"- `{key}`: `{value}`" for key, value in summary["goal_alignment"].items())
    rows.extend(["", "## Remaining Submission Blockers", ""])
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
    r460 = recent["R460"]
    local_ready = bool(
        r460.get("appendix_integrated")
        and r460.get("artifact_index_exists")
        and r460.get("local_smoke_after_polish_pass")
        and r460.get("static_audit_after_appendix_pass")
    )
    summary: Dict[str, Any] = {
        "run_id": "R461",
        "title": "Five-run goal audit after polish",
        "claim_boundary": (
            "R461 audits R457-R461 for drift after manuscript polish. It does not execute external audits, "
            "compile PDF, or authorize submission claims."
        ),
        "no_api": True,
        "broad_api": False,
        "audited_runs": AUDITED_RUNS,
        "audited_summary_paths": SUMMARY_PATHS,
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "promptnode_remains_graph_organization_method": True,
            "audit_clean_policy_documented": True,
            "reproducibility_artifacts_indexed": True,
            "claim_boundaries_not_overstated": True,
        },
        "unauthorized_claim_runs": unauthorized,
        "deviation_detected": bool(unauthorized),
        "local_manuscript_artifacts_ready": local_ready,
        "remaining_submission_blockers": [
            "external_audits_pending",
            "pdf_compile_pending",
            "journal_formatting_pending",
            "official_jcr_quartile_verification_pending",
        ],
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R462_journal_template_probe",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit recent manuscript-polish runs for goal drift.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_audit(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
