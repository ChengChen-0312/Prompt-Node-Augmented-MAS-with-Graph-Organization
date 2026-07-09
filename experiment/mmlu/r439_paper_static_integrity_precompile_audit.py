from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r439_paper_static_integrity_precompile_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r439_paper_static_integrity_precompile_audit_report.md"

FORBIDDEN_PHRASES = [
    "broad nonmath improvement",
    "universal multiple-choice improvement",
    "submission-ready",
    "exact MMLU STEM cost",
    "external audit passed",
]


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _main_inputs() -> List[str]:
    main = _repo_path("paper/main.tex").read_text(encoding="utf-8")
    inputs = []
    for match in re.finditer(r"\\input\{([^}]+)\}", main):
        target = match.group(1)
        if target == "math_commands":
            continue
        path = f"paper/{target}.tex"
        inputs.append(path)
    return inputs


def _tex_files() -> List[Path]:
    paths = [_repo_path("paper/main.tex"), *_repo_path("paper/sections").glob("*.tex")]
    return sorted(path for path in paths if path.exists())


def _scan_patterns(patterns: List[str]) -> List[Dict[str, Any]]:
    hits: List[Dict[str, Any]] = []
    for path in _tex_files():
        rel = str(path.relative_to(REPO_ROOT))
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for pattern in patterns:
                if pattern in line:
                    hits.append({"file": rel, "line": line_no, "pattern": pattern})
    return hits


def _stale_sections(referenced_sections: List[str]) -> List[str]:
    existing = {str(path.relative_to(REPO_ROOT)) for path in _repo_path("paper/sections").glob("*.tex")}
    return sorted(existing - set(referenced_sections))


def _latex_status() -> Dict[str, Any]:
    latexmk = shutil.which("latexmk")
    pdflatex = shutil.which("pdflatex")
    return {
        "latexmk": latexmk,
        "pdflatex": pdflatex,
        "compile_status": "not_run_no_latex_engine" if not (latexmk or pdflatex) else "not_run_static_audit_only",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R439 Paper Static Integrity Precompile Audit",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- All referenced sections exist: `{summary['all_referenced_sections_exist']}`",
        f"- Compile status: `{summary['compile_status']}`",
        "",
        "## Submission Blockers",
        "",
    ]
    rows.extend(f"- `{item}`" for item in summary["submission_blockers"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run_precompile_audit(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    referenced = _main_inputs()
    missing_sections = [path for path in referenced if not _repo_path(path).exists()]
    forbidden = _scan_patterns(FORBIDDEN_PHRASES)
    todos = _scan_patterns(["TODO", "FIXME", "XXX", "[VERIFY]"])
    latex = _latex_status()
    blockers = [
        "external_experiment_integrity_audit_pending",
        "external_citation_audit_pending",
        "paper_claim_audit_pending",
    ]
    if latex["compile_status"] == "not_run_no_latex_engine":
        blockers.append("latex_engine_missing_for_pdf_compile")
    summary: Dict[str, Any] = {
        "run_id": "R439",
        "title": "Paper static integrity precompile audit",
        "claim_boundary": (
            "R439 checks manuscript structure before compilation. It does not replace PDF compilation, "
            "external experiment audit, citation audit, or paper-claim audit."
        ),
        "no_api": True,
        "broad_api": False,
        "referenced_sections": referenced,
        "missing_sections": missing_sections,
        "all_referenced_sections_exist": not missing_sections,
        "stale_section_files": _stale_sections(referenced),
        "remaining_forbidden_hits": forbidden,
        "todo_hits": todos,
        "references_bib_exists": _repo_path("paper/references.bib").exists(),
        **latex,
        "submission_blockers": blockers,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R440_paper_claim_number_static_audit",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run static paper integrity checks before compilation.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_precompile_audit(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
