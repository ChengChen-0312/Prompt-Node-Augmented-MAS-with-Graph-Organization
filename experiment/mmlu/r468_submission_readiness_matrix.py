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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r468_submission_readiness_matrix_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r468_submission_readiness_matrix_report.md"
DEFAULT_MATRIX_MD = "paper/artifacts/submission_readiness_matrix.md"


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


def render_matrix(summary: Dict[str, Any]) -> str:
    rows = [
        "# Submission Readiness Matrix",
        "",
        "| Item | Status | Evidence | Required Next Action |",
        "|---|---|---|---|",
    ]
    for item, payload in summary["readiness_matrix"].items():
        rows.append(
            f"| `{item}` | `{payload['status']}` | {payload['evidence']} | {payload['next_action']} |"
        )
    rows.extend(
        [
            "",
            f"- Paper claim authorized: `{summary['paper_claim_authorized']}`",
            f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
            "",
        ]
    )
    return "\n".join(rows)


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R468 Submission Readiness Matrix",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Matrix: `{summary['matrix_md']}`",
        f"- Ready local items: `{summary['ready_local_count']}`",
        f"- Blocked items: `{summary['blocked_count']}`",
        "",
        f"- Paper claim authorized: `{summary['paper_claim_authorized']}`",
        f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
        f"- Next required run: `{summary['next_required_run']}`",
        "",
    ]
    return "\n".join(rows)


def run_matrix(
    matrix_md: str = DEFAULT_MATRIX_MD,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    r460 = _load_json("experiment/mmlu/res_logs/mmlu_r460_manuscript_status_snapshot_after_polish_summary.json")
    r464 = _load_json("experiment/mmlu/res_logs/mmlu_r464_external_audit_authorization_checklist_summary.json")
    r467 = _load_json("experiment/mmlu/res_logs/mmlu_r467_jcr_quartile_verification_plan_summary.json")
    readiness_matrix = {
        "local_manuscript_artifacts": {
            "status": "ready_local" if r460.get("appendix_integrated") and r460.get("artifact_index_exists") else "blocked",
            "evidence": "R460 confirms appendix, artifact index, and local smoke after polish.",
            "next_action": "Keep synchronized while audits and template conversion proceed.",
        },
        "source_package_manifest": {
            "status": "ready_local",
            "evidence": "R463 lists paper source files and exclusion patterns.",
            "next_action": "Use for future JAIR/KAIS template conversion or manual review import.",
        },
        "external_audits": {
            "status": "blocked",
            "evidence": "R464 lists three payloads but transmission_performed=false.",
            "next_action": "Obtain explicit user authorization, then run/import experiment, claim, and citation reviews.",
        },
        "pdf_compile": {
            "status": "blocked",
            "evidence": "R452 found no latexmk or pdflatex.",
            "next_action": "Install or locate a TeX engine, then compile and visually inspect the PDF.",
        },
        "official_jcr_verification": {
            "status": "blocked",
            "evidence": "R467 records public planning sources only; official_jcr_verification_completed=false.",
            "next_action": "Verify JAIR/KAIS in official JCR or institutional Web of Science.",
        },
        "journal_template_conversion": {
            "status": "blocked",
            "evidence": "R462 records JAIR/KAIS templates but template_conversion_performed=false.",
            "next_action": "Convert after external audits settle claim scope.",
        },
    }
    ready_local_count = sum(1 for item in readiness_matrix.values() if item["status"] == "ready_local")
    blocked_count = sum(1 for item in readiness_matrix.values() if item["status"] == "blocked")
    summary: Dict[str, Any] = {
        "run_id": "R468",
        "title": "Submission readiness matrix",
        "claim_boundary": (
            "R468 separates locally ready manuscript artifacts from submission blockers. "
            "It does not execute blocked steps or authorize claims."
        ),
        "no_api": True,
        "broad_api": False,
        "matrix_md": matrix_md,
        "readiness_matrix": readiness_matrix,
        "ready_local_count": ready_local_count,
        "blocked_count": blocked_count,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R469_local_smoke_after_jcr_readiness",
    }
    _write_text(matrix_md, render_matrix(summary))
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build submission readiness matrix.")
    parser.add_argument("--matrix_md", default=DEFAULT_MATRIX_MD)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_matrix(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
