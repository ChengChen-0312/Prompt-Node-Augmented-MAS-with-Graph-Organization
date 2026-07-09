from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r443_manuscript_status_snapshot_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r443_manuscript_status_snapshot_report.md"


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


def _paper_files() -> List[str]:
    files = ["paper/main.tex", "paper/math_commands.tex", "paper/references.bib"]
    files.extend(str(path.relative_to(REPO_ROOT)) for path in sorted(_repo_path("paper/sections").glob("*.tex")))
    return files


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R443 Manuscript Status Snapshot",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Complete initial paper draft: `{summary['complete_initial_paper_draft']}`",
        f"- Local smoke pass: `{summary['local_smoke_pass']}`",
        f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
        "",
        "## Remaining Blockers",
        "",
    ]
    rows.extend(f"- `{item}`" for item in summary["remaining_blockers"])
    rows.extend(["", "## Paper Files", ""])
    rows.extend(f"- `{path}`" for path in summary["paper_files"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run_snapshot(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    r437 = _load_json("experiment/mmlu/res_logs/mmlu_r437_related_work_initial_draft_summary.json")
    r439 = _load_json("experiment/mmlu/res_logs/mmlu_r439_paper_static_integrity_precompile_audit_summary.json")
    r440 = _load_json("experiment/mmlu/res_logs/mmlu_r440_paper_claim_number_static_audit_summary.json")
    r441 = _load_json("experiment/mmlu/res_logs/mmlu_r441_external_audit_package_refresh_summary.json")
    r442 = _load_json("experiment/mmlu/res_logs/mmlu_r442_local_smoke_test_suite_summary.json")

    blockers = [
        "external_experiment_integrity_audit_pending",
        "external_citation_audit_pending",
        "external_paper_claim_audit_pending",
    ]
    if r439.get("compile_status") == "not_run_no_latex_engine":
        blockers.append("latex_engine_missing_for_pdf_compile")

    summary: Dict[str, Any] = {
        "run_id": "R443",
        "title": "Manuscript status snapshot",
        "claim_boundary": (
            "R443 summarizes the current initial paper draft and remaining blockers. "
            "It does not execute external audits or mark the manuscript ready for submission."
        ),
        "no_api": True,
        "broad_api": False,
        "paper_files": _paper_files(),
        "complete_initial_paper_draft": bool(r437.get("complete_initial_paper_draft")),
        "local_smoke_pass": bool(r442.get("local_smoke_pass")),
        "static_structure_pass": bool(r439.get("all_referenced_sections_exist") and not r439.get("stale_section_files")),
        "static_number_audit_pass": bool(r440.get("static_number_audit_pass")),
        "external_audit_packages": r441.get("audit_packages", {}),
        "remaining_blockers": blockers,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R444_external_audit_execution_plan",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize current manuscript status and remaining blockers.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_snapshot(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
